from __future__ import annotations

from notification_sound_db.catalog import classify


def test_classification_rules() -> None:
    assert classify("calls_incoming_ring_v2", "unknown") == "incoming_call"
    assert classify("calls_they_joined_call_v2", "unknown") == "call_state"
    assert classify("Mail Fetch Error", "unknown") == "error"
    assert classify("Mail Sent", "unknown") == "completion"
    assert classify("discord_message1", "unknown") == "message"
    assert classify("mystery", "unknown") == "unknown"
