import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "live_realtime_api"))

from transcript import SegmentTracker  # noqa: E402


class SegmentTrackerTest(unittest.TestCase):
    def test_no_correction_when_deltas_match_completed(self):
        tracker = SegmentTracker()
        tracker.on_delta("source", "item_a", "Sawubona ")
        tracker.on_delta("source", "item_a", "unjani\n")
        self.assertIsNone(tracker.on_completed("source", "item_a", "Sawubona unjani"))

    def test_correction_when_model_revised_sent_words(self):
        tracker = SegmentTracker()
        tracker.on_delta("source", "item_a", "hello there ")
        tracker.on_delta("source", "item_a", "\n")
        self.assertEqual(tracker.on_completed("source", "item_a", "hi there friend"), "hi there friend")

    def test_empty_segment_after_deltas_is_a_correction(self):
        tracker = SegmentTracker()
        tracker.on_delta("source", "item_a", "um ")
        tracker.on_delta("source", "item_a", "\n")
        self.assertEqual(tracker.on_completed("source", "item_a", ""), "")

    def test_streams_and_items_are_tracked_separately(self):
        tracker = SegmentTracker()
        tracker.on_delta("source", "item_a", "Sawubona\n")
        tracker.on_delta("translated", "item_a", "Hello\n")
        tracker.on_delta("source", "item_b", "Ngiyabonga\n")
        self.assertIsNone(tracker.on_completed("translated", "item_a", "Hello"))
        self.assertIsNone(tracker.on_completed("source", "item_a", "Sawubona"))
        self.assertIsNone(tracker.on_completed("source", "item_b", "Ngiyabonga"))


if __name__ == "__main__":
    unittest.main()
