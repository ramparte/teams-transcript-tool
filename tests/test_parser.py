"""Tests for transcript parser module."""

import tempfile
from pathlib import Path

import pytest

from teams_transcript.models import Utterance
from teams_transcript.parser import (
    _merge_consecutive_utterances,
    _normalize_timestamp,
    parse_transcript,
    parse_vtt,
)


# Sample VTT content for testing
SAMPLE_VTT = """WEBVTT

00:00:00.000 --> 00:00:05.000
<v Alice Smith>Hello everyone, welcome to the meeting.</v>

00:00:05.500 --> 00:00:10.000
<v Bob Jones>Thanks Alice! Glad to be here.</v>

00:00:10.500 --> 00:00:15.000
<v Alice Smith>Let's get started with the agenda.</v>
"""

SAMPLE_VTT_CONSECUTIVE = """WEBVTT

00:00:00.000 --> 00:00:05.000
<v Alice Smith>Hello everyone.</v>

00:00:05.500 --> 00:00:10.000
<v Alice Smith>Welcome to the meeting.</v>

00:00:10.500 --> 00:00:15.000
<v Bob Jones>Thanks Alice!</v>
"""


class TestParseVtt:
    """Tests for VTT parsing."""

    def test_parse_valid_vtt(self, tmp_path: Path) -> None:
        """Test parsing a valid VTT file."""
        vtt_file = tmp_path / "test.vtt"
        vtt_file.write_text(SAMPLE_VTT)

        utterances = parse_vtt(vtt_file)

        assert len(utterances) == 3
        assert utterances[0].speaker == "Alice Smith"
        assert utterances[0].timestamp == "00:00:00"
        assert "Hello everyone" in utterances[0].text
        assert utterances[1].speaker == "Bob Jones"

    def test_parse_vtt_merges_consecutive(self, tmp_path: Path) -> None:
        """Test that consecutive utterances from same speaker are merged."""
        vtt_file = tmp_path / "test.vtt"
        vtt_file.write_text(SAMPLE_VTT_CONSECUTIVE)

        utterances = parse_vtt(vtt_file)

        # Alice's two consecutive utterances should be merged
        assert len(utterances) == 2
        assert utterances[0].speaker == "Alice Smith"
        assert "Hello everyone" in utterances[0].text
        assert "Welcome to the meeting" in utterances[0].text

    def test_parse_vtt_file_not_found(self, tmp_path: Path) -> None:
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            parse_vtt(tmp_path / "nonexistent.vtt")

    def test_parse_vtt_invalid_format(self, tmp_path: Path) -> None:
        """Test error handling for invalid VTT format."""
        vtt_file = tmp_path / "invalid.vtt"
        vtt_file.write_text("This is not a valid VTT file")

        with pytest.raises(ValueError, match="missing WEBVTT header"):
            parse_vtt(vtt_file)


class TestParseTranscript:
    """Tests for auto-detection parsing."""

    def test_parse_transcript_vtt(self, tmp_path: Path) -> None:
        """Test auto-detection of VTT files."""
        vtt_file = tmp_path / "test.vtt"
        vtt_file.write_text(SAMPLE_VTT)

        utterances = parse_transcript(vtt_file)

        assert len(utterances) > 0
        assert all(isinstance(u, Utterance) for u in utterances)

    def test_parse_transcript_unsupported(self, tmp_path: Path) -> None:
        """Test error handling for unsupported formats."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Some content")

        with pytest.raises(ValueError, match="Unsupported file format"):
            parse_transcript(txt_file)


class TestNormalizeTimestamp:
    """Tests for timestamp normalization."""

    def test_normalize_short_hour(self) -> None:
        """Test normalizing single-digit hour."""
        assert _normalize_timestamp("0:01:23") == "00:01:23"

    def test_normalize_full_timestamp(self) -> None:
        """Test normalizing already-full timestamp."""
        assert _normalize_timestamp("12:34:56") == "12:34:56"


class TestMergeConsecutiveUtterances:
    """Tests for utterance merging."""

    def test_merge_same_speaker(self) -> None:
        """Test merging consecutive same-speaker utterances."""
        utterances = [
            Utterance("Alice", "00:00:00", "Hello."),
            Utterance("Alice", "00:00:05", "How are you?"),
            Utterance("Bob", "00:00:10", "Good!"),
        ]

        merged = _merge_consecutive_utterances(utterances)

        assert len(merged) == 2
        assert merged[0].speaker == "Alice"
        assert "Hello." in merged[0].text
        assert "How are you?" in merged[0].text
        assert merged[0].timestamp == "00:00:00"  # Keeps first timestamp

    def test_merge_empty_list(self) -> None:
        """Test merging empty list."""
        assert _merge_consecutive_utterances([]) == []

    def test_merge_single_utterance(self) -> None:
        """Test merging single utterance."""
        utterances = [Utterance("Alice", "00:00:00", "Hello.")]

        merged = _merge_consecutive_utterances(utterances)

        assert len(merged) == 1
        assert merged[0].text == "Hello."

    def test_no_merge_different_speakers(self) -> None:
        """Test no merging when speakers alternate."""
        utterances = [
            Utterance("Alice", "00:00:00", "Hello."),
            Utterance("Bob", "00:00:05", "Hi."),
            Utterance("Alice", "00:00:10", "Bye."),
        ]

        merged = _merge_consecutive_utterances(utterances)

        assert len(merged) == 3
