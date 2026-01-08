"""Transcript parsing module.

Handles parsing of VTT and DOCX transcript formats into a unified
list of Utterance objects.
"""

import re
from pathlib import Path

from docx import Document

from .models import Utterance


def parse_vtt(file_path: Path | str) -> list[Utterance]:
    """Parse VTT file into utterances.

    VTT (WebVTT) files from Teams contain cue blocks with speaker info
    in the format:
        <v Speaker Name>Text content</v>

    Args:
        file_path: Path to .vtt file

    Returns:
        List of Utterance objects, chronologically ordered

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid

    Example:
        >>> utterances = parse_vtt("meeting.vtt")
        >>> for u in utterances:
        ...     print(f"{u.speaker}: {u.text}")
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"VTT file not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")

    # Check for WEBVTT header
    if not content.strip().startswith("WEBVTT"):
        raise ValueError(f"Invalid VTT file: missing WEBVTT header in {file_path}")

    utterances: list[Utterance] = []

    # Pattern to match timestamp lines: 00:00:00.000 --> 00:00:05.000
    timestamp_pattern = re.compile(
        r"(\d{2}:\d{2}:\d{2})\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}"
    )

    # Pattern to match speaker tags: <v Speaker Name>text</v> or <v Speaker Name>text (no closing tag)
    speaker_pattern = re.compile(r"<v\s+([^>]+)>(.*)(?:</v>)?$")

    lines = content.split("\n")
    current_timestamp = "00:00:00"

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check for timestamp line
        ts_match = timestamp_pattern.match(line)
        if ts_match:
            current_timestamp = ts_match.group(1)
            i += 1
            continue

        # Check for speaker content
        speaker_match = speaker_pattern.search(line)
        if speaker_match:
            speaker = speaker_match.group(1).strip()
            text = speaker_match.group(2).strip()

            # Collect continuation lines (text without speaker tag)
            while i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if not next_line or timestamp_pattern.match(next_line):
                    break
                # Check if next line has a speaker tag (new utterance)
                if speaker_pattern.search(next_line):
                    break
                # Plain text continuation
                if next_line and not next_line.startswith("<"):
                    text += " " + next_line
                i += 1

            if text:
                utterances.append(
                    Utterance(speaker=speaker, timestamp=current_timestamp, text=text)
                )

        i += 1

    return _merge_consecutive_utterances(utterances)


def parse_docx(file_path: Path | str) -> list[Utterance]:
    """Parse DOCX transcript into utterances.

    Teams DOCX transcripts typically have paragraphs in the format:
        Speaker Name
        0:01:23
        Text content

    Args:
        file_path: Path to .docx file

    Returns:
        List of Utterance objects, chronologically ordered

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid

    Example:
        >>> utterances = parse_docx("meeting.docx")
        >>> for u in utterances:
        ...     print(f"{u.speaker}: {u.text}")
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"DOCX file not found: {file_path}")

    try:
        doc = Document(file_path)
    except Exception as e:
        raise ValueError(f"Invalid DOCX file: {file_path} - {e}") from e

    utterances: list[Utterance] = []

    # Pattern to match timestamps: 0:01:23 or 00:01:23
    timestamp_pattern = re.compile(r"^(\d{1,2}:\d{2}:\d{2})$")

    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    i = 0
    while i < len(paragraphs):
        # Look for pattern: Speaker, Timestamp, Text
        if i + 2 < len(paragraphs):
            potential_speaker = paragraphs[i]
            potential_timestamp = paragraphs[i + 1]
            potential_text = paragraphs[i + 2]

            ts_match = timestamp_pattern.match(potential_timestamp)
            if ts_match:
                # Normalize timestamp to HH:MM:SS
                timestamp = _normalize_timestamp(ts_match.group(1))

                # Collect text until next speaker block
                text_parts = [potential_text]
                j = i + 3
                while j < len(paragraphs):
                    # Check if this starts a new speaker block
                    if j + 1 < len(paragraphs) and timestamp_pattern.match(
                        paragraphs[j + 1]
                    ):
                        break
                    text_parts.append(paragraphs[j])
                    j += 1

                utterances.append(
                    Utterance(
                        speaker=potential_speaker,
                        timestamp=timestamp,
                        text=" ".join(text_parts),
                    )
                )
                i = j
                continue

        i += 1

    if not utterances:
        raise ValueError(f"No valid transcript content found in {file_path}")

    return _merge_consecutive_utterances(utterances)


def parse_transcript(file_path: Path | str) -> list[Utterance]:
    """Auto-detect format and parse transcript.

    Dispatches to parse_vtt or parse_docx based on file extension.

    Args:
        file_path: Path to .vtt or .docx file

    Returns:
        List of Utterance objects, chronologically ordered

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is unsupported or invalid

    Example:
        >>> utterances = parse_transcript("meeting.vtt")
        >>> utterances = parse_transcript("meeting.docx")
    """
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    if extension == ".vtt":
        return parse_vtt(file_path)
    elif extension == ".docx":
        return parse_docx(file_path)
    else:
        raise ValueError(
            f"Unsupported file format: {extension}. Supported: .vtt, .docx"
        )


def _normalize_timestamp(timestamp: str) -> str:
    """Normalize timestamp to HH:MM:SS format.

    Args:
        timestamp: Time string in H:MM:SS or HH:MM:SS format

    Returns:
        Normalized HH:MM:SS string
    """
    parts = timestamp.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    return timestamp


def _merge_consecutive_utterances(utterances: list[Utterance]) -> list[Utterance]:
    """Merge consecutive utterances from the same speaker.

    Combines adjacent utterances from the same speaker into a single
    utterance to create cleaner output.

    Args:
        utterances: List of utterances to merge

    Returns:
        Merged list with consecutive same-speaker utterances combined
    """
    if not utterances:
        return []

    merged: list[Utterance] = []
    current = utterances[0]

    for next_utterance in utterances[1:]:
        if next_utterance.speaker == current.speaker:
            # Merge text, keep original timestamp
            current = Utterance(
                speaker=current.speaker,
                timestamp=current.timestamp,
                text=current.text + " " + next_utterance.text,
            )
        else:
            merged.append(current)
            current = next_utterance

    merged.append(current)
    return merged
