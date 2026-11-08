"""Candidate Promo Generator for Microdrama Screenplays.

Generates both continuous (single-segment) and stitched (multi-segment) promo candidates
ranging between 20 to 60 seconds with explosive 3-second hooks and unresolved cliffhangers.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Set

from src.microdrama_parser import ScriptBeat, Scene, Episode, BeatType, seconds_to_timestamp


# High-impact lexicon for hooks and cliffhangers
PHYSICAL_HOOK_KEYWORDS = {
    "slap", "slaps", "strike", "strikes", "grab", "grabs", "seize", "seizes",
    "tear", "tears", "rip", "rips", "push", "pushes", "shove", "kneel", "kneels",
    "smash", "drop", "drops", "blade", "sword", "weapon", "blood", "collar",
    "throat", "choke", "drag", "drags", "force", "forces", "clutch", "clutches"
}

CONFLICT_HOOK_KEYWORDS = {
    "plain", "worthless", "low value", "refuse", "never", "disgrace", "shame",
    "turn around", "not anymore", "beggar", "duke", "marry", "divorce", "bastard",
    "dare", "who are you", "mistake", "ruined", "trash", "servant", "impudent",
    "unworthy", "cast aside", "replace", "traitor", "scum", "unfaithful"
}

HIGH_TENSION_EMOTIONS = {
    "cold", "callous", "commanding", "shocked", "horrified", "furious",
    "derisive", "arrogant", "conceited", "desperate", "pleading", "venomous",
    "scornful", "menacing", "cruel", "mocking", "defiant", "blunt"
}

CLIFFHANGER_KEYWORDS = {
    "cliffhanger", "drone swells", "ominous peak", "cut to black", "abrupt cut",
    "swelling score", "holding into", "stinger", "blackout", "shocked silence"
}


@dataclass
class PromoSegment:
    episode_num: int
    start_time: float
    end_time: float
    beats: List[ScriptBeat] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)

    @property
    def start_timestamp(self) -> str:
        return seconds_to_timestamp(self.start_time)

    @property
    def end_timestamp(self) -> str:
        return seconds_to_timestamp(self.end_time)

    @property
    def transcript(self) -> str:
        lines = []
        for b in self.beats:
            if b.beat_type == BeatType.DIALOGUE and b.speaker:
                emo = f" ({b.emotion})" if b.emotion else ""
                lines.append(f'{b.speaker}{emo}: "{b.content}"')
            elif b.beat_type == BeatType.ACTION:
                lines.append(f"[ACTION: {b.content}]")
            elif b.beat_type == BeatType.CAMERA:
                lines.append(f"[CAMERA: {b.content}]")
            elif b.beat_type in (BeatType.SOUND_FX, BeatType.MUSIC):
                lines.append(f"[SFX: {b.content}]")
        return "\n".join(lines)


@dataclass
class PromoCandidate:
    candidate_id: str
    promo_type: str  # "continuous" or "stitched"
    segments: List[PromoSegment]
    hook_score: float
    cliffhanger_score: float
    pacing_score: float
    clarity_score: float
    heuristic_score: float
    hook_summary: str
    cliffhanger_summary: str
    primary_characters: List[str] = field(default_factory=list)

    @property
    def total_duration(self) -> float:
        return sum(s.duration for s in self.segments)

    @property
    def episode_numbers(self) -> List[int]:
        return sorted(list(set(s.episode_num for s in self.segments)))

    def get_full_transcript(self) -> str:
        parts = []
        for i, seg in enumerate(self.segments):
            header = f"--- SEGMENT {i+1} [Episode {seg.episode_num} | {seg.start_timestamp} - {seg.end_timestamp} ({seg.duration:.1f}s)] ---"
            parts.append(header)
            parts.append(seg.transcript)
        return "\n\n".join(parts)


class CandidateGenerator:
    """Generates and ranks promo candidates using deterministic domain heuristics."""

    def __init__(self, min_duration: float = 20.0, max_duration: float = 60.0):
        self.min_duration = min_duration
        self.max_duration = max_duration

    def evaluate_hook(self, beats: List[ScriptBeat], window_start: float) -> Tuple[float, str]:
        """Score the opening 3-4 seconds of a candidate promo."""
        opening_beats = [
            b for b in beats
            if b.start_time < window_start + 4.0 and b.end_time > window_start
        ]
        if not opening_beats:
            return 0.0, "No opening beats found"

        score = 0.0
        reasons = []

        for b in opening_beats:
            content_lower = b.content.lower()

            # Physical action hook
            phys_hits = [w for w in PHYSICAL_HOOK_KEYWORDS if w in content_lower]
            if phys_hits:
                score += 3.5
                reasons.append(f"Physical action: {', '.join(phys_hits[:2])}")

            # Verbal confrontation / status challenge
            conflict_hits = [w for w in CONFLICT_HOOK_KEYWORDS if w in content_lower]
            if conflict_hits:
                score += 3.0
                reasons.append(f"Shocking line/betrayal: {', '.join(conflict_hits[:2])}")

            # Intense emotional delivery
            if b.emotion:
                emo_lower = b.emotion.lower()
                matched_emos = [e for e in HIGH_TENSION_EMOTIONS if e in emo_lower]
                if matched_emos:
                    score += 2.0
                    reasons.append(f"High-tension delivery: {', '.join(matched_emos[:2])}")

            # Camera punch: close-up on tears, tight insert, sudden confrontation
            if b.beat_type == BeatType.CAMERA:
                if any(k in content_lower for k in ["close-up", "extreme close-up", "tight insert", "tracking"]):
                    score += 1.5

            # Dialogue opening is punchy for mobile feeds
            if b.beat_type == BeatType.DIALOGUE and b.content:
                score += 1.0

        # Cap score at 10.0
        final_score = min(10.0, round(score, 1))
        summary = "; ".join(reasons) if reasons else "Moderate opening tension"
        return final_score, summary

    def evaluate_cliffhanger(self, beats: List[ScriptBeat], window_end: float) -> Tuple[float, str]:
        """Score the ending 3-4 seconds of a candidate promo."""
        terminal_beats = [
            b for b in beats
            if b.end_time > window_end - 4.0 and b.start_time < window_end
        ]
        if not terminal_beats:
            return 0.0, "No terminal beats found"

        score = 0.0
        reasons = []

        for b in terminal_beats:
            content_lower = b.content.lower()

            # SFX / Music Cliffhanger cue
            sfx_hits = [w for w in CLIFFHANGER_KEYWORDS if w in content_lower]
            if sfx_hits or b.beat_type == BeatType.SOUND_FX:
                score += 4.0
                reasons.append(f"Cliffhanger audio/visual cue: {', '.join(sfx_hits[:2]) if sfx_hits else 'Sound swell'}")

            # Camera cut to black
            if b.beat_type == BeatType.CAMERA and ("cut to black" in content_lower or "holds" in content_lower):
                score += 3.0
                reasons.append("Cut to black / Dramatic hold")

            # Dialogue cliffhangers: question, interrupted sentence, dramatic ultimatum
            if b.beat_type == BeatType.DIALOGUE:
                if b.content.strip().endswith("?") or "?" in b.content:
                    score += 3.0
                    reasons.append("Unresolved hanging question")
                elif b.content.strip().endswith("...") or "..." in b.content:
                    score += 2.5
                    reasons.append("Interrupted declaration")
                elif any(w in content_lower for w in ["marry", "kill", "regret", "never", "leave", "pay"]):
                    score += 2.5
                    reasons.append("High-stakes ultimatum")

            # Physical action cliffhanger: weapon draw, glare, clenched fist
            if b.beat_type == BeatType.ACTION:
                if any(w in content_lower for w in ["defiance", "clench", "freeze", "kneel", "tears", "blade"]):
                    score += 2.0
                    reasons.append("Tense physical standoff")

        final_score = min(10.0, round(score, 1))
        summary = "; ".join(reasons) if reasons else "Standard scene transition"
        return final_score, summary

    def evaluate_standalone_clarity(self, beats: List[ScriptBeat], episode_num: int) -> float:
        """Score how easily a cold viewer understands the scene without prior lore."""
        score = 5.0  # Base neutral score

        # Early episodes (1-10) have much higher universal clarity (wedding, family abuse, secret duke)
        if episode_num <= 5:
            score += 3.0
        elif episode_num <= 15:
            score += 1.5
        elif episode_num > 35:
            # Late episodes often involve convoluted subplots
            score -= 1.5

        # Dialogue density: pure action with no dialogue is confusing on TikTok; dialogue gives stakes
        dialogues = [b for b in beats if b.beat_type == BeatType.DIALOGUE]
        if len(dialogues) >= 3:
            score += 1.5
        elif len(dialogues) == 0:
            score -= 2.5

        # Check for presence of key archetypal figures (Juliana, Gerald, Clarissa, Duke/Soldier)
        speakers = {b.speaker.upper() for b in beats if b.speaker}
        key_figures = {"JULIANA", "LADY JULIANA", "GERALD", "THE FORMER GROOM", "CLARISSA", "MYSTERIOUS BEARDED MAN", "ALEXANDER", "DUKE"}
        if speakers.intersection(key_figures):
            score += 1.5

        return min(10.0, max(1.0, round(score, 1)))

    def generate_single_segment_candidates(self, episode: Episode) -> List[PromoCandidate]:
        """Extract continuous promo candidates between 20.0s and 60.0s within an episode."""
        candidates: List[PromoCandidate] = []
        beats = episode.all_beats
        if not beats:
            return candidates

        # Filter candidate start indices: must start on a dialogue or action or camera beat with some punch
        for start_idx in range(len(beats)):
            start_beat = beats[start_idx]
            start_time = start_beat.start_time

            # Scan forward for end beats that satisfy 20s <= duration <= 60s
            for end_idx in range(start_idx, len(beats)):
                end_beat = beats[end_idx]
                end_time = end_beat.end_time
                duration = end_time - start_time

                if duration < self.min_duration:
                    continue
                if duration > self.max_duration:
                    break  # Exceeded duration cap for this start_idx

                window_beats = beats[start_idx : end_idx + 1]

                # Evaluate Hook (first 3-4s)
                hook_score, hook_summary = self.evaluate_hook(window_beats, start_time)
                if hook_score < 3.5:
                    continue  # Weak hook, not viable for TikTok

                # Evaluate Cliffhanger (last 3-4s)
                cliff_score, cliff_summary = self.evaluate_cliffhanger(window_beats, end_time)
                if cliff_score < 3.5:
                    continue  # Weak cutoff

                # Evaluate Standalone Clarity
                clarity_score = self.evaluate_standalone_clarity(window_beats, episode.episode_num)

                # Pacing: optimal promo duration is 30-45s on TikTok/Shorts
                pacing_score = 10.0 - abs(38.0 - duration) * 0.25
                pacing_score = min(10.0, max(2.0, pacing_score))

                # Composite Heuristic Score
                heuristic = (
                    0.35 * hook_score
                    + 0.35 * cliff_score
                    + 0.20 * clarity_score
                    + 0.10 * pacing_score
                )

                # Extract speakers
                speakers = list(dict.fromkeys(b.speaker for b in window_beats if b.speaker))

                seg = PromoSegment(
                    episode_num=episode.episode_num,
                    start_time=start_time,
                    end_time=end_time,
                    beats=window_beats,
                )

                candidate = PromoCandidate(
                    candidate_id=f"EP{episode.episode_num:02d}_{int(start_time):03d}_{int(end_time):03d}",
                    promo_type="continuous",
                    segments=[seg],
                    hook_score=hook_score,
                    cliffhanger_score=cliff_score,
                    pacing_score=round(pacing_score, 1),
                    clarity_score=clarity_score,
                    heuristic_score=round(heuristic, 2),
                    hook_summary=hook_summary,
                    cliffhanger_summary=cliff_summary,
                    primary_characters=speakers,
                )
                candidates.append(candidate)

        return candidates

    def generate_stitched_candidates(self, episodes: List[Episode]) -> List[PromoCandidate]:
        """Extract high-voltage stitched promos combining 2 beats (Setup/Hook + Climax/Cliffhanger)."""
        stitched: List[PromoCandidate] = []

        # Find top setup beats (duration 10-25s with high hook score)
        setup_beats_pool: List[Tuple[int, float, float, List[ScriptBeat], float, str]] = []
        climax_beats_pool: List[Tuple[int, float, float, List[ScriptBeat], float, str]] = []

        for ep in episodes[:15]:  # Focus on early high-clarity episodes
            beats = ep.all_beats
            for i in range(len(beats)):
                for j in range(i, min(i + 12, len(beats))):
                    dur = beats[j].end_time - beats[i].start_time
                    sub = beats[i : j + 1]
                    if 12.0 <= dur <= 25.0:
                        h_score, h_sum = self.evaluate_hook(sub, beats[i].start_time)
                        if h_score >= 6.0:
                            setup_beats_pool.append((ep.episode_num, beats[i].start_time, beats[j].end_time, sub, h_score, h_sum))

                    if 12.0 <= dur <= 30.0:
                        c_score, c_sum = self.evaluate_cliffhanger(sub, beats[j].end_time)
                        if c_score >= 6.5:
                            climax_beats_pool.append((ep.episode_num, beats[i].start_time, beats[j].end_time, sub, c_score, c_sum))

        # Combine setups with climaxes chronologically
        for s_ep, s_start, s_end, s_beats, h_score, h_sum in setup_beats_pool:
            s_dur = s_end - s_start
            for c_ep, c_start, c_end, c_beats, c_score, c_sum in climax_beats_pool:
                # Chronological requirement
                if s_ep > c_ep:
                    continue
                if s_ep == c_ep and c_start <= s_end:
                    continue
                if (c_ep - s_ep) > 3:  # Too far apart loses narrative link
                    continue

                c_dur = c_end - c_start
                total_dur = s_dur + c_dur

                # Character continuity check: Juliana or Duke must be in both
                s_speakers = {b.speaker.upper() for b in s_beats if b.speaker}
                c_speakers = {b.speaker.upper() for b in c_beats if b.speaker}
                common = s_speakers.intersection(c_speakers)
                if not common and not any("JULIANA" in sp for sp in s_speakers | c_speakers):
                    continue

                clarity_score = self.evaluate_standalone_clarity(s_beats + c_beats, s_ep)
                pacing_score = 9.0  # Stitched promos inherently have fast progression

                heuristic = (
                    0.35 * h_score
                    + 0.35 * c_score
                    + 0.20 * clarity_score
                    + 0.10 * pacing_score
                )

                seg1 = PromoSegment(episode_num=s_ep, start_time=s_start, end_time=s_end, beats=s_beats)
                seg2 = PromoSegment(episode_num=c_ep, start_time=c_start, end_time=c_end, beats=c_beats)

                cand = PromoCandidate(
                    candidate_id=f"STITCH_EP{s_ep:02d}_{int(s_start):03d}__EP{c_ep:02d}_{int(c_start):03d}",
                    promo_type="stitched",
                    segments=[seg1, seg2],
                    hook_score=h_score,
                    cliffhanger_score=c_score,
                    pacing_score=pacing_score,
                    clarity_score=clarity_score,
                    heuristic_score=round(heuristic, 2),
                    hook_summary=h_sum,
                    cliffhanger_summary=c_sum,
                    primary_characters=list(dict.fromkeys(b.speaker for b in (s_beats + c_beats) if b.speaker)),
                )
                stitched.append(cand)

        return stitched

    def non_maximum_suppression(
        self, candidates: List[PromoCandidate], iou_threshold: float = 0.5, max_per_episode: int = 3
    ) -> List[PromoCandidate]:
        """Deduplicate overlapping windows using Temporal IoU and diversify episode representation."""
        # Sort by composite heuristic score descending
        candidates.sort(key=lambda c: c.heuristic_score, reverse=True)

        selected: List[PromoCandidate] = []
        episode_counts: dict[int, int] = {}

        for cand in candidates:
            # Check episode quota
            main_ep = cand.segments[0].episode_num
            if episode_counts.get(main_ep, 0) >= max_per_episode:
                continue

            # Check overlap against already selected candidates
            overlap = False
            for sel in selected:
                # Only check IoU if same type and same primary episode
                if cand.promo_type == "continuous" and sel.promo_type == "continuous":
                    if cand.segments[0].episode_num == sel.segments[0].episode_num:
                        c_start, c_end = cand.segments[0].start_time, cand.segments[0].end_time
                        s_start, s_end = sel.segments[0].start_time, sel.segments[0].end_time

                        intersection = max(0.0, min(c_end, s_end) - max(c_start, s_start))
                        union = max(c_end, s_end) - min(c_start, s_start)
                        iou = intersection / union if union > 0 else 0.0

                        if iou > iou_threshold:
                            overlap = True
                            break

            if not overlap:
                selected.append(cand)
                episode_counts[main_ep] = episode_counts.get(main_ep, 0) + 1

        return selected
