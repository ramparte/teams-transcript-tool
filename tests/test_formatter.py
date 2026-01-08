"""Tests for markdown formatter module."""

import pytest

from teams_transcript.formatter import (
    _generate_empty_document,
    format_compact,
    format_markdown,
)
from teams_transcript.models import Utterance


class TestFormatMarkdown:
    """Tests for standard markdown formatting."""

    def test_format_basic(self) -> None:
        """Test basic formatting with utterances."""
        utterances = [
            Utterance("Alice", "00:00:10", "Hello everyone"),
            Utterance("Bob", "00:00:15", "Hi Alice!"),
        ]

        result = format_markdown(utterances)

        assert "**Alice**" in result
        assert "**Bob**" in result
        assert "Hello everyone" in result
        assert "Hi Alice!" in result
        assert "(00:00:10)" in result
        assert "(00:00:15)" in result

    def test_format_with_title(self) -> None:
        """Test formatting with custom title."""
        utterances = [Utterance("Alice", "00:00:00", "Test")]

        result = format_markdown(utterances, title="Team Meeting")

        assert "# Team Meeting" in result

    def test_format_without_timestamps(self) -> None:
        """Test formatting with timestamps disabled."""
        utterances = [Utterance("Alice", "00:00:10", "Hello")]

        result = format_markdown(utterances, include_timestamps=False)

        assert "**Alice**" in result
        assert "(00:00:10)" not in result

    def test_format_empty_utterances(self) -> None:
        """Test formatting empty utterance list."""
        result = format_markdown([])

        assert "No transcript content found" in result

    def test_format_empty_with_title(self) -> None:
        """Test empty formatting with title."""
        result = format_markdown([], title="Empty Meeting")

        assert "# Empty Meeting" in result
        assert "No transcript content found" in result

    def test_format_has_separators(self) -> None:
        """Test that separators appear between utterances."""
        utterances = [
            Utterance("Alice", "00:00:00", "First"),
            Utterance("Bob", "00:00:10", "Second"),
            Utterance("Alice", "00:00:20", "Third"),
        ]

        result = format_markdown(utterances)

        # Should have 2 separators (between 3 utterances)
        assert result.count("---") == 2

    def test_format_no_trailing_separator(self) -> None:
        """Test no separator after last utterance."""
        utterances = [
            Utterance("Alice", "00:00:00", "First"),
            Utterance("Bob", "00:00:10", "Last"),
        ]

        result = format_markdown(utterances)
        lines = result.strip().split("\n")

        # Last meaningful line should not be a separator
        last_content_line = [l for l in lines if l.strip() and l.strip() != "---"][-1]
        assert last_content_line != "---"


class TestFormatCompact:
    """Tests for compact markdown formatting."""

    def test_format_compact_basic(self) -> None:
        """Test basic compact formatting."""
        utterances = [
            Utterance("Alice", "00:00:10", "Hello everyone"),
            Utterance("Bob", "00:00:15", "Hi Alice!"),
        ]

        result = format_compact(utterances)

        assert "- **Alice** (00:00:10): Hello everyone" in result
        assert "- **Bob** (00:00:15): Hi Alice!" in result

    def test_format_compact_without_timestamps(self) -> None:
        """Test compact formatting without timestamps."""
        utterances = [Utterance("Alice", "00:00:10", "Hello")]

        result = format_compact(utterances, include_timestamps=False)

        assert "- **Alice**: Hello" in result
        assert "(00:00:10)" not in result

    def test_format_compact_with_title(self) -> None:
        """Test compact formatting with title."""
        utterances = [Utterance("Alice", "00:00:00", "Test")]

        result = format_compact(utterances, title="Quick Chat")

        assert "# Quick Chat" in result

    def test_format_compact_empty(self) -> None:
        """Test compact formatting with empty list."""
        result = format_compact([])

        assert "No transcript content found" in result


class TestGenerateEmptyDocument:
    """Tests for empty document generation."""

    def test_empty_no_title(self) -> None:
        """Test empty document without title."""
        result = _generate_empty_document()

        assert "No transcript content found" in result
        assert "#" not in result

    def test_empty_with_title(self) -> None:
        """Test empty document with title."""
        result = _generate_empty_document("Missing Transcript")

        assert "# Missing Transcript" in result
        assert "No transcript content found" in result
