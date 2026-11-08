"""Unit tests for CandidateGenerator."""

import unittest
from src.microdrama_parser import parse_all_episodes
from src.candidate_generator import CandidateGenerator


class TestCandidateGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scripts_dir = r"I Married a Broken Soldier. He was a Duke-scripts (2) (1)\I Married a Broken Soldier. He was a Duke"
        cls.episodes = parse_all_episodes(scripts_dir)

    def test_single_segment_generation(self):
        generator = CandidateGenerator(min_duration=20.0, max_duration=60.0)
        # Test on Episode 1
        ep1_candidates = generator.generate_single_segment_candidates(self.episodes[0])
        self.assertGreater(len(ep1_candidates), 0)
        for c in ep1_candidates:
            self.assertGreaterEqual(c.total_duration, 20.0)
            self.assertLessEqual(c.total_duration, 60.0)
            self.assertGreaterEqual(c.hook_score, 3.5)
            self.assertGreaterEqual(c.cliffhanger_score, 3.5)

    def test_stitched_generation(self):
        generator = CandidateGenerator(min_duration=20.0, max_duration=60.0)
        stitched = generator.generate_stitched_candidates(self.episodes[:5])
        self.assertGreater(len(stitched), 0)
        for c in stitched:
            self.assertEqual(len(c.segments), 2)
            self.assertGreaterEqual(c.total_duration, 20.0)
            self.assertLessEqual(c.total_duration, 60.0)

    def test_nms_deduplication(self):
        generator = CandidateGenerator(min_duration=20.0, max_duration=60.0)
        all_candidates = []
        for ep in self.episodes[:10]:
            all_candidates.extend(generator.generate_single_segment_candidates(ep))
        initial_count = len(all_candidates)
        deduped = generator.non_maximum_suppression(all_candidates, iou_threshold=0.5, max_per_episode=2)
        self.assertLess(len(deduped), initial_count)
        self.assertGreater(len(deduped), 5)


if __name__ == "__main__":
    unittest.main()

