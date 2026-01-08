"""CLI entry point for Teams Transcript Tool.

Provides the command-line interface for converting transcripts
and optionally pushing to GitHub.
"""

import sys
from pathlib import Path

import click

from .formatter import format_markdown
from .github import check_gh_installed, push_to_repo
from .parser import parse_transcript


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (default: stdout or derived from input)",
)
@click.option(
    "--repo",
    "-r",
    help="GitHub repo to push to (owner/repo format)",
)
@click.option(
    "--branch",
    "-b",
    default="main",
    help="Target branch for GitHub push (default: main)",
)
@click.option(
    "--path",
    "-p",
    help="Path in repo for file (default: derived from input filename)",
)
@click.option(
    "--title",
    "-t",
    help="Document title (H1 header in output)",
)
@click.option(
    "--no-timestamps",
    is_flag=True,
    help="Omit timestamps from output",
)
@click.option(
    "--message",
    "-m",
    help="Commit message for GitHub push",
)
@click.version_option(package_name="teams-transcript")
def convert(
    input_file: Path,
    output: Path | None,
    repo: str | None,
    branch: str,
    path: str | None,
    title: str | None,
    no_timestamps: bool,
    message: str | None,
) -> None:
    """Convert Teams transcript to Markdown.

    Supports VTT and DOCX transcript formats from Microsoft Teams.

    Examples:

        # Convert to stdout
        teams-transcript meeting.vtt

        # Convert to file
        teams-transcript meeting.vtt -o meeting.md

        # Convert and push to GitHub
        teams-transcript meeting.vtt --repo myorg/notes --path transcripts/meeting.md

        # With custom title and no timestamps
        teams-transcript meeting.docx -t "Team Standup" --no-timestamps -o standup.md
    """
    try:
        # Parse the transcript
        click.echo(f"Parsing {input_file}...", err=True)
        utterances = parse_transcript(input_file)
        click.echo(f"Found {len(utterances)} utterances", err=True)

        # Generate title from filename if not provided
        if title is None:
            title = input_file.stem.replace("-", " ").replace("_", " ").title()

        # Format to Markdown
        markdown = format_markdown(
            utterances,
            title=title,
            include_timestamps=not no_timestamps,
        )

        # Determine output destination
        if repo:
            # Push to GitHub
            _handle_github_push(
                markdown=markdown,
                repo=repo,
                branch=branch,
                path=path,
                input_file=input_file,
                message=message,
            )
        elif output:
            # Write to file
            output.write_text(markdown, encoding="utf-8")
            click.echo(f"Written to {output}", err=True)
        else:
            # Write to stdout
            click.echo(markdown)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _handle_github_push(
    markdown: str,
    repo: str,
    branch: str,
    path: str | None,
    input_file: Path,
    message: str | None,
) -> None:
    """Handle pushing content to GitHub.

    Args:
        markdown: Formatted markdown content
        repo: Repository in "owner/repo" format
        branch: Target branch
        path: Destination path in repo (optional)
        input_file: Original input file (for deriving path)
        message: Commit message (optional)
    """
    # Check gh CLI first
    if not check_gh_installed():
        raise RuntimeError(
            "GitHub CLI (gh) is not installed or not authenticated.\n"
            "Install from https://cli.github.com/ and run 'gh auth login'"
        )

    # Derive path from input filename if not provided
    if path is None:
        path = f"transcripts/{input_file.stem}.md"

    click.echo(f"Pushing to {repo}:{branch}/{path}...", err=True)

    push_to_repo(
        content=markdown,
        repo=repo,
        path=path,
        branch=branch,
        message=message,
    )

    click.echo(f"Successfully pushed to https://github.com/{repo}/blob/{branch}/{path}", err=True)


def main() -> None:
    """Main entry point."""
    convert()


if __name__ == "__main__":
    main()
