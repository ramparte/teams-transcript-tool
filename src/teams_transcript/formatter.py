"""Markdown formatting module.

Converts parsed utterances into clean, readable Markdown output.
"""

from datetime import datetime

from .models import Utterance


def format_markdown(
    utterances: list[Utterance],
    title: str | None = None,
    include_timestamps: bool = True,
) -> str:
    """Convert utterances to Markdown.

    Generates a clean Markdown document with optional title and timestamps.
    Groups consecutive utterances from the same speaker.

    Args:
        utterances: List of parsed utterances
        title: Optional document title (H1 header)
        include_timestamps: Whether to include timestamps (default: True)

    Returns:
        Formatted Markdown string

    Example:
        >>> utterances = [
        ...     Utterance("Alice", "00:00:10", "Hello everyone"),
        ...     Utterance("Bob", "00:00:15", "Hi Alice!"),
        ... ]
        >>> print(format_markdown(utterances, title="Team Meeting"))
        # Team Meeting

        **Alice** (00:00:10)

        Hello everyone

        ---

        **Bob** (00:00:15)

        Hi Alice!
    """
    if not utterances:
        return _generate_empty_document(title)

    lines: list[str] = []

    # Add title if provided
    if title:
        lines.append(f"# {title}")
        lines.append("")

    # Add metadata
    lines.append(f"*Transcript generated on {datetime.now().strftime('%Y-%m-%d')}*")
    lines.append("")

    # Format each utterance
    for i, utterance in enumerate(utterances):
        # Speaker header with optional timestamp
        if include_timestamps:
            lines.append(f"**{utterance.speaker}** ({utterance.timestamp})")
        else:
            lines.append(f"**{utterance.speaker}**")

        lines.append("")

        # Utterance text
        lines.append(utterance.text)
        lines.append("")

        # Add separator between utterances (except after last one)
        if i < len(utterances) - 1:
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def format_compact(
    utterances: list[Utterance],
    title: str | None = None,
    include_timestamps: bool = True,
) -> str:
    """Convert utterances to compact Markdown format.

    A more condensed format with utterances as list items.
    Useful for longer transcripts.

    Args:
        utterances: List of parsed utterances
        title: Optional document title (H1 header)
        include_timestamps: Whether to include timestamps (default: True)

    Returns:
        Formatted Markdown string in compact format

    Example:
        >>> utterances = [
        ...     Utterance("Alice", "00:00:10", "Hello everyone"),
        ...     Utterance("Bob", "00:00:15", "Hi Alice!"),
        ... ]
        >>> print(format_compact(utterances))
        - **Alice** (00:00:10): Hello everyone
        - **Bob** (00:00:15): Hi Alice!
    """
    if not utterances:
        return _generate_empty_document(title)

    lines: list[str] = []

    # Add title if provided
    if title:
        lines.append(f"# {title}")
        lines.append("")

    # Format each utterance as a list item
    for utterance in utterances:
        if include_timestamps:
            lines.append(
                f"- **{utterance.speaker}** ({utterance.timestamp}): {utterance.text}"
            )
        else:
            lines.append(f"- **{utterance.speaker}**: {utterance.text}")

    lines.append("")
    return "\n".join(lines)


def _generate_empty_document(title: str | None = None) -> str:
    """Generate an empty transcript document.

    Args:
        title: Optional document title

    Returns:
        Markdown string indicating empty transcript
    """
    lines: list[str] = []

    if title:
        lines.append(f"# {title}")
        lines.append("")

    lines.append("*No transcript content found.*")
    lines.append("")

    return "\n".join(lines)
