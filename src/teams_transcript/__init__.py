"""Teams Transcript Tool.

Convert Teams meeting transcripts (VTT/DOCX) to clean Markdown
and optionally push to GitHub.

Basic Usage:
    >>> from teams_transcript import parse_transcript, format_markdown
    >>> utterances = parse_transcript("meeting.vtt")
    >>> markdown = format_markdown(utterances)
"""

from .models import Utterance
from .parser import parse_transcript, parse_vtt, parse_docx
from .formatter import format_markdown

__all__ = [
    "Utterance",
    "parse_transcript",
    "parse_vtt",
    "parse_docx",
    "format_markdown",
]

__version__ = "0.1.0"
