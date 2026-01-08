# Teams Transcript to Markdown - Design Document

## 1. Overview

### Purpose and Scope

A focused CLI tool that converts Microsoft Teams meeting transcripts into clean, readable markdown and pushes them to a GitHub repository. The tool bridges the gap between Teams' native transcript export formats and version-controlled documentation.

**In Scope:**
- Parse VTT (WebVTT) transcript files (Teams' primary export format)
- Parse DOCX transcript files (Teams' alternative export format)
- Convert to clean, well-formatted markdown
- Push to specified GitHub repository via gh CLI
- Support branch specification

**Out of Scope:**
- Video/audio file processing
- Real-time transcript capture
- Multiple transcript merging
- GUI interface

### Key Goals and Success Criteria

| Goal | Success Criteria |
|------|------------------|
| Simple CLI | Single command converts and pushes in one step |
| Clean output | Markdown is human-readable with clear speaker attribution |
| Reliable parsing | Handles Teams' actual export formats correctly |
| Git integration | Seamless push via existing gh CLI authentication |
| Minimal dependencies | Uses only essential libraries |

**Quality Bar:**
- A user can convert and push a transcript in under 30 seconds
- Output markdown is immediately useful without manual editing
- Tool fails clearly with actionable error messages

---

## 2. Architecture

### Component Breakdown

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI (main.py)                        │
│  - Argument parsing (Click)                                  │
│  - Orchestrates flow                                         │
│  - Error handling & user feedback                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  parser.py      │     │  github.py      │
│  - VTT parsing  │     │  - gh CLI wrap  │
│  - DOCX parsing │     │  - Commit/push  │
│  - Format detect│     │  - Branch ops   │
└────────┬────────┘     └─────────────────┘
         │                       ▲
         ▼                       │
┌─────────────────┐              │
│  formatter.py   │──────────────┘
│  - MD generation│
│  - Template     │
└─────────────────┘
```

**Four modules, each with a single responsibility:**

1. **main.py** - CLI entry point and orchestration
2. **parser.py** - Transcript file parsing (VTT/DOCX)
3. **formatter.py** - Markdown generation
4. **github.py** - GitHub repository operations

### Data Flow and Interactions

```
User Input                     Internal Data                      Output
───────────                    ─────────────                      ──────

transcript.vtt  ──┐
        or       ├──▶  Parser  ──▶  List[Utterance]  ──▶  Formatter  ──▶  markdown
transcript.docx ──┘                 │                                       │
                                    │                                       │
                     dataclass:     │                                       ▼
                     - speaker      │                              GitHub Push
                     - timestamp    │                                       │
                     - text         │                                       ▼
                                    │                              repo/transcript.md
```

**Core Data Structure:**

```python
@dataclass
class Utterance:
    speaker: str           # "John Doe"
    timestamp: str         # "00:01:23" 
    text: str              # "Hello everyone..."
```

### Integration Points

| Integration | Method | Notes |
|-------------|--------|-------|
| Teams VTT files | File read + regex parsing | Standard WebVTT with Teams extensions |
| Teams DOCX files | python-docx library | Structured table format |
| GitHub | gh CLI subprocess | Leverages existing user auth |
| File system | pathlib | Cross-platform paths |

---

## 3. File Structure

```
teams-transcript-tool/
├── DESIGN.md                    # This document
├── README.md                    # User documentation (create during impl)
├── pyproject.toml               # Project config and dependencies
│
├── src/
│   └── teams_transcript/
│       ├── __init__.py          # Package init, version
│       ├── main.py              # CLI entry point
│       ├── parser.py            # VTT/DOCX parsing
│       ├── formatter.py         # Markdown generation
│       └── github.py            # gh CLI integration
│
└── tests/
    ├── __init__.py
    ├── test_parser.py           # Parser unit tests
    ├── test_formatter.py        # Formatter unit tests
    ├── test_github.py           # GitHub module tests (mocked)
    └── fixtures/
        ├── sample.vtt           # Test VTT file
        └── sample.docx          # Test DOCX file
```

**File Purposes:**

| File | Purpose |
|------|---------|
| `main.py` | CLI commands, argument validation, flow orchestration |
| `parser.py` | File format detection, VTT parsing, DOCX parsing |
| `formatter.py` | Markdown template, utterance formatting |
| `github.py` | gh CLI wrapper, repo operations, branch handling |
| `pyproject.toml` | Dependencies, build config, CLI entrypoint |

---

## 4. Interfaces

### Public APIs and Contracts

#### CLI Interface

```bash
# Basic usage
teams-transcript convert <transcript-file> --repo <owner/repo>

# With options
teams-transcript convert meeting.vtt \
    --repo myorg/meeting-notes \
    --branch feature/q1-meetings \
    --output "2024-01-meeting.md" \
    --message "Add Q1 planning meeting transcript"
```

**Arguments:**

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `transcript-file` | Yes | - | Path to .vtt or .docx file |
| `--repo`, `-r` | Yes | - | Target GitHub repo (owner/repo) |
| `--branch`, `-b` | No | default branch | Target branch |
| `--output`, `-o` | No | `<filename>.md` | Output filename in repo |
| `--message`, `-m` | No | Auto-generated | Commit message |
| `--dry-run` | No | False | Preview without pushing |

#### Module Contracts

**parser.py:**
```python
def parse_transcript(file_path: Path) -> list[Utterance]:
    """
    Parse a Teams transcript file.
    
    Args:
        file_path: Path to .vtt or .docx transcript
        
    Returns:
        List of Utterance objects in chronological order
        
    Raises:
        TranscriptParseError: If file cannot be parsed
        UnsupportedFormatError: If file format not recognized
    """
```

**formatter.py:**
```python
def format_markdown(
    utterances: list[Utterance],
    title: str | None = None,
    include_timestamps: bool = True
) -> str:
    """
    Convert utterances to markdown.
    
    Args:
        utterances: Parsed transcript data
        title: Optional document title
        include_timestamps: Include timestamps in output
        
    Returns:
        Formatted markdown string
    """
```

**github.py:**
```python
def push_to_repo(
    content: str,
    repo: str,
    filename: str,
    branch: str | None = None,
    commit_message: str | None = None
) -> str:
    """
    Push content to GitHub repository.
    
    Args:
        content: File content to push
        repo: Repository in owner/repo format
        filename: Target filename in repo
        branch: Target branch (None = default)
        commit_message: Commit message
        
    Returns:
        URL of created/updated file
        
    Raises:
        GitHubAuthError: If gh CLI not authenticated
        GitHubRepoError: If repo not accessible
    """
```

### Configuration Options

**Environment Variables:**

| Variable | Purpose | Default |
|----------|---------|---------|
| `GITHUB_TOKEN` | Fallback auth if gh CLI unavailable | None |
| `TEAMS_TRANSCRIPT_BRANCH` | Default branch | repo default |

**No config file** - CLI arguments are sufficient for this tool's scope.

### Error Handling Strategy

**Error Hierarchy:**
```python
class TranscriptToolError(Exception):
    """Base exception for all tool errors."""

class TranscriptParseError(TranscriptToolError):
    """Failed to parse transcript file."""

class UnsupportedFormatError(TranscriptToolError):
    """File format not supported."""

class GitHubAuthError(TranscriptToolError):
    """GitHub authentication failed."""

class GitHubRepoError(TranscriptToolError):
    """Repository operation failed."""
```

**Error Messages - User-Friendly:**
```
Error: Could not parse 'meeting.txt'
       Supported formats: .vtt, .docx
       
Error: GitHub authentication required
       Run 'gh auth login' to authenticate
       
Error: Repository 'myorg/notes' not found or not accessible
       Check repository name and permissions
```

---

## 5. Implementation Plan

### Suggested Order

```
Phase 1: Core Foundation (Day 1)
├── 1.1 Project setup (pyproject.toml, structure)
├── 1.2 VTT parser implementation
└── 1.3 Markdown formatter

Phase 2: Full Pipeline (Day 1-2)
├── 2.1 DOCX parser implementation  
├── 2.2 CLI with Click
└── 2.3 Local dry-run working

Phase 3: GitHub Integration (Day 2)
├── 3.1 gh CLI wrapper
├── 3.2 Push functionality
└── 3.3 Branch support

Phase 4: Polish (Day 2-3)
├── 4.1 Error handling refinement
├── 4.2 Tests
└── 4.3 README documentation
```

### Dependencies Between Components

```
parser.py ──────────────┐
                        ├──▶ main.py (needs both)
formatter.py ───────────┘         │
                                  │
github.py ◀───────────────────────┘
(called after formatter produces markdown)
```

**Implementation can proceed in parallel:**
- Parser and Formatter have no dependencies
- GitHub module can be stubbed initially
- CLI orchestration comes last

### Testing Approach

**Test Pyramid:**
- 60% Unit tests (parser, formatter logic)
- 30% Integration tests (CLI end-to-end with mocked gh)
- 10% Manual validation (real Teams files, real repos)

**Unit Tests:**
```python
# test_parser.py
def test_parse_vtt_extracts_speakers():
    """Speaker names correctly extracted from VTT."""

def test_parse_vtt_handles_timestamps():
    """Timestamps preserved in correct format."""

def test_parse_docx_table_format():
    """DOCX table format parsed correctly."""

# test_formatter.py  
def test_format_groups_by_speaker():
    """Consecutive same-speaker entries grouped."""

def test_format_includes_timestamps():
    """Timestamps appear in expected format."""
```

**Integration Tests:**
```python
# test_cli.py
def test_convert_dry_run(tmp_path, sample_vtt):
    """Full pipeline with --dry-run produces expected markdown."""
```

**Test Fixtures:**
- Create minimal VTT file matching Teams format
- Create minimal DOCX file matching Teams format
- Mock gh CLI responses

---

## 6. Considerations

### Edge Cases

| Edge Case | Handling |
|-----------|----------|
| Empty transcript | Generate markdown with "No transcript content" note |
| Single speaker | Simplify format, skip speaker headers |
| Very long utterances | Preserve as-is, no truncation |
| Special characters in names | Escape for markdown |
| Non-English content | Pass through unchanged (UTF-8) |
| Missing timestamps | Use "??" placeholder, continue parsing |
| Malformed VTT | Best-effort parse, warn about skipped lines |
| File > 10MB | Process normally (text files should be fine) |
| Branch doesn't exist | Fail with clear error, suggest creating branch |
| Repo has no default branch | Fail with clear error |

### Performance

**Expected Performance:**
- Typical transcript (1hr meeting): < 1 second parse/format
- GitHub push: 2-5 seconds (network dependent)
- Total CLI execution: < 10 seconds

**No optimization needed** for expected use case (single files, infrequent runs).

### Security Considerations

| Concern | Mitigation |
|---------|------------|
| GitHub token exposure | Use gh CLI (handles auth securely) |
| Arbitrary file read | Validate file extension before parsing |
| Command injection | Use subprocess with list args, not shell=True |
| Sensitive transcript content | User responsibility; tool doesn't inspect content |
| Repo permissions | gh CLI enforces user's actual permissions |

**Security Best Practices in Code:**
```python
# Good: subprocess with list
subprocess.run(["gh", "api", endpoint], capture_output=True)

# Bad: shell string interpolation
subprocess.run(f"gh api {endpoint}", shell=True)  # NEVER
```

---

## Dependencies

**Runtime Dependencies:**
```toml
[project]
dependencies = [
    "click>=8.0",           # CLI framework
    "python-docx>=0.8",     # DOCX parsing
]
```

**Dev Dependencies:**
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov",
]
```

**System Requirements:**
- Python 3.10+
- gh CLI installed and authenticated

---

## Example Output

**Input (VTT snippet):**
```
WEBVTT

00:00:05.000 --> 00:00:08.000
<v John Doe>Hello everyone, let's get started.</v>

00:00:08.500 --> 00:00:12.000
<v Jane Smith>Thanks John. I have updates on the project.</v>
```

**Output (Markdown):**
```markdown
# Meeting Transcript

**Date:** 2024-01-15

---

## John Doe

**[00:00:05]** Hello everyone, let's get started.

## Jane Smith

**[00:00:08]** Thanks John. I have updates on the project.
```

---

## Success Metrics

Post-implementation, validate:

1. `teams-transcript convert sample.vtt --repo test/repo --dry-run` works
2. Output markdown is readable without editing
3. Real Teams transcript files parse correctly
4. Push to actual repo succeeds
5. Error messages are clear and actionable
