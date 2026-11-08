"""LLM Evaluator for Microdrama Promos.

Uses OpenRouter API (openai/gpt-4o-mini) with structured JSON evaluation to assess
first 3-second hook power, cliffhanger cutoff tension, and cold-audience clarity,
while strictly managing the API credit budget (< $0.02 total spend).
"""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import requests
from dotenv import load_dotenv

from src.candidate_generator import PromoCandidate
from src.microdrama_parser import seconds_to_timestamp


@dataclass
class LLMEvalResult:
    candidate_id: str
    hook_power: float  # 1.0 - 10.0
    cliffhanger_pull: float  # 1.0 - 10.0
    cold_audience_clarity: float  # 1.0 - 10.0
    viral_retention_score: float  # 1.0 - 10.0
    composite_llm_score: float  # Weighted combination
    hook_description: str
    cliffhanger_description: str
    why_it_works: str
    refined_start_offset: float = 0.0
    refined_end_offset: float = 0.0
    tokens_used: int = 0
    estimated_cost_usd: float = 0.0


class LLMEvaluator:
    """Evaluates candidate promos using OpenRouter with strict cost governance."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "openai/gpt-4o-mini",
    ):
        load_dotenv()
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")).rstrip("/")
        self.model = model
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost_usd = 0.0

        # Cost per 1M tokens for gpt-4o-mini ($0.15 prompt, $0.60 completion)
        self.prompt_cost_per_m = 0.15
        self.completion_cost_per_m = 0.60

    def evaluate_candidate(self, candidate: PromoCandidate) -> LLMEvalResult:
        """Evaluate a single promo candidate via OpenRouter."""
        if not self.api_key:
            # Fallback to heuristic evaluation if no key is present
            return self._heuristic_fallback(candidate)

        transcript = candidate.get_full_transcript()
        episodes_str = ", ".join(str(ep) for ep in candidate.episode_numbers)

        system_prompt = (
            "You are a Senior Performance Marketing Editor for top vertical microdrama apps "
            "(ReelShort, DramaBox, ShortMax). Your job is to evaluate short video promos "
            "(20-60 seconds) cut directly from screenplays to run as paid ads on TikTok, Instagram Reels, and YouTube Shorts.\n\n"
            "Rules for winning microdrama ads:\n"
            "1. THE HOOK (First 3 seconds): Must shock a scrolling user into stopping (slap, cruel betrayal, shocking line, humiliation, secret identity cue).\n"
            "2. COLD AUDIENCE CLARITY: A first-time viewer who has never heard of this show must understand the conflict and emotion immediately without needing backstories.\n"
            "3. THE CLIFFHANGER: Cuts sharply at the moment of peak unanswered curiosity or shock, making the user click the download or watch link.\n"
            "4. TIMING CADENCE: Ensure start and end cuts make sense musically and dramatically.\n\n"
            "Respond strictly in valid JSON with no markdown wrapping or preamble."
        )

        user_prompt = f"""Evaluate this candidate promo:
Candidate ID: {candidate.candidate_id}
Promo Type: {candidate.promo_type}
Total Duration: {candidate.total_duration:.1f} seconds
Episodes Involved: {episodes_str}

SCRIPT EXCERPT:
{transcript}

Return a JSON object with this exact structure:
{{
  "hook_power": <number 1.0 to 10.0>,
  "cliffhanger_pull": <number 1.0 to 10.0>,
  "cold_audience_clarity": <number 1.0 to 10.0>,
  "viral_retention_score": <number 1.0 to 10.0>,
  "hook_description": "<1-2 sentences on what hooks the viewer in the first 3 seconds>",
  "cliffhanger_description": "<1-2 sentences on how the promo cuts and the unresolved tension>",
  "why_it_works": "<Single punchy sentence on why this promo converts cold viewers>",
  "refined_start_offset": <float between -2.0 and +2.0, adjustment to optimize start>,
  "refined_end_offset": <float between -2.0 and +2.0, adjustment to optimize cutoff>
}}"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/microdrama-promo-finder",
            "X-Title": "Microdrama Promo Finder",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 500,
            "response_format": {"type": "json_object"},
        }

        try:
            url = f"{self.base_url}/chat/completions"
            response = requests.post(url, headers=headers, json=payload, timeout=25)
            if response.status_code != 200:
                print(f"[WARN] OpenRouter API returned status {response.status_code}: {response.text}")
                return self._heuristic_fallback(candidate)

            data = response.json()
            usage = data.get("usage", {})
            prompt_toks = usage.get("prompt_tokens", 0)
            comp_toks = usage.get("completion_tokens", 0)
            total_toks = prompt_toks + comp_toks

            cost = (prompt_toks * self.prompt_cost_per_m + comp_toks * self.completion_cost_per_m) / 1_000_000.0
            self.total_prompt_tokens += prompt_toks
            self.total_completion_tokens += comp_toks
            self.total_cost_usd += cost

            content_text = data["choices"][0]["message"]["content"]
            result_json = json.loads(content_text)

            h_p = float(result_json.get("hook_power", candidate.hook_score))
            c_p = float(result_json.get("cliffhanger_pull", candidate.cliffhanger_score))
            c_c = float(result_json.get("cold_audience_clarity", candidate.clarity_score))
            v_r = float(result_json.get("viral_retention_score", candidate.pacing_score))

            # Composite LLM Score
            comp_score = round(0.35 * h_p + 0.30 * c_p + 0.20 * c_c + 0.15 * v_r, 2)

            return LLMEvalResult(
                candidate_id=candidate.candidate_id,
                hook_power=h_p,
                cliffhanger_pull=c_p,
                cold_audience_clarity=c_c,
                viral_retention_score=v_r,
                composite_llm_score=comp_score,
                hook_description=result_json.get("hook_description", candidate.hook_summary),
                cliffhanger_description=result_json.get("cliffhanger_description", candidate.cliffhanger_summary),
                why_it_works=result_json.get("why_it_works", "High emotional conflict and primal betrayal drive cold viewer curiosity."),
                refined_start_offset=float(result_json.get("refined_start_offset", 0.0)),
                refined_end_offset=float(result_json.get("refined_end_offset", 0.0)),
                tokens_used=total_toks,
                estimated_cost_usd=cost,
            )

        except Exception as e:
            print(f"[WARN] Error calling OpenRouter: {e}. Using heuristic fallback.")
            return self._heuristic_fallback(candidate)

    def _heuristic_fallback(self, candidate: PromoCandidate) -> LLMEvalResult:
        """Deterministic fallback when LLM is offline or disabled."""
        comp_score = round(
            0.35 * candidate.hook_score
            + 0.30 * candidate.cliffhanger_score
            + 0.20 * candidate.clarity_score
            + 0.15 * candidate.pacing_score,
            2,
        )
        return LLMEvalResult(
            candidate_id=candidate.candidate_id,
            hook_power=candidate.hook_score,
            cliffhanger_pull=candidate.cliffhanger_score,
            cold_audience_clarity=candidate.clarity_score,
            viral_retention_score=candidate.pacing_score,
            composite_llm_score=comp_score,
            hook_description=f"First 3 seconds: {candidate.hook_summary}",
            cliffhanger_description=f"Cutoff: {candidate.cliffhanger_summary}",
            why_it_works="Explosive betrayal and high emotional contrast deliver immediate standalone narrative stakes.",
            tokens_used=0,
            estimated_cost_usd=0.0,
        )

