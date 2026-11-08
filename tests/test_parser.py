"""Unit tests for MicrodramaParser."""

import unittest
from src.microdrama_parser import (
    timestamp_to_seconds,
    seconds_to_timestamp,
    MicrodramaParser,
    parse_all_episodes,
    BeatType,
)

SAMPLE_SCRIPT = """EPISODE NUMBER: Episode 1
EPISODE LOGLINE: Lady Juliana arrives at the cathedral.
CONTINUITY NOTES: First episode.

--- SCRIPT START ---

SCENE 01
Scene heading: INT. CATHEDRAL – DAY
Scene start: 00:00.00
Scene end: 02:18.00

Actions and dialogue:

**CAMERA:**
Start: (00:00.00) | End: (00:04.80)
Symmetrical framing on the heavy church doors.

**ACTION:**
Start: (00:01.00) | End: (00:04.80)
Juliana pauses at the threshold.

**MATRIARCH (Cold, Commanding):**
Start: (00:11.30) | End: (00:13.10)
"You should turn around, Juliana."

**LADY JULIANA (Confused, Breathless):**
Start: (00:13.50) | End: (00:14.30)
"Why?"

**SOUND FX:**
Start: (02:15.00) | End: (02:17.50)
Solemn low-pitched string drone swells to an ominous cliffhanger peak.

**CAMERA:**
Start: (02:17.00) | End: (02:18.00)
Cut to black.

--- SCRIPT END ---
"""


class TestMicrodramaParser(unittest.TestCase):
    def test_timestamp_conversions(self):
        self.assertEqual(timestamp_to_seconds("00:00.00"), 0.0)
        self.assertEqual(timestamp_to_seconds("01:30.50"), 90.5)
        self.assertEqual(timestamp_to_seconds("(02:18.00)"), 138.0)
        self.assertEqual(seconds_to_timestamp(90.5), "01:30.50")
        self.assertEqual(seconds_to_timestamp(138.0), "02:18.00")

    def test_parse_text(self):
        parser = MicrodramaParser()
        ep = parser.parse_text(SAMPLE_SCRIPT)
        self.assertEqual(ep.episode_num, 1)
        self.assertEqual(ep.logline, "Lady Juliana arrives at the cathedral.")
        self.assertEqual(len(ep.scenes), 1)
        sc = ep.scenes[0]
        self.assertEqual(sc.scene_id, "SCENE 01")
        self.assertEqual(sc.heading, "INT. CATHEDRAL – DAY")
        self.assertEqual(len(sc.beats), 6)

        # Check dialogue beat
        b_dialogue = sc.beats[2]
        self.assertEqual(b_dialogue.beat_type, BeatType.DIALOGUE)
        self.assertEqual(b_dialogue.speaker, "MATRIARCH")
        self.assertEqual(b_dialogue.emotion, "Cold, Commanding")
        self.assertEqual(b_dialogue.content, "You should turn around, Juliana.")
        self.assertEqual(b_dialogue.start_time, 11.3)
        self.assertEqual(b_dialogue.end_time, 13.1)

        # Check sound fx beat
        b_sfx = sc.beats[4]
        self.assertEqual(b_sfx.beat_type, BeatType.SOUND_FX)
        self.assertTrue("cliffhanger" in b_sfx.content.lower())

    def test_parse_all_50_episodes(self):
        scripts_dir = r"I Married a Broken Soldier. He was a Duke-scripts (2) (1)\I Married a Broken Soldier. He was a Duke"
        episodes = parse_all_episodes(scripts_dir)
        self.assertEqual(len(episodes), 50)
        self.assertEqual(episodes[0].episode_num, 1)
        self.assertEqual(episodes[-1].episode_num, 50)
        for ep in episodes:
            self.assertGreater(len(ep.scenes), 0)
            self.assertGreater(len(ep.all_beats), 0)
            self.assertGreater(ep.total_duration, 30.0)


if __name__ == "__main__":
    unittest.main()
