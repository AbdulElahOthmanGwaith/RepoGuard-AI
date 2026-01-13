#!/usr/bin/env python3
"""
Auto-Guardian: Report Generator
================================
Generate detailed reports about code quality and send appropriate notifications
"""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class ReportType(Enum):
    """Types of reports"""
    PULL_REQUEST = "pull_request"
    DAILY_SUMMARY = "daily_summary"
    SECURITY_ALERT = "security_alert"
    QUALITY_REPORT = "quality_report"


@dataclass
class ReportConfig:
    """Report configuration"""
    scan_results_file: str
    pr_number: Optional[int] = None
    report_type: ReportType = ReportType.PULL_REQUEST
    include_details: bool = True
    include_suggestions: bool = True


class ReportGenerator:
    """Report generator"""
    
    def __init__(self, config: ReportConfig):
        self.config = config
        self.results = self._load_results()
    
    def _load_results(self) -> dict:
        """Load scan results"""
        with open(self.config.scan_results_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_pull_request_comment(self) -> str:
        """Generate comment for Pull Request"""
        summary = self.results.get('summary', {})
        critical_issues = self.results.get('critical_issues', [])
        auto_fixable = self.results.get('auto_fixable_issues', [])
        all_issues = self.results.get('all_issues', [])
        
        # Severity emojis
        severity_emojis = {
            'critical': 'Critical',
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low',
            'info': 'Info'
        }
        
        report = []
        
        # Title
        report.append("## Quality Scan Report - Auto-Guardian")
        report.append("")
        report.append(f"**Scan Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Files Scanned:** {summary.get('files_scanned', 0)}")
        report.append(f"**Total Issues:** {summary.get('total_issues', 0)}")
        report.append("")
        
        # Summary by severity
        report.append("### Issues Summary")
        report.append("")
        report.append("| Severity | Count |")
        report.append("|----------|-------|")
        for severity, count in summary.get('by_severity', {}).items():
            emoji = severity_emojis.get(severity, 'Info')
            report.append(f"| {emoji} | {count} |")
        report.append("")
        
        # Auto-fix status
        if auto_fixable:
            report.append("### Auto-Fixes Applied")
            report.append("")
            report.append(f"**{len(auto_fixable)}** issues were fixed automatically:")
            report.append("")
            
            for issue in auto_fixable[:10]:  # Show first 10 only
                file_path = Path(issue['file']).name
                report.append(f"- Fixed `{file_path}`:{issue['line']} - {issue['message']}")
            
            if len(auto_fixable) > 10:
                report.append(f"- ... and **{len(auto_fixable) - 10}** more fixes")
            report.append("")
        
        # Issues requiring human intervention
        if critical_issues:
            report.append("### Issues Requiring Human Intervention")
            report.append("")
            report.append("**This code cannot be merged until these issues are resolved:**")
            report.append("")
            
            for issue in critical_issues:
                file_path = Path(issue['file']).name
                emoji = severity_emojis.get(issue['severity'], 'Critical')
                report.append(f"- **{emoji} {issue['file']}:{issue['line']}**")
                report.append(f"  - Issue: {issue['message']}")
                if issue.get('suggestion'):
                    report.append(f"  - Suggestion: {issue['suggestion']}")
                report.append("")
            
            report.append("---")
            report.append("### Merge Status: Blocked")
            report.append("")
            report.append("**This Pull Request is blocked from merging due to critical issues.**")
            report.append("")
            report.append("Please resolve the issues above and try again.")
        else:
            # No critical issues
            report.append("---")
            report.append("### Merge Status: Approved")
            report.append("")
            report.append("**This code passed all quality checks!**")
            report.append("")
            report.append("You can proceed with merging this Pull Request.")
        
        # Footer
        report.append("")
        report.append("---")
        report.append("*Report generated automatically by Auto-Guardian Bot*")
        
        return '\n'.join(report)
    
    def generate_daily_summary(self) -> dict:
        """Generate daily summary"""
        summary = self.results.get('summary', {})
        
        return {
            "date": datetime.now().isoformat(),
            "total_issues": summary.get('total_issues', 0),
            "critical_issues": summary.get('critical_count', 0),
            "auto_fixed": summary.get('auto_fixable_count', 0),
            "by_severity": summary.get('by_severity', {}),
            "by_type": summary.get('by_type', {})
        }
    
    def generate_security_alert(self) -> str:
        """Generate security alert"""
        critical = self.results.get('critical_issues', [])
        security_issues = [i for i in critical if 'security' in i.get('type', '')]
        
        if not security_issues:
            return None
        
        alert = []
        alert.append("Security Alert - Auto-Guardian")
        alert.append("")
        alert.append("Security vulnerabilities detected in code:")
        alert.append("")
        
        for issue in security_issues:
            alert.append(f"- {issue['file']}:{issue['line']}")
            alert.append(f"  {issue['message']}")
            if issue.get('suggestion'):
                alert.append(f"  Suggestion: {issue['suggestion']}")
        
        return '\n'.join(alert)
    
    def save_report(self, content: str, filename: str = "report.md") -> Path:
        """Save report to file"""
        output_path = Path(filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return output_path


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto-Guardian Report Generator')
    parser.add_argument('--scan-results', required=True, help='Scan results file')
    parser.add_argument('--pr-number', type=int, help='Pull Request number')
    parser.add_argument('--output', '-o', default="report.md", help='Output file')
    parser.add_argument('--format', choices=['comment', 'summary', 'json'], 
                        default='comment', help='Report format')
    
    args = parser.parse_args()
    
    config = ReportConfig(
        scan_results_file=args.scan_results,
        pr_number=args.pr_number,
        report_type=ReportType.PULL_REQUEST
    )
    
    generator = ReportGenerator(config)
    
    if args.format == 'comment':
        report = generator.generate_pull_request_comment()
    elif args.format == 'summary':
        report = json.dumps(generator.generate_daily_summary(), indent=2)
    else:
        report = generator.generate_pull_request_comment()
    
    # Print report
    print(report)
    
    # Save report
    generator.save_report(report, args.output)
    print(f"\nReport saved to {args.output}")


if __name__ == '__main__':
    main()
