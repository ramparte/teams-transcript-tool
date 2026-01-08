"""GitHub operations module.

Handles pushing content to GitHub repositories via the gh CLI.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path


def check_gh_installed() -> bool:
    """Check if gh CLI is available and authenticated.

    Returns:
        True if gh is installed and authenticated, False otherwise

    Example:
        >>> if check_gh_installed():
        ...     print("Ready to push to GitHub")
    """
    # Check if gh is in PATH
    if shutil.which("gh") is None:
        return False

    # Check if authenticated
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def push_to_repo(
    content: str,
    repo: str,
    path: str,
    branch: str = "main",
    message: str | None = None,
) -> None:
    """Push content to GitHub repo via gh CLI.

    Uses the gh CLI to create or update a file in a GitHub repository.
    Requires gh to be installed and authenticated.

    Args:
        content: File content to push
        repo: Repository in "owner/repo" format
        path: Destination path within repo (e.g., "transcripts/meeting.md")
        branch: Target branch (default: "main")
        message: Commit message (auto-generated if None)

    Raises:
        RuntimeError: If gh CLI not installed or not authenticated
        subprocess.CalledProcessError: If push fails

    Example:
        >>> push_to_repo(
        ...     content="# Meeting Notes\\n...",
        ...     repo="myorg/notes",
        ...     path="transcripts/2024-01-15-standup.md",
        ...     branch="main",
        ...     message="Add standup transcript"
        ... )
    """
    # Validate gh CLI is ready
    if not check_gh_installed():
        raise RuntimeError(
            "GitHub CLI (gh) is not installed or not authenticated. "
            "Install from https://cli.github.com/ and run 'gh auth login'"
        )

    # Validate repo format
    if "/" not in repo or repo.count("/") != 1:
        raise ValueError(f"Invalid repo format: {repo}. Expected 'owner/repo'")

    # Generate commit message if not provided
    if message is None:
        filename = Path(path).name
        message = f"Add transcript: {filename}"

    # Write content to temp file for gh to read
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Use gh api to create/update file
        # First, try to get the file's SHA (needed for updates)
        sha = _get_file_sha(repo, path, branch)

        if sha:
            # Update existing file
            _update_file(repo, path, branch, content, message, sha)
        else:
            # Create new file
            _create_file(repo, path, branch, content, message)

    finally:
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)


def _get_file_sha(repo: str, path: str, branch: str) -> str | None:
    """Get the SHA of an existing file, or None if it doesn't exist.

    Args:
        repo: Repository in "owner/repo" format
        path: File path within repo
        branch: Branch name

    Returns:
        SHA string if file exists, None otherwise
    """
    try:
        result = subprocess.run(
            [
                "gh",
                "api",
                f"/repos/{repo}/contents/{path}",
                "-q",
                ".sha",
                "--jq",
                ".sha",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def _create_file(
    repo: str, path: str, branch: str, content: str, message: str
) -> None:
    """Create a new file in the repository.

    Args:
        repo: Repository in "owner/repo" format
        path: File path within repo
        branch: Branch name
        content: File content
        message: Commit message

    Raises:
        subprocess.CalledProcessError: If creation fails
    """
    import base64

    encoded_content = base64.b64encode(content.encode("utf-8")).decode("ascii")

    subprocess.run(
        [
            "gh",
            "api",
            "--method",
            "PUT",
            f"/repos/{repo}/contents/{path}",
            "-f",
            f"message={message}",
            "-f",
            f"content={encoded_content}",
            "-f",
            f"branch={branch}",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )


def _update_file(
    repo: str, path: str, branch: str, content: str, message: str, sha: str
) -> None:
    """Update an existing file in the repository.

    Args:
        repo: Repository in "owner/repo" format
        path: File path within repo
        branch: Branch name
        content: File content
        message: Commit message
        sha: Current file SHA

    Raises:
        subprocess.CalledProcessError: If update fails
    """
    import base64

    encoded_content = base64.b64encode(content.encode("utf-8")).decode("ascii")

    subprocess.run(
        [
            "gh",
            "api",
            "--method",
            "PUT",
            f"/repos/{repo}/contents/{path}",
            "-f",
            f"message={message}",
            "-f",
            f"content={encoded_content}",
            "-f",
            f"branch={branch}",
            "-f",
            f"sha={sha}",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
