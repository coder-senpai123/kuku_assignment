"""Screenplay Parser for Microdrama Episodes.

Extracts structured scenes, characters, camera angles, actions, dialogue,
and sound effects with millisecond-accurate timestamps.
"""

from __future__ import annotations
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class BeatType(str, Enum):
    CAMERA = "CAMERA"
    ACTION = "ACTION"
    DIALOGUE = "DIALOGUE"
    SOUND_FX = "SOUND_FX"
    MUSIC = "MUSIC"
    OTHER = "OTHER"


def timestamp_to_seconds(ts: str) -> float:
    """Convert timestamp format (MM:SS.SS or MM:SS) to floating-point seconds."""
    ts = ts.strip().strip("()")
    match = re.search(r"(\d{1,2}):(\d{2})(?:\.(\d+))?", ts)
    if not match:
        try:
            return float(ts)
        except ValueError:
            return 0.0
    minutes = int(match.group(1))
    seconds = int(match.group(2))
    fraction_str = match.group(3)
    if fraction_str:
        fraction = float(f"0.{fraction_str}")
    else:
        fraction = 0.0
    return minutes * 60 + seconds + fraction


def seconds_to_timestamp(seconds: float) -> str:
    """Convert floating-point seconds back to MM:SS.SS format."""
    if seconds < 0:
        seconds = 0.0
    minutes = int(seconds // 60)
    rem_seconds = seconds - (minutes * 60)
    return f"{minutes:02d}:{rem_seconds:05.2f}"


@dataclass
class ScriptBeat:
    episode_num: int
    scene_id: str
    beat_type: BeatType
    start_time: float
    end_time: float
    content: str
    speaker: Optional[str] = None
    emotion: Optional[str] = None

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)

    @property
    def start_timestamp(self) -> str:
        return seconds_to_timestamp(self.start_time)

    @property
    def end_timestamp(self) -> str:
        return seconds_to_timestamp(self.end_time)


@dataclass
class Scene:
    episode_num: int
    scene_id: str
    heading: str
    start_time: float
    end_time: float
    beats: List[ScriptBeat] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)


@dataclass
class Episode:
    episode_num: int
    logline: str
    continuity_notes: str
    scenes: List[Scene] = field(default_factory=list)
    file_path: str = ""

    @property
    def total_duration(self) -> float:
        if not self.scenes:
            return 0.0
        return max(s.end_time for s in self.scenes)

    @property
    def all_beats(self) -> List[ScriptBeat]:
        beats = []
        for scene in self.scenes:
            beats.extend(scene.beats)
        return beats


class MicrodramaParser:
    """Parses raw microdrama screenplay TXT files into structured data models."""

    HEADER_PATTERN = re.compile(
        r"^\*\*(?P<tag>[A-Z0-9_\'\-\s\(\)\,]+?):\*\*\s*$", re.IGNORECASE
    )
    TIME_PATTERN = re.compile(
        r"Start:\s*\(?(?P<start>\d{1,2}:\d{2}(?:\.\d+)?)\)?\s*\|\s*End:\s*\(?(?P<end>\d{1,2}:\d{2}(?:\.\d+)?)\)?",
        re.IGNORECASE,
    )

    def parse_file(self, file_path: str) -> Episode:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self.parse_text(content, file_path=file_path)

    def parse_text(self, text: str, file_path: str = "") -> Episode:
        lines = text.splitlines()

        # 1. Parse Episode Metadata
        episode_num = 0
        logline = ""
        continuity_notes = ""

        for line in lines:
            line_strip = line.strip()
            if line_strip.startswith("EPISODE NUMBER:"):
                match = re.search(r"\d+", line_strip)
                if match:
                    episode_num = int(match.group(0))
            elif line_strip.startswith("EPISODE LOGLINE:"):
                logline = line_strip[len("EPISODE LOGLINE:"):].strip()
            elif line_strip.startswith("CONTINUITY NOTES:"):
                continuity_notes = line_strip[len("CONTINUITY NOTES:"):].strip()

        # If episode_num not parsed from header, try filename
        if episode_num == 0 and file_path:
            match = re.search(r"episode-(\d+)", os.path.basename(file_path), re.IGNORECASE)
            if match:
                episode_num = int(match.group(1))

        # 2. Extract script body
        script_started = False
        body_lines: List[str] = []
        for line in lines:
            if "--- SCRIPT START ---" in line:
                script_started = True
                continue
            if "--- SCRIPT END ---" in line:
                break
            if script_started:
                body_lines.append(line)

        # 3. Parse scenes and beats
        scenes: List[Scene] = []
        current_scene: Optional[Scene] = None

        i = 0
        n = len(body_lines)
        while i < n:
            line = body_lines[i].strip()

            # Scene header detection
            if line.startswith("SCENE ") and not line.startswith("SCENE END"):
                scene_id = line
                heading = ""
                scene_start = 0.0
                scene_end = 0.0

                # Lookahead for heading and scene timings
                j = i + 1
                while j < n:
                    sub_line = body_lines[j].strip()
                    sub_lower = sub_line.lower()
                    if sub_lower.startswith("actions and dialogue:"):
                        j += 1
                        break
                    elif sub_lower.startswith("scene heading:"):
                        heading = sub_line.split(":", 1)[1].strip()
                    elif sub_lower.startswith("scene start:"):
                        ts_val = sub_line.split(":", 1)[1].strip()
                        scene_start = timestamp_to_seconds(ts_val)
                    elif sub_lower.startswith("scene end:"):
                        ts_val = sub_line.split(":", 1)[1].strip()
                        scene_end = timestamp_to_seconds(ts_val)
                    elif sub_line.startswith("SCENE ") or self.HEADER_PATTERN.match(sub_line):
                        break
                    j += 1

                current_scene = Scene(
                    episode_num=episode_num,
                    scene_id=scene_id,
                    heading=heading,
                    start_time=scene_start,
                    end_time=scene_end,
                    beats=[],
                )
                scenes.append(current_scene)
                i = j
                continue

            # Beat header detection: **TAG:**
            tag_match = self.HEADER_PATTERN.match(line)
            if tag_match and current_scene:
                raw_tag = tag_match.group("tag").strip()

                # Next line usually contains Start: (MM:SS.SS) | End: (MM:SS.SS)
                beat_start = 0.0
                beat_end = 0.0
                content_lines: List[str] = []

                k = i + 1
                while k < n:
                    sub_line = body_lines[k].strip()
                    if not sub_line:
                        # Empty line, could be between time and content or end of beat
                        if content_lines:
                            break
                        k += 1
                        continue

                    time_match = self.TIME_PATTERN.search(sub_line)
                    if time_match and beat_start == 0.0 and beat_end == 0.0:
                        beat_start = timestamp_to_seconds(time_match.group("start"))
                        beat_end = timestamp_to_seconds(time_match.group("end"))
                        k += 1
                        continue

                    # If another beat or scene starts, stop
                    if self.HEADER_PATTERN.match(sub_line) or sub_line.startswith("SCENE "):
                        break

                    content_lines.append(sub_line)
                    k += 1

                content = " ".join(content_lines).strip()
                # Clean up wrapping quotes for dialogue
                if content.startswith('"') and content.endswith('"') and len(content) > 1:
                    content = content[1:-1]

                # Determine BeatType, Speaker, Emotion
                beat_type, speaker, emotion = self._categorize_tag(raw_tag)

                beat = ScriptBeat(
                    episode_num=episode_num,
                    scene_id=current_scene.scene_id,
                    beat_type=beat_type,
                    start_time=beat_start,
                    end_time=beat_end,
                    content=content,
                    speaker=speaker,
                    emotion=emotion,
                )
                current_scene.beats.append(beat)
                i = k
                continue

            i += 1

        # Fallback: if scene end time is 0.0, use the last beat's end_time
        for sc in scenes:
            if sc.end_time == 0.0 and sc.beats:
                sc.end_time = max(b.end_time for b in sc.beats)

        return Episode(
            episode_num=episode_num,
            logline=logline,
            continuity_notes=continuity_notes,
            scenes=scenes,
            file_path=file_path,
        )

    def _categorize_tag(self, raw_tag: str) -> Tuple[BeatType, Optional[str], Optional[str]]:
        upper = raw_tag.upper()
        if upper == "CAMERA":
            return BeatType.CAMERA, None, None
        if upper == "ACTION":
            return BeatType.ACTION, None, None
        if upper.startswith("SOUND FX") or upper.startswith("SFX"):
            return BeatType.SOUND_FX, None, None
        if upper.startswith("MUSIC"):
            return BeatType.MUSIC, None, None

        # Dialogue: contains character name and optional emotion in parentheses
        # e.g., "MATRIARCH (Cold, Commanding)", "THE FORMER GROOM (Off-screen) (Dismissive)"
        # Match outermost or multiple parentheses
        emotion_matches = re.findall(r"\((.*?)\)", raw_tag)
        speaker = re.sub(r"\(.*?\)", "", raw_tag).strip()
        emotion = ", ".join(m.strip() for m in emotion_matches) if emotion_matches else None

        return BeatType.DIALOGUE, speaker, emotion


def parse_all_episodes(scripts_dir: str) -> List[Episode]:
    """Parse all screenplay files in the directory sorted by episode number."""
    parser = MicrodramaParser()
    episodes: List[Episode] = []

    files = [
        os.path.join(scripts_dir, f)
        for f in os.listdir(scripts_dir)
        if f.endswith(".txt") and f.startswith("episode-")
    ]

    def extract_num(path: str) -> int:
        m = re.search(r"episode-(\d+)", os.path.basename(path), re.IGNORECASE)
        return int(m.group(1)) if m else 0

    files.sort(key=extract_num)

    for fpath in files:
        ep = parser.parse_file(fpath)
        episodes.append(ep)

    return episodes
