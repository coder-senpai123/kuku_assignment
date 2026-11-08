"""Quality Auditor & Failure Mode Analyzer.

Identifies where the automated promo extraction tool picks badly, analyzing
false hooks, context traps, cadence clipping, and script-to-screen discrepancies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any

from src.candidate_generator import PromoCandidate
from src.llm_evaluator import LLMEvalResult
from src.microdrama_parser import BeatType


@dataclass
class QualityAuditReport:
    total_candidates_audited: int
    flagged_candidates_count: int
    systemic_failure_modes: List[Dict[str, str]]
    candidate_quality_warnings: List[Dict[str, Any]]
    recommendations_for_editors: List[str]


class QualityAuditor:
    """Audits extracted promos to identify false positives, weak hooks, and context traps."""

    SYSTEMIC_FAILURE_MODES = [
        {
            "category": "The 'Stage Direction' Illusion (Passive Action False Positive)",
            "description": "Script descriptions like 'Juliana clenches her knuckles with suppressed fury' or 'Her eyes fill with silent sorrow' read with high dramatic weight on paper. On screen, 4 seconds of silent physical reaction without rapid dialogue or camera movement translates to sluggish video pacing, triggering instant thumb scrolls.",
            "impact": "High bounce rate in first 2 seconds on TikTok / Instagram Reels.",
            "mitigation": "Enforce presence of punchy spoken dialogue or dynamic camera motion (extreme close-up / sudden snap) within the first 1.5 seconds.",
        },
        {
            "category": "The Cold-Audience Lore Trap (Context Asymmetry)",
            "description": "Episodes 30-50 feature intense confrontations, but they hinge on intricate subplots (e.g., poisoned dowries, secondary noble factions, forged wills). The tool detects explosive keywords ('poison', 'traitor', 'proof'), but cold viewers scrolling social feeds have zero emotional investment in secondary characters.",
            "impact": "High initial click-through but catastrophic drop-off before 10 seconds; low app installation conversion.",
            "mitigation": "Apply a steep decay penalty to episodes beyond Episode 20 for top-of-funnel ads, reserving them strictly for mid-campaign retargeting.",
        },
        {
            "category": "Over-Indexing on Scriptwriter 'Cliffhanger' SFX Tags",
            "description": "Nearly every episode ends with a variation of 'Solemn low-pitched string drone swells to an ominous cliffhanger peak. Cut to black.' The tool can be tricked into picking a dull 30-second lead-up simply because the terminal SFX cue contains the literal word 'cliffhanger'.",
            "impact": "Promos that start weakly but end with a loud boom and cut to black, boring viewers long before the cliffhanger arrives.",
            "mitigation": "Couple cliffhanger scoring with dialogue tension and unresolved character questions, rather than relying solely on SFX cues.",
        },
        {
            "category": "Multi-Segment Visual & Audio Discontinuity",
            "description": "Stitching two segments from different scenes or episodes (e.g. Cathedral altar to rainy woods) can create jarring tonal dissonance. Without a crossfade or audio bridge, a cold viewer experiences cognitive whiplash.",
            "impact": "Viewer confusion regarding character location, wardrobe, and timeline.",
            "mitigation": "Restrict stitched promos to segments that share identical location headings or involve immediate cause-and-effect character actions.",
        },
        {
            "category": "Micro-Boundary Clipping & Cadence Chopping",
            "description": "Automated time boundaries that cut off an actor mid-breath, mid-sentence, or right as the background score resolves rather than holding the unresolved tension.",
            "impact": "The promo feels mechanically truncated or defective.",
            "mitigation": "Snap candidate boundaries strictly to beat ends and use LLM offset refinement to ensure natural sentence cadences.",
        },
    ]

    def audit_candidates(
        self, candidates: List[PromoCandidate], evaluations: Dict[str, LLMEvalResult]
    ) -> QualityAuditReport:
        warnings = []

        for cand in candidates:
            ev = evaluations.get(cand.candidate_id)
            cand_warnings = []

            # 1. Check for passive action trap (hook is purely action with no dialogue)
            opening_beats = [b for b in cand.segments[0].beats if b.start_time <= cand.segments[0].start_time + 4.0]
            opening_dialogue = [b for b in opening_beats if b.beat_type == BeatType.DIALOGUE]
            if not opening_dialogue and any(b.beat_type == BeatType.ACTION for b in opening_beats):
                cand_warnings.append("Hook consists solely of physical action/reaction with no spoken dialogue; risks slow pacing on TikTok.")

            # 2. Check for late episode lore trap
            min_ep = min(s.episode_num for s in cand.segments)
            if min_ep > 25 and (ev and ev.cold_audience_clarity < 6.5):
                cand_warnings.append(f"Episode {min_ep} relies on late-series narrative context; cold viewers may not understand secondary character stakes.")

            # 3. Check for SFX reliance with weak terminal dialogue
            terminal_beats = [b for b in cand.segments[-1].beats if b.end_time >= cand.segments[-1].end_time - 4.0]
            has_sfx = any("cliffhanger" in b.content.lower() for b in terminal_beats)
            terminal_dialogue = [b for b in terminal_beats if b.beat_type == BeatType.DIALOGUE]
            if has_sfx and not terminal_dialogue:
                cand_warnings.append("Cliffhanger relies heavily on SFX audio swell without an unresolved dialogue hook or dramatic ultimatum.")

            # 4. Check for stitched discontinuity
            if cand.promo_type == "stitched" and len(cand.segments) > 1:
                ep1 = cand.segments[0].episode_num
                ep2 = cand.segments[1].episode_num
                if ep1 != ep2:
                    cand_warnings.append(f"Stitches across episodes (Ep {ep1} -> Ep {ep2}); requires careful visual transition during editing.")

            if cand_warnings:
                warnings.append({
                    "candidate_id": cand.candidate_id,
                    "episodes": cand.episode_numbers,
                    "warnings": cand_warnings,
                })

        recommendations = [
            "Always preview the first 2 seconds on actual mobile vertical frame (9:16) to verify that physical action reads dynamically without relying on reading stage directions.",
            "For cold acquisition on TikTok, prioritize Episodes 1-4 promos where the emotional premise is universally self-explanatory (wedding altar abandonment).",
            "When using stitched promos across different locations, add a quick 0.5s audio bridge or whoosh sound effect so viewers perceive it as a deliberate trailer cut rather than a playback error.",
            "Avoid using promos from late episodes (> Ep 30) for cold audiences; deploy them exclusively as retargeting ads to viewers who have already completed Episode 5.",
        ]

        return QualityAuditReport(
            total_candidates_audited=len(candidates),
            flagged_candidates_count=len(warnings),
            systemic_failure_modes=self.SYSTEMIC_FAILURE_MODES,
            candidate_quality_warnings=warnings,
            recommendations_for_editors=recommendations,
        )

