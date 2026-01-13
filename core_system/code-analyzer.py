#!/usr/bin/env python3
"""
Auto-Guardian: Smart Code Analyzer
===================================
This script analyzes code to detect various issues
"""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class Severity(Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueType(Enum):
    """Types of issues"""
    SYNTAX_ERROR = "syntax_error"
    LINTING_ERROR = "linting_error"
    SECURITY_VULNERABILITY = "security_vulnerability"
    CODE_SMELL = "code_smell"
    DEPRECATED_USAGE = "deprecated_usage"
    PERFORMANCE_ISSUE = "performance_issue"
    STYLE_VIOLATION = "style_violation"
    TYPE_ERROR = "type_error"
    UNUSED_CODE = "unused_code"
    IMPORT_ERROR = "import_error"


@dataclass
class CodeIssue:
    """Representation of a code issue"""
    file: str
    line: int
    column: int
    severity: Severity
    issue_type: IssueType
    message: str
    rule_id: Optional[str] = None
    suggestion: Optional[str] = None
    fixable: bool = False
    
    def to_dict(self) -> dict:
        """Convert issue to dictionary"""
        return {
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "severity": self.severity.value,
            "type": self.issue_type.value,
            "message": self.message,
            "rule_id": self.rule_id,
            "suggestion": self.suggestion,
            "fixable": self.fixable
        }


@dataclass
class ScanResult:
    """Complete scan result"""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    files_scanned: int = 0
    issues_found: int = 0
    issues_by_severity: dict = field(default_factory=dict)
    issues_by_type: dict = field(default_factory=dict)
    critical_issues: list = field(default_factory=list)
    auto_fixable_issues: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert result to dictionary"""
        return {
            "timestamp": self.timestamp,
            "summary": {
                "files_scanned": self.files_scanned,
                "total_issues": self.issues_found,
                "by_severity": self.issues_by_severity,
                "by_type": self.issues_by_type,
                "critical_count": len(self.critical_issues),
                "auto_fixable_count": len(self.auto_fixable_issues)
            },
            "critical_issues": [i.to_dict() for i in self.critical_issues],
            "auto_fixable_issues": [i.to_dict() for i in self.auto_fixable_issues],
            "all_issues": [i.to_dict() for i in self.issues]
        }


class CodeAnalyzer:
    """Main code analyzer"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.issues: list[CodeIssue] = []
        self.result = ScanResult()
    
    def scan_python(self) -> list[CodeIssue]:
        """Scan Python files"""
        issues = []
        
        # Find Python files
        py_files = list(self.project_root.rglob("*.py"))
        self.result.files_scanned += len(py_files)
        
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    # Check common formatting errors
                    if re.search(r'print\s*\([^)]*\)', line):
                        issues.append(CodeIssue(
                            file=str(py_file),
                            line=line_num,
                            column=line.find('print'),
                            severity=Severity.LOW,
                            issue_type=IssueType.CODE_SMELL,
                            message="print() usage for debugging",
                            suggestion="Use logger instead of print",
                            fixable=True
                        ))
                    
                    # Check unused variables
                    if re.match(r'^\s*_+\w*$', line.strip()):
                        issues.append(CodeIssue(
                            file=str(py_file),
                            line=line_num,
                            column=0,
                            severity=Severity.INFO,
                            issue_type=IssueType.UNUSED_CODE,
                            message="Unused variable",
                            fixable=True
                        ))
                
                # Check syntax errors
                try:
                    import ast
                    ast.parse(content)
                except SyntaxError as e:
                    issues.append(CodeIssue(
                        file=str(py_file),
                        line=e.lineno or 1,
                        column=e.offset or 0,
                        severity=Severity.CRITICAL,
                        issue_type=IssueType.SYNTAX_ERROR,
                        message=f"Syntax error: {e.msg}",
                        suggestion="Review syntax on this line",
                        fixable=False
                    ))
                
                # Check security vulnerabilities
                security_patterns = [
                    (r"os\.environ\[['\"]\w+['\"]\]", "Direct environment variable access", Severity.HIGH, True),
                    (r"eval\s*\(", "Unsafe eval() usage", Severity.CRITICAL, False),
                    (r"exec\s*\(", "Unsafe exec() usage", Severity.CRITICAL, False),
                    (r"pickle\.load", "pickle.load may be unsafe", Severity.MEDIUM, True),
                    (r"yaml\.load", "yaml.load without SafeLoader", Severity.HIGH, True),
                    (r"password\s*=", "Password in code", Severity.HIGH, False),
                    (r"secret\s*=", "Secret key in code", Severity.HIGH, False),
                    (r"api[_-]?key\s*=", "API key in code", Severity.HIGH, False),
                ]
                
                for pattern, desc, severity, fixable in security_patterns:
                    if re.search(pattern, content):
                        line_num = self._find_line_with_pattern(lines, pattern)
                        issues.append(CodeIssue(
                            file=str(py_file),
                            line=line_num,
                            column=0,
                            severity=severity,
                            issue_type=IssueType.SECURITY_VULNERABILITY,
                            message=f"Security: {desc}",
                            suggestion="Move to .env file",
                            fixable=fixable
                        ))
                
            except Exception as e:
                print(f"Error reading {py_file}: {e}")
        
        return issues
    
    def scan_javascript(self) -> list[CodeIssue]:
        """Scan JavaScript files"""
        issues = []
        js_files = list(self.project_root.rglob("*.js")) + list(self.project_root.rglob("*.ts"))
        
        for js_file in js_files:
            try:
                content = js_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                # Check == instead of ===
                for line_num, line in enumerate(lines, 1):
                    if re.search(r'[^=!]==[^=]', line):
                        issues.append(CodeIssue(
                            file=str(js_file),
                            line=line_num,
                            column=line.find('=='),
                            severity=Severity.MEDIUM,
                            issue_type=IssueType.CODE_SMELL,
                            message="Use === instead of ==",
                            suggestion="Use === for strict comparison",
                            fixable=True
                        ))
                    
                    # Check var instead of let/const
                    if re.search(r'\bvar\s+\w+', line):
                        issues.append(CodeIssue(
                            file=str(js_file),
                            line=line_num,
                            column=line.find('var'),
                            severity=Severity.LOW,
                            issue_type=IssueType.DEPRECATED_USAGE,
                            message="Use let/const instead of var",
                            suggestion="Use let or const",
                            fixable=True
                        ))
                    
                    # Check console.log
                    if re.search(r'console\.(log|debug|info)', line):
                        issues.append(CodeIssue(
                            file=str(js_file),
                            line=line_num,
                            column=line.find('console'),
                            severity=Severity.INFO,
                            issue_type=IssueType.CODE_SMELL,
                            message="Remaining console.log statement",
                            suggestion="Remove or use logger",
                            fixable=True
                        ))
                
            except Exception as e:
                print(f"Error reading {js_file}: {e}")
        
        return issues
    
    def _find_line_with_pattern(self, lines: list[str], pattern: str) -> int:
        """Find line containing pattern"""
        for line_num, line in enumerate(lines, 1):
            if re.search(pattern, line):
                return line_num
        return 1
    
    def run_linters(self) -> list[CodeIssue]:
        """Run external linting tools"""
        issues = []
        
        # Run Flake8 for Python
        try:
            result = subprocess.run(
                ['flake8', '.', '--format=json', '--max-line-length=100'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode != 0:
                data = json.loads(result.stdout) if result.stdout else []
                for item in data:
                    issues.append(CodeIssue(
                        file=item['filename'],
                        line=item['line_number'],
                        column=item['column_number'],
                        severity=self._map_flake8_severity(item['type']),
                        issue_type=IssueType.LINTING_ERROR,
                        message=item['text'],
                        rule_id=item['id'],
                        fixable=True
                    ))
        except Exception as e:
            print(f"Flake8 not available: {e}")
        
        # Run ESLint if available
        try:
            result = subprocess.run(
                ['npx', 'eslint', '.', '--format=json'],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=60
            )
            if result.returncode != 0:
                data = json.loads(result.stdout) if result.stdout else []
                for item in data:
                    for msg in item.get('messages', []):
                        issues.append(CodeIssue(
                            file=item['filePath'],
                            line=msg['line'],
                            column=msg['column'],
                            severity=self._map_eslint_severity(msg['severity']),
                            issue_type=IssueType.LINTING_ERROR,
                            message=msg['message'],
                            rule_id=msg['ruleId'],
                            fixable=msg.get('fix') is not None
                        ))
        except Exception as e:
            print(f"ESLint not available: {e}")
        
        return issues
    
    def _map_flake8_severity(self, code: str) -> Severity:
        """Map severity from Flake8 code"""
        prefix = code[0] if code else 'W'
        if prefix == 'E':
            return Severity.HIGH
        elif prefix == 'F':
            return Severity.CRITICAL
        elif prefix == 'W':
            return Severity.LOW
        return Severity.MEDIUM
    
    def _map_eslint_severity(self, severity: int) -> Severity:
        """Map severity from ESLint"""
        if severity == 2:
            return Severity.HIGH
        elif severity == 1:
            return Severity.MEDIUM
        return Severity.LOW
    
    def analyze(self) -> ScanResult:
        """Run complete analysis"""
        print("Starting code analysis...")
        
        # Collect issues from all sources
        python_issues = self.scan_python()
        js_issues = self.scan_javascript()
        linter_issues = self.run_linters()
        
        self.issues = python_issues + js_issues + linter_issues
        self.result.issues = self.issues
        self.result.issues_found = len(self.issues)
        
        # Categorize issues
        for issue in self.issues:
            # By severity
            severity_key = issue.severity.value
            self.result.issues_by_severity[severity_key] = \
                self.result.issues_by_severity.get(severity_key, 0) + 1
            
            # By type
            type_key = issue.issue_type.value
            self.result.issues_by_type[type_key] = \
                self.result.issues_by_type.get(type_key, 0) + 1
            
            # Critical issues
            if issue.severity == Severity.CRITICAL:
                self.result.critical_issues.append(issue)
            
            # Auto-fixable issues
            if issue.fixable:
                self.result.auto_fixable_issues.append(issue)
        
        # Print summary
        print(f"   Files scanned: {self.result.files_scanned}")
        print(f"   Issues found: {self.result.issues_found}")
        print(f"   Critical issues: {len(self.result.critical_issues)}")
        print(f"   Auto-fixable issues: {len(self.result.auto_fixable_issues)}")
        
        return self.result


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto-Guardian Code Analyzer')
    parser.add_argument('--output', '-o', help='Output file', default='scan-results.json')
    parser.add_argument('--format', '-f', choices=['json', 'sarif'], default='json',
                        help='Output format')
    parser.add_argument('--project-root', '-p', help='Project directory')
    
    args = parser.parse_args()
    
    # Create analyzer and run it
    analyzer = CodeAnalyzer(args.project_root)
    result = analyzer.analyze()
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if args.format == 'json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"   Results saved to {output_path}")
    
    # Save critical issues file
    if result.critical_issues:
        critical_path = Path("critical-issues.json")
        with open(critical_path, 'w', encoding='utf-8') as f:
            json.dump([i.to_dict() for i in result.critical_issues], f, indent=2, ensure_ascii=False)
        print(f"   Critical issues saved to {critical_path}")
    
    # Return exit code based on critical issues
    sys.exit(1 if len(result.critical_issues) > 0 else 0)


if __name__ == '__main__':
    main()
