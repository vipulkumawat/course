from typing import Dict, List, Any
from datetime import datetime
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import pandas as pd

class ComplianceReportGenerator:
    def __init__(self, output_path: str = "data/reports"):
        self.output_path = output_path
        os.makedirs(output_path, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom report styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=12
        ))
    
    def generate_pci_dss_report(self, coverage_data: Dict[str, Any],
                                evidence_data: Dict[str, List[Dict]], 
                                gaps: List[str]) -> str:
        """Generate PCI-DSS compliance report"""
        filename = f"PCI_DSS_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(self.output_path, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        
        # Title
        story.append(Paragraph("PCI-DSS Compliance Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        summary_text = f"""
        <b>Report Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
        <b>Framework:</b> PCI-DSS v4.0<br/>
        <b>Coverage:</b> {coverage_data['coverage_percentage']:.1f}%<br/>
        <b>Requirements with Evidence:</b> {coverage_data['requirements_with_evidence']} / {coverage_data['total_requirements']}<br/>
        <b>Compliance Gaps:</b> {len(gaps)}
        """
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Coverage Details
        story.append(Paragraph("Coverage by Requirement", self.styles['SectionHeader']))
        coverage_table_data = [["Requirement", "Evidence Count", "Status"]]
        
        for req_id, count in coverage_data['evidence_by_requirement'].items():
            status = "✓ Compliant" if count > 0 else "✗ Gap"
            coverage_table_data.append([req_id, str(count), status])
        
        coverage_table = Table(coverage_table_data, colWidths=[2*inch, 2*inch, 2*inch])
        coverage_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(coverage_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Gap Analysis
        if gaps:
            story.append(Paragraph("Compliance Gaps Requiring Attention", self.styles['SectionHeader']))
            gap_text = "<br/>".join([f"• Requirement {gap}: No evidence collected" for gap in gaps])
            story.append(Paragraph(gap_text, self.styles['Normal']))
        
        doc.build(story)
        return filepath
    
    def generate_soc2_report(self, coverage_data: Dict[str, Any],
                            evidence_data: Dict[str, List[Dict]],
                            gaps: List[str]) -> str:
        """Generate SOC2 compliance report"""
        filename = f"SOC2_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(self.output_path, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        
        # Title
        story.append(Paragraph("SOC 2 Type II Compliance Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Trust Services Criteria
        story.append(Paragraph("Trust Services Criteria Assessment", self.styles['SectionHeader']))
        summary_text = f"""
        <b>Reporting Period:</b> {datetime.now().strftime('%Y-%m-%d')}<br/>
        <b>Framework:</b> SOC 2 Type II<br/>
        <b>Control Coverage:</b> {coverage_data['coverage_percentage']:.1f}%<br/>
        <b>Total Control Points:</b> {coverage_data['total_requirements']}<br/>
        <b>Effective Controls:</b> {coverage_data['requirements_with_evidence']}
        """
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Control Effectiveness
        story.append(Paragraph("Control Effectiveness by Category", self.styles['SectionHeader']))
        control_data = [["Control Point", "Evidence Count", "Effectiveness"]]
        
        for req_id, count in coverage_data['evidence_by_requirement'].items():
            effectiveness = "Operating Effectively" if count >= 3 else "Requires Testing"
            control_data.append([req_id, str(count), effectiveness])
        
        control_table = Table(control_data, colWidths=[2*inch, 2*inch, 2*inch])
        control_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(control_table)
        
        doc.build(story)
        return filepath
    
    def generate_iso27001_report(self, coverage_data: Dict[str, Any],
                                  evidence_data: Dict[str, List[Dict]],
                                  gaps: List[str]) -> str:
        """Generate ISO 27001 compliance report"""
        filename = f"ISO27001_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(self.output_path, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        
        # Title
        story.append(Paragraph("ISO 27001 Compliance Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        summary_text = f"""
        <b>Report Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
        <b>Framework:</b> ISO/IEC 27001:2022<br/>
        <b>Coverage:</b> {coverage_data['coverage_percentage']:.1f}%<br/>
        <b>Controls with Evidence:</b> {coverage_data['requirements_with_evidence']} / {coverage_data['total_requirements']}<br/>
        <b>Compliance Gaps:</b> {len(gaps)}
        """
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Coverage Details
        story.append(Paragraph("Control Coverage", self.styles['SectionHeader']))
        coverage_table_data = [["Control", "Evidence Count", "Status"]]
        
        for req_id, count in coverage_data['evidence_by_requirement'].items():
            status = "✓ Implemented" if count > 0 else "✗ Gap"
            coverage_table_data.append([req_id, str(count), status])
        
        coverage_table = Table(coverage_table_data, colWidths=[2*inch, 2*inch, 2*inch])
        coverage_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(coverage_table)
        
        doc.build(story)
        return filepath
    
    def generate_hipaa_report(self, coverage_data: Dict[str, Any],
                              evidence_data: Dict[str, List[Dict]],
                              gaps: List[str]) -> str:
        """Generate HIPAA compliance report"""
        filename = f"HIPAA_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(self.output_path, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        
        # Title
        story.append(Paragraph("HIPAA Compliance Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        summary_text = f"""
        <b>Report Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
        <b>Framework:</b> HIPAA Security Rule<br/>
        <b>Coverage:</b> {coverage_data['coverage_percentage']:.1f}%<br/>
        <b>Requirements with Evidence:</b> {coverage_data['requirements_with_evidence']} / {coverage_data['total_requirements']}<br/>
        <b>Compliance Gaps:</b> {len(gaps)}
        """
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Coverage Details
        story.append(Paragraph("Requirement Coverage", self.styles['SectionHeader']))
        coverage_table_data = [["Requirement", "Evidence Count", "Status"]]
        
        for req_id, count in coverage_data['evidence_by_requirement'].items():
            status = "✓ Compliant" if count > 0 else "✗ Gap"
            coverage_table_data.append([req_id, str(count), status])
        
        coverage_table = Table(coverage_table_data, colWidths=[2*inch, 2*inch, 2*inch])
        coverage_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(coverage_table)
        
        doc.build(story)
        return filepath
    
    def generate_multi_framework_report(self, all_coverage: Dict[str, Dict], 
                                       all_gaps: Dict[str, List[str]]) -> str:
        """Generate combined multi-framework report"""
        filename = f"Multi_Framework_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(self.output_path, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        
        # Title
        story.append(Paragraph("Multi-Framework Compliance Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Overview
        story.append(Paragraph("Compliance Overview", self.styles['SectionHeader']))
        overview_data = [["Framework", "Coverage", "Requirements", "Gaps"]]
        
        for framework_name, coverage in all_coverage.items():
            gaps_count = len(all_gaps.get(framework_name, []))
            overview_data.append([
                framework_name.upper(),
                f"{coverage['coverage_percentage']:.1f}%",
                f"{coverage['requirements_with_evidence']}/{coverage['total_requirements']}",
                str(gaps_count)
            ])
        
        overview_table = Table(overview_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(overview_table)
        
        doc.build(story)
        return filepath
    
    def export_to_excel(self, coverage_data: Dict[str, Any], 
                       framework_name: str) -> str:
        """Export compliance data to Excel"""
        filename = f"{framework_name}_Data_{datetime.now().strftime('%Y%m%d')}.xlsx"
        filepath = os.path.join(self.output_path, filename)
        
        # Create DataFrame
        data = []
        for req_id, count in coverage_data['evidence_by_requirement'].items():
            data.append({
                "Requirement": req_id,
                "Evidence Count": count,
                "Status": "Compliant" if count > 0 else "Gap"
            })
        
        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False, engine='openpyxl')
        
        return filepath
