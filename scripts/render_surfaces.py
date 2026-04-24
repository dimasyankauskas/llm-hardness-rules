#!/usr/bin/env python3
"""Render public prompt surfaces from the canonical core protocol."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CORE_PATH = ROOT / "protocols" / "core.md"


def read_text(path: Path) -> str:
    return path.read_text().strip() + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n")


def wrapped_surface(title: str, intro: str, body: str) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            "<!-- Generated from protocols/core.md by scripts/render_surfaces.py. -->",
            "",
            intro,
            "",
            body.strip(),
        ]
    )


def render_cursor(body: str) -> str:
    return "\n".join(
        [
            "---",
            "description: Hardness Protocol — portable core rules for deterministic AI agent execution",
            "alwaysApply: true",
            "---",
            "",
            "<!-- Generated from protocols/core.md by scripts/render_surfaces.py. -->",
            "",
            body.strip(),
        ]
    )


def render_skill(body: str) -> str:
    return "\n".join(
        [
            "---",
            "name: hardness-protocol",
            "description: >",
            "  Portable foundation rules for AI coding agents. Enforces AP-21, AP-22, AP-23,",
            "  simplicity-first execution, surgical changes, and concrete deliverables.",
            "license: MIT",
            "---",
            "",
            "<!-- Generated from protocols/core.md by scripts/render_surfaces.py. -->",
            "",
            body.strip(),
        ]
    )


def main() -> None:
    body = read_text(CORE_PATH)

    surfaces = {
        ROOT / "AGENTS.md": wrapped_surface(
            "AGENTS.md",
            "Codex-native Hardness Protocol. Keep the base contract small and use `profiles/` only when a task explicitly needs stricter process.",
            body,
        ),
        ROOT / "CLAUDE.md": wrapped_surface(
            "CLAUDE.md",
            "Claude Code version of the Hardness Protocol. This is the shared core, not the stricter profiles.",
            body,
        ),
        ROOT / "GEMINI.md": wrapped_surface(
            "GEMINI.md",
            "Gemini/Antigravity version of the Hardness Protocol. This is the shared core, not the stricter profiles.",
            body,
        ),
        ROOT / ".cursor" / "rules" / "hardness.mdc": render_cursor(body),
        ROOT / "skills" / "hardness-protocol" / "SKILL.md": render_skill(body),
    }

    for path, content in surfaces.items():
        write_text(path, content)
        print(f"rendered {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
