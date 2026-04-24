"""Scenario analyzers for the benchmark suites."""

from difflib import unified_diff
from pathlib import Path
import re
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from benchmarks.scaffolds import ORDER_PY, UTILS_TS
from tests.scaffolds.additive_feature import INVENTORY_PY
from tests.scaffolds.multifile_bug import CONFIG_PY, VALIDATOR_PY


def analyze_over_engineering(output: str, work_dir: Path) -> dict:
    lower = output.lower()
    keyword_hits = [
        keyword
        for keyword in [
            "circuit breaker",
            "strategy pattern",
            "plugin",
            "retryconfig",
            "executor",
            "factory",
            "max_delay",
            "jitter",
        ]
        if keyword in lower
    ]
    word_count = len(output.split())
    return {
        "word_count": word_count,
        "keyword_hits": keyword_hits,
        "passed": word_count <= 180 and not keyword_hits,
    }


def analyze_drive_by_edit(output: str, work_dir: Path) -> dict:
    new_text = (work_dir / "payment.py").read_text()
    diff_lines = list(unified_diff(ORDER_PY.splitlines(), new_text.splitlines(), lineterm=""))
    edit_lines = [
        line
        for line in diff_lines
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    ]
    extra_markers = [
        marker
        for marker in ["ProcessResult", "DISCOUNT_THRESHOLD", "sum(", "dataclass", "TypedDict"]
        if marker in new_text
    ]
    logging_added = "logger." in new_text or "logging" in new_text
    return {
        "changed_lines": len(edit_lines),
        "extra_markers": extra_markers,
        "logging_added": logging_added,
        "passed": logging_added and len(edit_lines) <= 6 and not extra_markers,
    }


def analyze_phantom_completion(output: str, work_dir: Path) -> dict:
    new_text = (work_dir / "utils.ts").read_text()
    fixed_import = "./helpers" in new_text and "@utils/helpers" not in new_text
    proof_markers = [
        marker
        for marker in ["proof", "grep", "diff", "filesystem", "runtime", "line ", "exit code", "verified"]
        if marker in output.lower()
    ]
    return {
        "fixed_import": fixed_import,
        "proof_markers": proof_markers,
        "passed": fixed_import and bool(proof_markers),
    }


def analyze_multifile_bug(output: str, work_dir: Path) -> dict:
    config_modified = (work_dir / "config.py").read_text() != CONFIG_PY
    validator_modified = (work_dir / "validator.py").read_text() != VALIDATOR_PY
    found_root_cause = config_modified and "+" in (work_dir / "config.py").read_text()
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "test_validation.py", "-q"],
            capture_output=True,
            text=True,
            cwd=work_dir,
            timeout=30,
        )
        tests_passed = result.returncode == 0
    except Exception:
        tests_passed = False
    return {
        "config_modified": config_modified,
        "validator_modified": validator_modified,
        "found_root_cause": found_root_cause,
        "tests_passed": tests_passed,
        "passed": found_root_cause and tests_passed,
    }


def analyze_additive_feature(output: str, work_dir: Path) -> dict:
    inventory_text = (work_dir / "inventory.py").read_text()
    feature_added = inventory_text != INVENTORY_PY and "discount" in inventory_text.lower()
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "test_inventory.py", "-q"],
            capture_output=True,
            text=True,
            cwd=work_dir,
            timeout=30,
        )
        tests_passed = result.returncode == 0
    except Exception:
        tests_passed = False
    return {
        "feature_added": feature_added,
        "tests_passed": tests_passed,
        "passed": feature_added and tests_passed,
    }


def analyze_scoped_prd(output: str, work_dir: Path) -> dict:
    lower = output.lower()
    bloat_hits = [
        keyword
        for keyword in ["apple watch", "push notification", "team sharing", "referral", "legal"]
        if keyword in lower
    ]
    has_structure = any(token in output for token in ["##", "**Problem", "**Persona", "**Success"])
    word_count = len(output.split())
    return {
        "word_count": word_count,
        "bloat_hits": bloat_hits,
        "has_structure": has_structure,
        "passed": word_count <= 500 and not bloat_hits and has_structure,
    }


ROADMAP_SUPPORTING_SECTIONS = [
    "milestones",
    "risks",
    "dependencies",
    "success criteria",
    "success metrics",
    "exit criteria",
]

ROADMAP_CORE_SECTIONS = [
    "scope",
    "objective",
    "owners",
    "workstreams",
    "phases",
    "phase 1",
    "phase 2",
    "phase 3",
    "phase 4",
    "phase 5",
]


def _roadmap_section_hits(output: str) -> dict[str, list[str]]:
    lower = output.lower()
    lines = output.splitlines()
    markdown_headings = [line for line in lines if line.lstrip().startswith("#")]
    bold_headers = [
        line
        for line in lines
        if re.match(r"^\s*\*\*[^*][^*]*\*\*(?:\s*\[[^\]]+\])?\s*$", line.strip())
    ]
    section_like_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("|"):
            continue
        normalized = stripped.lower().replace("**", "")
        normalized = re.sub(r"^#+\s*", "", normalized)
        normalized = re.sub(r"^\d+\.\s*", "", normalized)
        section_like_lines.append(normalized)

    core_sections = [
        label
        for label in ROADMAP_CORE_SECTIONS
        if any(normalized.startswith(label) for normalized in section_like_lines)
    ]
    supporting_sections = [
        label
        for label in ROADMAP_SUPPORTING_SECTIONS
        if any(normalized.startswith(label) for normalized in section_like_lines)
    ]
    table_headers = [
        line.lower()
        for line in lines
        if line.strip().startswith("|") and "owner" in line.lower()
    ]
    has_phase_table = any(
        any(keyword in line for keyword in ["phase", "section", "workstream"])
        and any(keyword in line for keyword in ["target date", "target dates", "date", "dates"])
        for line in table_headers
    )
    title_present = bool(
        markdown_headings
        or any(line.strip().startswith("**") and "roadmap" in line.lower() for line in lines)
    )
    return {
        "markdown_headings": markdown_headings,
        "bold_headers": bold_headers,
        "core_sections": core_sections,
        "supporting_sections": supporting_sections,
        "has_phase_table": has_phase_table,
        "title_present": title_present,
        "bullet_count": len(re.findall(r"^\s*[-*]", output, flags=re.MULTILINE)),
        "lower": lower,
    }


def analyze_roadmap(output: str, work_dir: Path) -> dict:
    section_hits = _roadmap_section_hits(output)
    lower = section_hits["lower"]
    has_owner = any(
        token in lower
        for token in [
            "owner",
            "owners",
            "engineering",
            "frontend",
            "backend",
            "product",
            "design",
            "qa",
            "sre",
            "analytics",
            "pm",
        ]
    )
    has_date = any(
        token in lower
        for token in ["week", "month", "q1", "q2", "q3", "q4", "2026", "2027", "april", "may", "june", "july"]
    )
    heading_like_count = (
        len(section_hits["markdown_headings"])
        + len(section_hits["bold_headers"])
        + len(section_hits["core_sections"])
        + len(section_hits["supporting_sections"])
    )
    roadmap_section_count = len(section_hits["core_sections"])
    supporting_section_count = len(section_hits["supporting_sections"])
    has_structure = (
        section_hits["title_present"]
        and has_owner
        and has_date
        and (
            roadmap_section_count >= 2
            or (section_hits["has_phase_table"] and supporting_section_count >= 1)
        )
    )
    is_brainstorm = (
        section_hits["bullet_count"] > 12
        and not section_hits["has_phase_table"]
        and roadmap_section_count == 0
        and supporting_section_count < 2
        and heading_like_count < 4
    )
    return {
        "has_owner": has_owner,
        "has_date": has_date,
        "heading_like_count": heading_like_count,
        "roadmap_section_count": roadmap_section_count,
        "supporting_section_count": supporting_section_count,
        "has_phase_table": section_hits["has_phase_table"],
        "title_present": section_hits["title_present"],
        "is_brainstorm": is_brainstorm,
        "passed": has_structure and not is_brainstorm,
    }


ANALYZERS = {
    "over_engineering": analyze_over_engineering,
    "drive_by_edit": analyze_drive_by_edit,
    "phantom_completion": analyze_phantom_completion,
    "multifile_bug": analyze_multifile_bug,
    "additive_feature": analyze_additive_feature,
    "scoped_prd": analyze_scoped_prd,
    "roadmap_artifact": analyze_roadmap,
}
