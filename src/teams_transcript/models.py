"""Data models for Teams Transcript Tool.

This module defines the core data structures used throughout the application.
"""

from dataclasses import dataclass


@dataclass
class Utterance:
    """A single spoken segment from a transcript.

    Represents one speaker's utterance at a specific point in time.

    Attributes:
        speaker: Name of the person speaking
        timestamp: Time in HH:MM:SS format
        text: The spoken content

    Example:
        >>> u = Utterance(speaker="John Doe", timestamp="00:01:23", text="Hello everyone")
        >>> print(f"{u.speaker} at {u.timestamp}: {u.text}")
        John Doe at 00:01:23: Hello everyone
    """

    speaker: str
    timestamp: str  # HH:MM:SS format
    text: str

    def __str__(self) -> str:
        """Return a human-readable representation."""
        return f"[{self.timestamp}] {self.speaker}: {self.text}"
