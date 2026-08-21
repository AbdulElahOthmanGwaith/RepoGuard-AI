import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core_system"

_spec = importlib.util.spec_from_file_location("code_analyzer", CORE / "code-analyzer.py")
_code_analyzer = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_code_analyzer)
CodeIssue = _code_analyzer.CodeIssue
IssueType = _code_analyzer.IssueType
ScanResult = _code_analyzer.ScanResult
Severity = _code_analyzer.Severity


def test_sarif_schema_and_severity_mapping():
    result = ScanResult(
        issues=[
            CodeIssue(
                file="src/example.py",
                line=4,
                column=1,
                severity=Severity.HIGH,
                issue_type=IssueType.SECURITY_VULNERABILITY,
                message="Unsafe operation",
                rule_id="security/unsafe-operation",
            ),
            CodeIssue(
                file="src/example.py",
                line=9,
                column=0,
                severity=Severity.INFO,
                issue_type=IssueType.CODE_SMELL,
                message="Informational finding",
            ),
        ]
    )

    sarif = result.to_sarif()
    assert sarif["version"] == "2.1.0"
    run = sarif["runs"][0]
    assert run["tool"]["driver"]["name"] == "RepoGuard-AI"
    assert [item["level"] for item in run["results"]] == ["error", "note"]
    assert run["results"][0]["locations"][0]["physicalLocation"]["region"] == {
        "startLine": 4,
        "startColumn": 2,
    }
    assert len(run["tool"]["driver"]["rules"]) == 2


def test_cli_writes_sarif_file(tmp_path):
    output = tmp_path / "results.sarif.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(CORE / "code-analyzer.py"),
            "--project-root",
            str(tmp_path),
            "--format",
            "sarif",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["version"] == "2.1.0"
    assert payload["runs"][0]["results"] == []
