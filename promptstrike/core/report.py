"""
Report Generator - JSON, PDF, and HTML report generation
Reference: cid-roadmap-v1 Sprint S-1, Issue PS-2
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from jinja2 import Template

# ReportLab imports moved to PDF generation method to avoid startup issues
REPORTLAB_AVAILABLE = True

from ..models.scan_result import ScanResult, AttackResult, SeverityLevel


class ReportGenerator:
    """
    Generate security scan reports in multiple formats
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_json(self, scan_result: ScanResult) -> Path:
        """Generate JSON report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"promptstrike_scan_{timestamp}.json"
        output_path = self.output_dir / filename
        
        # Convert to dictionary for JSON serialization
        report_data = {
            "scan_id": scan_result.scan_id,
            "target": scan_result.target,
            "attack_pack": scan_result.attack_pack,
            "start_time": scan_result.start_time.isoformat(),
            "end_time": scan_result.end_time.isoformat(),
            "duration_seconds": scan_result.duration_seconds,
            "overall_risk_score": scan_result.overall_risk_score,
            "security_posture": scan_result.security_posture,
            "vulnerability_count": scan_result.vulnerability_count,
            "results": [self._attack_result_to_dict(result) for result in scan_result.results],
            "metadata": {
                "max_requests": scan_result.metadata.max_requests,
                "timeout_seconds": scan_result.metadata.timeout_seconds,
                "attack_pack_version": scan_result.metadata.attack_pack_version,
                "total_attacks": scan_result.metadata.total_attacks,
                "successful_attacks": scan_result.metadata.successful_attacks,
                "failed_attacks": scan_result.metadata.failed_attacks,
                "vulnerabilities_found": scan_result.metadata.vulnerabilities_found,
                "total_duration_seconds": scan_result.metadata.total_duration_seconds,
                "avg_response_time_ms": scan_result.metadata.avg_response_time_ms,
                "total_tokens_used": scan_result.metadata.total_tokens_used,
                "total_cost_usd": scan_result.metadata.total_cost_usd,
                "cli_version": scan_result.metadata.cli_version,
                "python_version": scan_result.metadata.python_version,
                "platform": scan_result.metadata.platform
            },
            "compliance": {
                "nist_rmf_controls_tested": scan_result.compliance.nist_rmf_controls_tested,
                "nist_rmf_gaps_identified": scan_result.compliance.nist_rmf_gaps_identified,
                "eu_ai_act_risk_category": scan_result.compliance.eu_ai_act_risk_category,
                "eu_ai_act_articles_relevant": scan_result.compliance.eu_ai_act_articles_relevant,
                "soc2_controls_impact": scan_result.compliance.soc2_controls_impact,
                "evidence_artifacts": scan_result.compliance.evidence_artifacts,
                "audit_hash": scan_result.compliance.audit_hash
            },
            "immediate_actions": scan_result.immediate_actions,
            "recommended_controls": scan_result.recommended_controls,
            "generated_by": "PromptStrike CLI v0.1.0",
            "generated_at": datetime.now().isoformat()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        return output_path
    
    def generate_html(self, scan_result: ScanResult) -> Path:
        """Generate HTML report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"promptstrike_scan_{timestamp}.html"
        output_path = self.output_dir / filename
        
        template = self._get_html_template()
        
        # Prepare data for template
        vulnerabilities_by_severity = self._group_by_severity(scan_result.results)
        
        html_content = template.render(
            scan_result=scan_result,
            vulnerabilities_by_severity=vulnerabilities_by_severity,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            severity_colors=self._get_severity_colors()
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return output_path
    
    def generate_pdf(self, scan_result: ScanResult) -> Path:
        """Generate PDF report using ReportLab"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"promptstrike_scan_{timestamp}.pdf"
        output_path = self.output_dir / filename
        
        # Try to import ReportLab only when needed
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        except (ImportError, Exception) as e:
            # Fallback to text file if ReportLab not available or fails
            return self._generate_text_fallback_pdf(scan_result, output_path)
        
        # Create PDF document
        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Title page with logo placeholder
        story.append(Paragraph("🎯 PromptStrike Security Scan Report", title_style))
        story.append(Paragraph("Enterprise LLM Security Assessment", styles['Heading3']))
        story.append(Spacer(1, 0.3*inch))
        
        # Executive summary table
        summary_data = [
            ['Target', scan_result.target],
            ['Scan ID', scan_result.scan_id],
            ['Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Duration', f"{scan_result.duration_seconds:.1f} seconds"],
            ['Risk Score', f"{scan_result.overall_risk_score}/10"],
            ['Security Posture', scan_result.security_posture.upper()],
            ['Vulnerabilities Found', str(scan_result.vulnerability_count)],
            ['Total Attacks', str(len(scan_result.results))]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Vulnerabilities by severity
        story.append(Paragraph("Vulnerability Summary", heading_style))
        
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        for result in scan_result.results:
            if result.is_vulnerable:
                severity_counts[result.severity.value] += 1
        
        severity_data = [['Severity', 'Count', 'Risk Level']]
        severity_colors_map = {
            'critical': colors.red,
            'high': colors.orange, 
            'medium': colors.yellow,
            'low': colors.lightgreen,
            'info': colors.lightgrey
        }
        
        for severity, count in severity_counts.items():
            if count > 0:
                severity_data.append([severity.title(), str(count), self._get_risk_description(severity)])
        
        if len(severity_data) > 1:
            severity_table = Table(severity_data, colWidths=[1.5*inch, 1*inch, 2.5*inch])
            severity_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(severity_table)
        else:
            story.append(Paragraph("No vulnerabilities detected.", styles['Normal']))
        
        story.append(PageBreak())
        
        # Detailed findings
        if scan_result.vulnerability_count > 0:
            story.append(Paragraph("🚨 Detailed Vulnerability Findings", heading_style))
            
            # Create vulnerability table for better presentation
            vuln_data = [['Attack ID', 'Category', 'Severity', 'Risk Score', 'Description']]
            
            for result in scan_result.results:
                if result.is_vulnerable:
                    vuln_data.append([
                        result.attack_id,
                        result.category.value.replace('_', ' ').title(),
                        result.severity.value.upper(),
                        f"{result.risk_score:.1f}/10",
                        result.description[:50] + "..." if len(result.description) > 50 else result.description
                    ])
            
            if len(vuln_data) > 1:
                vuln_table = Table(vuln_data, colWidths=[1*inch, 1.5*inch, 1*inch, 1*inch, 2*inch])
                vuln_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white])
                ]))
                story.append(vuln_table)
        
        # Compliance section
        story.append(PageBreak())
        story.append(Paragraph("Compliance & Recommendations", heading_style))
        
        # NIST controls
        if scan_result.compliance.nist_rmf_controls_tested:
            story.append(Paragraph("NIST AI-RMF Controls Tested:", styles['Heading3']))
            nist_text = ", ".join(scan_result.compliance.nist_rmf_controls_tested)
            story.append(Paragraph(nist_text, styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # EU AI Act
        if scan_result.compliance.eu_ai_act_articles_relevant:
            story.append(Paragraph("EU AI Act Articles:", styles['Heading3']))
            eu_text = ", ".join(scan_result.compliance.eu_ai_act_articles_relevant)
            story.append(Paragraph(eu_text, styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Immediate actions
        if scan_result.immediate_actions:
            story.append(Paragraph("Immediate Actions Required:", styles['Heading3']))
            for action in scan_result.immediate_actions:
                story.append(Paragraph(f"• {action}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        footer_text = f"Generated by PromptStrike CLI v0.1.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        return output_path
    
    def _generate_text_fallback_pdf(self, scan_result: ScanResult, output_path: Path) -> Path:
        """Fallback text-based PDF when ReportLab is not available"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("PROMPTSTRIKE SECURITY SCAN REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Target: {scan_result.target}\n")
            f.write(f"Risk Score: {scan_result.overall_risk_score}/10\n")
            f.write(f"Security Posture: {scan_result.security_posture.upper()}\n")
            f.write(f"Vulnerabilities Found: {scan_result.vulnerability_count}\n\n")
            f.write("NOTE: ReportLab not installed. Install with: pip install reportlab\n")
        return output_path
    
    def _create_vulnerability_section(self, result: AttackResult, styles):
        """Create a vulnerability section for the PDF"""
        # Import Paragraph locally to avoid import issues
        try:
            from reportlab.platypus import Paragraph
            from reportlab.lib.utils import simpleSplit
            
            # Create clean text content without HTML tags to avoid parsing issues
            content_lines = [
                f"Attack ID: {result.attack_id}",
                f"Category: {result.category.value.replace('_', ' ').title()}",
                f"Severity: {result.severity.value.upper()}",
                f"Risk Score: {result.risk_score}/10",
                f"Confidence: {result.confidence_score:.2f}",
                f"Description: {result.description}",
                f"Evidence: {result.evidence or 'N/A'}"
            ]
            
            # Join with line breaks
            content = "<br/>".join(content_lines)
            
            return Paragraph(content, styles['Normal'])
        except ImportError:
            # Fallback to simple string
            return f"Attack ID: {result.attack_id} | Severity: {result.severity.value.upper()}"
    
    def _get_risk_description(self, severity: str) -> str:
        """Get risk description for severity level"""
        descriptions = {
            'critical': 'Immediate action required',
            'high': 'High priority remediation',
            'medium': 'Medium priority review',
            'low': 'Low priority monitoring',
            'info': 'Informational only'
        }
        return descriptions.get(severity, 'Unknown')
    
    def _attack_result_to_dict(self, result: AttackResult) -> Dict[str, Any]:
        """Convert AttackResult to dictionary"""
        return {
            "attack_id": result.attack_id,
            "category": result.category.value,
            "severity": result.severity.value,
            "description": result.description,
            "prompt_used": result.prompt_used,
            "response_received": result.response_received,
            "is_vulnerable": result.is_vulnerable,
            "confidence_score": result.confidence_score,
            "risk_score": result.risk_score,
            "evidence": result.evidence,
            "attack_vector": result.attack_vector,
            "response_time_ms": result.response_time_ms,
            "tokens_used": result.tokens_used,
            "cost_usd": result.cost_usd,
            "nist_controls": result.nist_controls,
            "eu_ai_act_refs": result.eu_ai_act_refs,
            "timestamp": result.timestamp.isoformat()
        }
    
    def _group_by_severity(self, results: List[AttackResult]) -> Dict[str, List[AttackResult]]:
        """Group attack results by severity level"""
        grouped = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": []
        }
        
        for result in results:
            if result.is_vulnerable:
                grouped[result.severity.value].append(result)
        
        return grouped
    
    def _get_severity_colors(self) -> Dict[str, str]:
        """Get color codes for severity levels"""
        return {
            "critical": "#dc3545",  # Red
            "high": "#fd7e14",      # Orange
            "medium": "#ffc107",    # Yellow
            "low": "#20c997",       # Teal
            "info": "#6c757d"       # Gray
        }
    
    def _get_html_template(self) -> Template:
        """Get HTML report template"""
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PromptStrike Security Scan Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }
        .header h1 { margin: 0; font-size: 2.5rem; }
        .header .subtitle { opacity: 0.9; margin-top: 10px; }
        .content { padding: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .summary-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }
        .summary-card h3 { margin: 0 0 10px 0; color: #495057; }
        .summary-card .value { font-size: 2rem; font-weight: bold; color: #212529; }
        .risk-score { font-size: 3rem !important; }
        .risk-critical { color: #dc3545; }
        .risk-high { color: #fd7e14; }
        .risk-medium { color: #ffc107; }
        .risk-low { color: #28a745; }
        .vulnerability { background: #fff; border: 1px solid #dee2e6; border-radius: 8px; margin-bottom: 20px; overflow: hidden; }
        .vulnerability-header { padding: 15px 20px; font-weight: bold; color: white; }
        .vulnerability-body { padding: 20px; }
        .vulnerability-critical { background: #dc3545; }
        .vulnerability-high { background: #fd7e14; }
        .vulnerability-medium { background: #ffc107; color: #212529; }
        .vulnerability-low { background: #28a745; }
        .vulnerability-info { background: #17a2b8; }
        .code-block { background: #f8f9fa; border-radius: 4px; padding: 15px; margin: 10px 0; font-family: 'Monaco', 'Consolas', monospace; font-size: 0.9rem; overflow-x: auto; }
        .compliance-section { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 30px; }
        .footer { text-align: center; padding: 20px; color: #6c757d; border-top: 1px solid #dee2e6; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 PromptStrike Security Report</h1>
            <div class="subtitle">
                Target: {{ scan_result.target }} | Generated: {{ generated_at }}
            </div>
        </div>
        
        <div class="content">
            <div class="summary">
                <div class="summary-card">
                    <h3>Overall Risk Score</h3>
                    <div class="value risk-score {% if scan_result.overall_risk_score >= 8 %}risk-critical{% elif scan_result.overall_risk_score >= 6 %}risk-high{% elif scan_result.overall_risk_score >= 4 %}risk-medium{% else %}risk-low{% endif %}">
                        {{ "%.1f"|format(scan_result.overall_risk_score) }}/10
                    </div>
                </div>
                <div class="summary-card">
                    <h3>Security Posture</h3>
                    <div class="value">{{ scan_result.security_posture.title() }}</div>
                </div>
                <div class="summary-card">
                    <h3>Vulnerabilities Found</h3>
                    <div class="value">{{ scan_result.vulnerability_count }}</div>
                </div>
                <div class="summary-card">
                    <h3>Tests Performed</h3>
                    <div class="value">{{ scan_result.metadata.total_attacks }}</div>
                </div>
            </div>
            
            {% if scan_result.vulnerability_count > 0 %}
            <h2>🚨 Vulnerabilities Detected</h2>
            
            {% for severity, vulns in vulnerabilities_by_severity.items() %}
                {% if vulns %}
                <h3>{{ severity.title() }} Severity ({{ vulns|length }})</h3>
                {% for vuln in vulns %}
                <div class="vulnerability">
                    <div class="vulnerability-header vulnerability-{{ severity }}">
                        {{ vuln.attack_id }}: {{ vuln.description }}
                    </div>
                    <div class="vulnerability-body">
                        <p><strong>Category:</strong> {{ vuln.category.value.replace('_', ' ').title() }}</p>
                        <p><strong>Risk Score:</strong> {{ "%.1f"|format(vuln.risk_score) }}/10</p>
                        <p><strong>Confidence:</strong> {{ "%.1f"|format(vuln.confidence_score * 100) }}%</p>
                        
                        <h4>Attack Payload:</h4>
                        <div class="code-block">{{ vuln.prompt_used }}</div>
                        
                        <h4>Response (truncated):</h4>
                        <div class="code-block">{{ vuln.response_received[:300] }}{% if vuln.response_received|length > 300 %}...{% endif %}</div>
                        
                        {% if vuln.nist_controls %}
                        <p><strong>NIST Controls:</strong> {{ vuln.nist_controls|join(', ') }}</p>
                        {% endif %}
                        
                        {% if vuln.eu_ai_act_refs %}
                        <p><strong>EU AI Act:</strong> {{ vuln.eu_ai_act_refs|join(', ') }}</p>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
                {% endif %}
            {% endfor %}
            {% else %}
            <div style="text-align: center; padding: 40px; background: #d4edda; border-radius: 8px; color: #155724;">
                <h2>✅ No Vulnerabilities Detected</h2>
                <p>All {{ scan_result.metadata.total_attacks }} security tests passed successfully.</p>
            </div>
            {% endif %}
            
            {% if scan_result.immediate_actions %}
            <h2>⚡ Immediate Actions Required</h2>
            <ul>
                {% for action in scan_result.immediate_actions %}
                <li>{{ action }}</li>
                {% endfor %}
            </ul>
            {% endif %}
            
            {% if scan_result.recommended_controls %}
            <h2>🛡️ Recommended Security Controls</h2>
            <ul>
                {% for control in scan_result.recommended_controls %}
                <li>{{ control }}</li>
                {% endfor %}
            </ul>
            {% endif %}
            
            <div class="compliance-section">
                <h2>📋 Compliance Summary</h2>
                <p><strong>NIST AI-RMF Risk Category:</strong> {{ scan_result.compliance.eu_ai_act_risk_category.title() }}</p>
                <p><strong>Controls Tested:</strong> {{ scan_result.compliance.nist_rmf_controls_tested|length }} NIST controls</p>
                <p><strong>EU AI Act Articles:</strong> {{ scan_result.compliance.eu_ai_act_articles_relevant|join(', ') }}</p>
                <p><strong>Scan Duration:</strong> {{ "%.1f"|format(scan_result.duration_seconds) }} seconds</p>
                {% if scan_result.metadata.total_cost_usd %}
                <p><strong>Estimated Cost:</strong> ${{ "%.4f"|format(scan_result.metadata.total_cost_usd) }}</p>
                {% endif %}
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by PromptStrike CLI v0.1.0 | Sprint S-1 MVP</p>
            <p>For support: <a href="mailto:dev@promptstrike.com">dev@promptstrike.com</a></p>
        </div>
    </div>
</body>
</html>
        """
        return Template(template_str)
    
    def _generate_markdown_report(self, scan_result: ScanResult) -> str:
        """Generate markdown content for PDF report"""
        content = f"""
# PromptStrike Security Scan Report

**Target:** {scan_result.target}  
**Scan ID:** {scan_result.scan_id}  
**Duration:** {scan_result.duration_seconds:.1f} seconds  
**Overall Risk Score:** {scan_result.overall_risk_score:.1f}/10  
**Security Posture:** {scan_result.security_posture.upper()}  

## Executive Summary

- **Total Tests:** {scan_result.metadata.total_attacks}
- **Vulnerabilities Found:** {scan_result.vulnerability_count}
- **Critical Issues:** {len([r for r in scan_result.results if r.is_vulnerable and r.severity == SeverityLevel.CRITICAL])}
- **High Priority Issues:** {len([r for r in scan_result.results if r.is_vulnerable and r.severity == SeverityLevel.HIGH])}

## Vulnerability Details

"""
        
        vulnerabilities = [r for r in scan_result.results if r.is_vulnerable]
        
        if vulnerabilities:
            for vuln in sorted(vulnerabilities, key=lambda x: x.risk_score, reverse=True):
                content += f"""
### {vuln.attack_id}: {vuln.description}

- **Category:** {vuln.category.value.replace('_', ' ').title()}
- **Severity:** {vuln.severity.value.upper()}
- **Risk Score:** {vuln.risk_score:.1f}/10
- **Confidence:** {vuln.confidence_score * 100:.1f}%

**Attack Payload:**
```
{vuln.prompt_used}
```

**Response (truncated):**
```
{vuln.response_received[:200]}{'...' if len(vuln.response_received) > 200 else ''}
```

---
"""
        else:
            content += "No vulnerabilities detected. All security tests passed.\\n"
        
        return content