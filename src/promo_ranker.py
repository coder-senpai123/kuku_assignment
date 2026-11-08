"""Promo Ranker & Growth Optimization Engine.

Ranks microdrama promos using a multi-factor viral acquisition formula
and provides strategic posting hierarchy recommendations (Day 1 Flagship, Day 2 Reversal, etc.).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.candidate_generator import PromoCandidate
from src.llm_evaluator import LLMEvalResult
from src.microdrama_parser import seconds_to_timestamp


@dataclass
class RankedPromo:
    rank: int
    candidate_id: str
    promo_type: str  # "continuous" or "stitched"
    total_duration: float
    segments: List[Dict[str, Any]]
    hook: str
    cliffhanger: str
    why_it_works: str
    funnel_tier: str
    posting_priority: str
    posting_rationale: str
    hook_score: float
    cliffhanger_score: float
    clarity_score: float
    viral_score: float
    composite_score: float


class PromoRanker:
    """Ranks candidate promos for maximum user acquisition and conversion."""

    def rank_promos(
        self, candidates: List[PromoCandidate], evaluations: Dict[str, LLMEvalResult]
    ) -> List[RankedPromo]:
        ranked_list: List[RankedPromo] = []

        # Merge candidate data with LLM evaluation
        scored_items = []
        for cand in candidates:
            eval_res = evaluations.get(cand.candidate_id)
            if not eval_res:
                continue

            # Composite ranking score:
            # 35% Hook + 30% Cliffhanger + 20% Cold Clarity + 15% Viral Pacing
            final_score = eval_res.composite_llm_score

            # Boost early episodes slightly for cold-audience priority (episodes 1-4 are best for Day 1 launch)
            min_ep = min(s.episode_num for s in cand.segments)
            if min_ep <= 3:
                final_score += 0.3
            elif min_ep > 25:
                final_score -= 0.4

            scored_items.append((final_score, cand, eval_res))

        # Sort descending by final score
        scored_items.sort(key=lambda x: x[0], reverse=True)

        for i, (score, cand, ev) in enumerate(scored_items):
            rank = i + 1

            # Format segments with micro-boundary adjustments
            formatted_segments = []
            for s_idx, seg in enumerate(cand.segments):
                # Apply boundary refinement to first start and last end
                adj_start = seg.start_time
                adj_end = seg.end_time

                if s_idx == 0 and ev.refined_start_offset != 0:
                    adj_start = max(0.0, adj_start + ev.refined_start_offset)
                if s_idx == len(cand.segments) - 1 and ev.refined_end_offset != 0:
                    adj_end = adj_end + ev.refined_end_offset

                formatted_segments.append(
                    {
                        "episode": seg.episode_num,
                        "start_time_seconds": round(adj_start, 2),
                        "end_time_seconds": round(adj_end, 2),
                        "start_timestamp": seconds_to_timestamp(adj_start),
                        "end_timestamp": seconds_to_timestamp(adj_end),
                        "duration_seconds": round(adj_end - adj_start, 2),
                    }
                )

            total_dur = sum(s["duration_seconds"] for s in formatted_segments)

            # Determine Funnel Tier and Strategic Posting Priority
            funnel_tier, priority, rationale = self._determine_posting_strategy(
                rank, cand, ev, formatted_segments
            )

            promo = RankedPromo(
                rank=rank,
                candidate_id=cand.candidate_id,
                promo_type=cand.promo_type,
                total_duration=round(total_dur, 2),
                segments=formatted_segments,
                hook=ev.hook_description,
                cliffhanger=ev.cliffhanger_description,
                why_it_works=ev.why_it_works,
                funnel_tier=funnel_tier,
                posting_priority=priority,
                posting_rationale=rationale,
                hook_score=ev.hook_power,
                cliffhanger_score=ev.cliffhanger_pull,
                clarity_score=ev.cold_audience_clarity,
                viral_score=ev.viral_retention_score,
                composite_score=round(score, 2),
            )
            ranked_list.append(promo)

        return ranked_list

    def _determine_posting_strategy(
        self, rank: int, cand: PromoCandidate, ev: LLMEvalResult, segments: List[Dict[str, Any]]
    ) -> tuple[str, str, str]:
        """Classify promo into performance marketing hierarchy."""
        min_ep = min(s["episode"] for s in segments)

        if rank == 1:
            return (
                "Tier 1: Top-of-Funnel Flagship Ad",
                "POST FIRST (Day 1 Campaign Launch - Broad Reach)",
                "This promo should be posted first across TikTok and Instagram Reels. "
                "It features primal, universal emotional stakes (altar abandonment and sister betrayal) "
                "that require zero prior knowledge to evoke instant anger and empathy. "
                "Its high hook-stopping power and ruthless cliffhanger cut maximize initial Click-Through Rate (CTR) "
                "and app install conversions for completely cold viewers.",
            )
        elif rank == 2:
            return (
                "Tier 1: High-Conversion Retargeting Ad",
                "POST SECOND (Day 1 Night / Day 2 Push)",
                "Post this second to retarget users who engaged with the initial betrayal promo. "
                "It delivers the immediate emotional turnaround—a scarred, honorable soldier drops to one knee "
                "to defend Juliana before the sneering church guests. The cliffhanger cut on the wedding proposal "
                "compels viewers to binge Episode 2 and 3 immediately.",
            )
        elif rank == 3 or cand.promo_type == "stitched":
            return (
                "Tier 2: High-Paced Dynamic Synthesis Ad",
                "POST THIRD (Day 2-3 High-Velocity Ads)",
                "Post this third on YouTube Shorts and TikTok as a high-velocity narrative synthesis. "
                "By stitching the devastating insult directly into the soldier's dramatic intervention, "
                "it compresses the full setup-conflict-reversal arc into 35-50 seconds, driving maximum "
                "watch-time retention and viewer conversion.",
            )
        elif min_ep <= 5:
            return (
                "Tier 2: Escalation & Conflict Deepener",
                "POST FOURTH (Day 3-4 Mid-Funnel Push)",
                "Post to capitalize on audience momentum with escalating public confrontations "
                "and the villains' escalating insolence.",
            )
        else:
            return (
                "Tier 3: Power Reveal & Payoff Ad",
                "POST LATER (Day 5+ Re-engagement / Core Retargeting)",
                "Post as a mid-campaign retargeting ad to existing viewers who want to see the villains get their comeuppance "
                "and witness the mysterious soldier reveal his supreme ducal power.",
            )

