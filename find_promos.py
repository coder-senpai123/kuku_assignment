#!/usr/bin/env python3
"""Main CLI Driver for Microdrama Promo Finder.

Reads microdrama screenplays across all episodes, extracts optimal 20-60 second promos,
evaluates them with LLM scoring within strict budget bounds, ranks them for user acquisition,
and audits for quality pitfalls.
"""

from __future__ import annotations
import argparse
import json
import os
import re
import sys
import time
from typing import List, Dict, Any, Optional

from src.microdrama_parser import parse_all_episodes, seconds_to_timestamp
from src.candidate_generator import CandidateGenerator, PromoCandidate
from src.llm_evaluator import LLMEvaluator, LLMEvalResult
from src.promo_ranker import PromoRanker, RankedPromo
from src.quality_auditor import QualityAuditor, QualityAuditReport


def sanitize_slug(name: str) -> str:
    """Sanitize show title into a clean filename slug."""
    slug = re.sub(r"[^\w\-]", "_", name)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "show"


def detect_show_name(scripts_dir: str, explicit_name: Optional[str] = None) -> str:
    """Detect clean show title from directory name or argument."""
    if explicit_name:
        return explicit_name.strip()
    norm = os.path.normpath(scripts_dir)
    base = os.path.basename(norm)
    if not base or base == ".":
        base = os.path.basename(os.path.dirname(norm))
    # Strip script wrappers
    clean = re.sub(r"-scripts.*", "", base, flags=re.IGNORECASE)
    return clean.strip() or "Microdrama"


def run_pipeline(
    scripts_dir: str,
    output_dir: str = "results",
    candidate_limit: int = 15,
    use_llm: bool = True,
    model: str = "openai/gpt-4o-mini",
    show_name_arg: Optional[str] = None,
    verbose: bool = False,
    reuse_cache: bool = True,
) -> None:
    start_time = time.time()
    os.makedirs(output_dir, exist_ok=True)

    show_name = detect_show_name(scripts_dir, show_name_arg)
    show_slug = sanitize_slug(show_name)

    json_path = os.path.join(output_dir, f"promo_{show_slug}.json")
    md_path = os.path.join(output_dir, f"promo_{show_slug}.md")

    print("=" * 80)
    print("🎬 MICRODRAMA PROMO FINDER & VIRAL RANKING ENGINE")
    print("=" * 80)
    print(f"🎭 Show Title:      {show_name}")
    print(f"📁 Scripts Path:    {scripts_dir}")
    print(f"⏱️  Duration Range:  20.0s - 60.0s")
    print(f"🤖 LLM Evaluator:   {'Active (' + model + ')' if use_llm else 'Disabled (Heuristic Mode)'}")
    print(f"💾 Output Files:    promo_{show_slug}.md & promo_{show_slug}.json")
    print("-" * 80)

    # 1. Parse Episodes
    print("\n[Step 1/5] Ingesting and Parsing Screenplays across all episodes...")
    episodes = parse_all_episodes(scripts_dir)
    total_scenes = sum(len(ep.scenes) for ep in episodes)
    total_beats = sum(len(ep.all_beats) for ep in episodes)
    total_runtime_min = sum(ep.total_duration for ep in episodes) / 60.0
    print(f"  ✓ Parsed {len(episodes)} episodes: {total_scenes} scenes, {total_beats} beats ({total_runtime_min:.1f} mins total runtime).")

    # 2. Heuristic Candidate Generation
    print("\n[Step 2/5] Generating Promo Candidates (Single-Segment & Stitched)...")
    generator = CandidateGenerator(min_duration=20.0, max_duration=60.0)

    single_candidates: List[PromoCandidate] = []
    for ep in episodes:
        single_candidates.extend(generator.generate_single_segment_candidates(ep))

    stitched_candidates = generator.generate_stitched_candidates(episodes)
    raw_total = len(single_candidates) + len(stitched_candidates)
    print(f"  ✓ Found {raw_total} raw candidate windows ({len(single_candidates)} continuous, {len(stitched_candidates)} stitched).")

    # Non-Maximum Suppression (NMS) Filtering
    print("  Applying NMS Temporal IoU <= 0.45 & Diversity Filter...")
    all_raw = single_candidates + stitched_candidates
    filtered_candidates = generator.non_maximum_suppression(all_raw, iou_threshold=0.45, max_per_episode=2)
    top_candidates = filtered_candidates[:candidate_limit]
    print(f"  ✓ Selected top {len(top_candidates)} highest-scoring candidates for deep evaluation.")

    # 3. LLM Evaluation (with optional cache check)
    cached_evals: Dict[str, Any] = {}
    if reuse_cache and os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                for p in old_data.get("ranked_promos", []):
                    cached_evals[p["candidate_id"]] = p
        except Exception:
            pass

    print(f"\n[Step 3/5] Evaluating Candidates with LLM (OpenRouter: {model})...")
    evaluator = LLMEvaluator(model=model) if use_llm else LLMEvaluator(api_key="")
    evaluations: Dict[str, LLMEvalResult] = {}

    cache_hits = 0
    for idx, cand in enumerate(top_candidates):
        cid = cand.candidate_id
        if reuse_cache and cid in cached_evals:
            old_p = cached_evals[cid]
            evaluations[cid] = LLMEvalResult(
                candidate_id=cid,
                hook_power=old_p["metrics"]["hook_score"],
                cliffhanger_pull=old_p["metrics"]["cliffhanger_score"],
                cold_audience_clarity=old_p["metrics"]["clarity_score"],
                viral_retention_score=old_p["metrics"]["viral_score"],
                composite_llm_score=old_p["composite_score"],
                hook_description=old_p["hook"],
                cliffhanger_description=old_p["cliffhanger"],
                why_it_works=old_p["why_it_works"],
                refined_start_offset=0.0,
                refined_end_offset=0.0,
                tokens_used=0,
                estimated_cost_usd=0.0,
            )
            cache_hits += 1
            print(f"  Candidate {idx+1}/{len(top_candidates)}: {cid} [Cached] Score: {old_p['composite_score']}/10")
        else:
            print(f"  Candidate {idx+1}/{len(top_candidates)}: {cid} ({cand.promo_type}, {cand.total_duration:.1f}s)...", end="", flush=True)
            res = evaluator.evaluate_candidate(cand)
            evaluations[cid] = res
            print(f" Done! (Composite: {res.composite_llm_score}/10, Cost: ${res.estimated_cost_usd:.5f})")

    total_cost = evaluator.total_cost_usd
    total_tokens = evaluator.total_prompt_tokens + evaluator.total_completion_tokens
    print(f"  ✓ Evaluation complete. New Tokens: {total_tokens:,} | New Spend: ${total_cost:.5f} USD | Cache Hits: {cache_hits}")

    # 4. Ranking & Posting Strategy
    print("\n[Step 4/5] Ranking Promos & Assigning Performance Funnel Strategy...")
    ranker = PromoRanker()
    ranked_promos = ranker.rank_promos(top_candidates, evaluations)

    # 5. Quality Audit
    print("\n[Step 5/5] Auditing Promos for Quality Pitfalls & Failure Modes...")
    auditor = QualityAuditor()
    audit_report = auditor.audit_candidates(top_candidates, evaluations)
    print(f"  ✓ Audited {audit_report.total_candidates_audited} candidates ({audit_report.flagged_candidates_count} items with quality notes).")

    # Display Concise Summary Table on Terminal
    print("\n" + "=" * 80)
    print(f"🏆 TOP RANKED PROMOS: {show_name.upper()}")
    print("=" * 80)
    header = f"{'Rank':<5} | {'Type':<10} | {'Dur':<6} | {'Segments':<30} | {'Score':<5} | {'Launch Priority'}"
    print(header)
    print("-" * 80)

    for promo in ranked_promos:
        # Compact segments string
        seg_parts = []
        for s in promo.segments:
            seg_parts.append(f"Ep{s['episode']} [{s['start_timestamp'][:5]}-{s['end_timestamp'][:5]}]")
        segs_str = " + ".join(seg_parts)
        if len(segs_str) > 30:
            segs_str = segs_str[:27] + "..."

        prio_short = promo.posting_priority.split("(")[0].strip()
        print(f"#{promo.rank:<4} | {promo.promo_type.upper():<10} | {promo.total_duration:<5.1f}s | {segs_str:<30} | {promo.composite_score:<5.2f} | {prio_short}")

        if verbose:
            print(f"       🪝 Hook:        {promo.hook}")
            print(f"       🧗 Cliffhanger: {promo.cliffhanger}")
            print(f"       💡 Why It Works: {promo.why_it_works}\n")

    print("-" * 80)

    # Save Results
    export_data = {
        "metadata": {
            "show_title": show_name,
            "show_slug": show_slug,
            "total_episodes": len(episodes),
            "evaluated_candidates": len(ranked_promos),
            "total_llm_cost_usd": total_cost,
            "total_tokens_used": total_tokens,
            "execution_time_seconds": round(time.time() - start_time, 2),
        },
        "ranked_promos": [
            {
                "rank": p.rank,
                "candidate_id": p.candidate_id,
                "promo_type": p.promo_type,
                "total_duration_seconds": p.total_duration,
                "composite_score": p.composite_score,
                "funnel_tier": p.funnel_tier,
                "posting_priority": p.posting_priority,
                "posting_rationale": p.posting_rationale,
                "segments": p.segments,
                "hook": p.hook,
                "cliffhanger": p.cliffhanger,
                "why_it_works": p.why_it_works,
                "metrics": {
                    "hook_score": p.hook_score,
                    "cliffhanger_score": p.cliffhanger_score,
                    "clarity_score": p.clarity_score,
                    "viral_score": p.viral_score,
                },
            }
            for p in ranked_promos
        ],
        "quality_audit": {
            "total_audited": audit_report.total_candidates_audited,
            "flagged_count": audit_report.flagged_candidates_count,
            "systemic_failure_modes": audit_report.systemic_failure_modes,
            "candidate_warnings": audit_report.candidate_quality_warnings,
            "recommendations": audit_report.recommendations_for_editors,
        },
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2)

    generate_markdown_report(md_path, export_data)

    elapsed = time.time() - start_time
    print(f"\n💾 Files saved successfully:")
    print(f"   📄 Markdown Report: {md_path}")
    print(f"   📦 JSON Data:       {json_path}")
    print(f"\n✨ Promo discovery finished in {elapsed:.1f}s.")


def generate_markdown_report(path: str, data: Dict[str, Any]) -> None:
    lines = []
    lines.append(f"# Microdrama Promo Selection & Performance Marketing Report: {data['metadata']['show_title']}")
    lines.append(f"**Total Screenplay Episodes**: {data['metadata']['total_episodes']}")
    lines.append(f"**LLM Evaluation Cost**: ${data['metadata']['total_llm_cost_usd']:.5f} USD | **Tokens Used**: {data['metadata']['total_tokens_used']:,}\n")

    lines.append("## Executive Summary")
    lines.append(f"This report presents the highest-converting video promos extracted from all episodes of *{data['metadata']['show_title']}*. "
                 f"Each promo is optimized for vertical video platforms (TikTok, Instagram Reels, YouTube Shorts): strictly 20–60 seconds, "
                 f"opening on a high-arousal 3-second hook, ending on an unresolved cliffhanger, and completely intelligible to cold audiences.\n")

    lines.append("## Ranked Promos & Strategic Posting Schedule\n")
    for p in data["ranked_promos"]:
        lines.append(f"### Rank #{p['rank']}: {p['candidate_id']} ({p['promo_type'].upper()}, {p['total_duration_seconds']:.1f}s)")
        lines.append(f"- **Composite Viral Score**: `{p['composite_score']}/10`")
        lines.append(f"- **Funnel Tier**: **{p['funnel_tier']}**")
        lines.append(f"- **Launch Timing**: `{p['posting_priority']}`")
        lines.append(f"- **Posting Rationale**: {p['posting_rationale']}")
        lines.append("\n**Timestamps & Segments (in order):**")
        for idx, s in enumerate(p["segments"]):
            lines.append(f"  {idx+1}. **Episode {s['episode']}**: `{s['start_timestamp']}` to `{s['end_timestamp']}` ({s['duration_seconds']:.1f}s)")
        lines.append(f"\n- **The Hook (First 3s)**: {p['hook']}")
        lines.append(f"- **The Cliffhanger**: {p['cliffhanger']}")
        lines.append(f"- **Why It Works**: *\"{p['why_it_works']}\"*")
        lines.append("\n---\n")

    lines.append("## Quality Check: Where Does the Tool Pick Badly?")
    lines.append("Automated screenplay analysis has intrinsic boundaries. Below is a detailed audit of where algorithmic selection fails and how human editors should inspect the cuts:\n")

    qa = data["quality_audit"]
    for idx, fm in enumerate(qa["systemic_failure_modes"], 1):
        lines.append(f"### {idx}. {fm['category']}")
        lines.append(f"- **The Pitfall**: {fm['description']}")
        lines.append(f"- **Audience Impact**: {fm['impact']}")
        lines.append(f"- **Algorithmic Mitigation**: {fm['mitigation']}\n")

    lines.append("### Recommendations for Editors")
    for r in qa["recommendations"]:
        lines.append(f"- {r}")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Find best promos in a microdrama screenplay.")
    parser.add_argument(
        "--scripts-dir",
        type=str,
        default=r"I Married a Broken Soldier. He was a Duke-scripts (2) (1)\I Married a Broken Soldier. He was a Duke",
        help="Path to directory containing episode script files.",
    )
    parser.add_argument(
        "--show-name",
        type=str,
        default=None,
        help="Optional explicit title of the show (auto-detected if omitted).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Directory to save output json and markdown reports.",
    )
    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=15,
        help="Number of top candidates to evaluate with LLM and rank (default: 15).",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM evaluation and use heuristic scores only.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass cached evaluations and re-run all calls against OpenRouter.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print verbose details (hook, cliffhanger, rationale) for all promos in terminal.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="openai/gpt-4o-mini",
        help="OpenRouter model identifier (default: openai/gpt-4o-mini).",
    )

    args = parser.parse_args()
    run_pipeline(
        scripts_dir=args.scripts_dir,
        output_dir=args.output_dir,
        candidate_limit=args.candidate_limit,
        use_llm=not args.no_llm,
        model=args.model,
        show_name_arg=args.show_name,
        verbose=args.verbose,
        reuse_cache=not args.no_cache,
    )


if __name__ == "__main__":
    main()
