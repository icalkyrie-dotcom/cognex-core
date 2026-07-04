import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent / "context"

PROFILE_FILES = [
    "profile/identity.md",
    "profile/goals.md",
    "profile/preferences.md",
    "profile/personality.md",
    "profile/projects.md",
]

PROMPT_FILES = [
    "prompts/system.md",
    "prompts/response_style.md",
    "prompts/advisor.md",
]


def _read(relative_path: str) -> str:
    path = BASE_DIR / relative_path
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


def _read_capabilities() -> dict:
    path = BASE_DIR / "config/capabilities.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def build_context(memories: list = None) -> str:
    sections = []

    # Load prompts (system rules)
    for f in PROMPT_FILES:
        content = _read(f)
        if content:
            sections.append(content)

    # Load profile
    profile_parts = []
    for f in PROFILE_FILES:
        content = _read(f)
        if content:
            profile_parts.append(content)

    if profile_parts:
        sections.append("---\n# User Profile\n\n" + "\n\n---\n\n".join(profile_parts))

    # Load capabilities
    caps = _read_capabilities()
    if caps:
        active = [k for k, v in caps.items() if v]
        inactive = [k for k, v in caps.items() if not v]
        caps_text = "# Current Capabilities\n"
        if active:
            caps_text += "Available: " + ", ".join(active) + "\n"
        if inactive:
            caps_text += "Not available: " + ", ".join(inactive)
        sections.append(caps_text)

    # Load memories
    if memories:
        mem_text = "# Memory\n" + "\n".join(
            [f"- {m.key}: {m.value}" for m in memories]
        )
        sections.append(mem_text)

    return "\n\n---\n\n".join(sections)