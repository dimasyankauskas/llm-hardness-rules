from pathlib import Path

from benchmarks.analyzers import analyze_roadmap
from benchmarks.render_report import render_report


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "roadmap_artifact"


def roadmap_run(scenario: str, variant: str, passed: bool, timed_out: bool = False) -> dict:
    return {
        "scenario": scenario,
        "variant": variant,
        "analysis": {"passed": passed},
        "timed_out": timed_out,
    }


def test_roadmap_positive_fixtures_pass() -> None:
    for path in sorted(FIXTURE_DIR.glob("positive-*.md")):
        result = analyze_roadmap(path.read_text(), FIXTURE_DIR)
        assert result["passed"], f"{path.name} should pass but returned {result}"


def test_roadmap_negative_fixtures_fail() -> None:
    for path in sorted(FIXTURE_DIR.glob("negative-*.md")):
        result = analyze_roadmap(path.read_text(), FIXTURE_DIR)
        assert not result["passed"], f"{path.name} should fail but returned {result}"


def test_render_report_blocks_weak_roadmap_absolute_score() -> None:
    scenarios = [
        "over_engineering",
        "drive_by_edit",
        "phantom_completion",
        "multifile_bug",
        "additive_feature",
        "scoped_prd",
        "roadmap_artifact",
    ]
    core_runs = []
    interactive_runs = []
    for scenario in scenarios:
        bucket = interactive_runs if scenario in {"multifile_bug", "additive_feature", "scoped_prd", "roadmap_artifact"} else core_runs
        for _ in range(3):
            baseline_passed = False if scenario == "roadmap_artifact" else True
            hardness_passed = True
            if scenario == "roadmap_artifact":
                hardness_passed = _ == 0
            bucket.append(roadmap_run(scenario, "baseline", baseline_passed))
            bucket.append(roadmap_run(scenario, "hardness", hardness_passed))

    meta = {
        "agent": "codex",
        "agent_version": "codex-cli test",
        "timeout_seconds": 180,
        "runs_per_scenario": 3,
    }
    report = render_report(
        Path("core"),
        meta,
        core_runs,
        Path("interactive"),
        meta,
        interactive_runs,
    )
    assert "| roadmap_artifact | 0/3 | 1/3 | 0/3 | WIN | FAIL |" in report
    assert "- Gate status: `FAIL`" in report
