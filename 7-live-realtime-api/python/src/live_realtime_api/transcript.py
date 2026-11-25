"""
Track transcript text per segment so `completed` events can be checked against it.

The Live API streams each speech segment as append-only deltas (the last one ends in "\n"),
then sends one `completed` event with the segment's final text. Usually the deltas already
add up to that text. Occasionally the model revises words it had already sent, and then
`completed.transcript` is the version to keep.
"""


class SegmentTracker:
    def __init__(self) -> None:
        self._appended: dict[tuple[str, str | None], str] = {}

    def on_delta(self, stream: str, item_id: str | None, delta: str) -> None:
        key = (stream, item_id)
        self._appended[key] = self._appended.get(key, "") + delta

    def on_completed(self, stream: str, item_id: str | None, transcript: str) -> str | None:
        """Return the corrected text if it differs from what the deltas added up to, else None."""
        appended = self._appended.pop((stream, item_id), "").rstrip("\n")
        return transcript if transcript != appended else None
