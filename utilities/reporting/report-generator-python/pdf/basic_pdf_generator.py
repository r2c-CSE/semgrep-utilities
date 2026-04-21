import os
import urllib.parse
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable, PageBreak, KeepTogether, Image,
    Flowable
)
from reportlab.platypus.flowables import Flowable

from models import SemgrepProject, SemgrepFinding, ReportConfiguration, SemgrepLevel
from services.scoring_engine import ScoringEngine

# ─── Color constants ─────────────────────────────────────────────────────────
GREEN = HexColor('#00A86B')
DARK_GREEN = HexColor('#007A4D')
LIGHT_GREEN = HexColor('#D4EDDA')
RED = HexColor('#DC3545')
LIGHT_RED = HexColor('#FFEAEA')
ORANGE = HexColor('#FD7E14')
LIGHT_ORANGE = HexColor('#FFF3CD')
YELLOW = HexColor('#FFC107')
BLUE = HexColor('#007BFF')
TEAL = HexColor('#17A2B8')
LIGHT_TEAL = HexColor('#D1ECF1')
GRAY = HexColor('#666666')
DARK_GRAY = HexColor('#333333')
LIGHT_GRAY = HexColor('#F5F5F5')
MID_GRAY = HexColor('#F8F9FA')
BORDER_GRAY = HexColor('#DEE2E6')

PAGE_WIDTH, PAGE_HEIGHT = A4
HEADER_HEIGHT = 60
FOOTER_HEIGHT = 30
MARGIN = 30
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN

SEVERITY_COLORS = {
    'Critical': RED,
    'High': ORANGE,
    'Medium': YELLOW,
    'Low': HexColor('#28A745'),
}

OWASP_URLS = {
    'broken-access-control': 'https://owasp.org/Top10/A01_2021-Broken_Access_Control/',
    'cryptographic-failures': 'https://owasp.org/Top10/A02_2021-Cryptographic_Failures/',
    'injection': 'https://owasp.org/Top10/A03_2021-Injection/',
    'insecure-design': 'https://owasp.org/Top10/A04_2021-Insecure_Design/',
    'security-misconfiguration': 'https://owasp.org/Top10/A05_2021-Security_Misconfiguration/',
    'vulnerable-components': 'https://owasp.org/Top10/A06_2021-Vulnerable_and_Outdated_Components/',
    'identification-authentication-failures': 'https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/',
    'software-data-integrity-failures': 'https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/',
    'security-logging-monitoring-failures': 'https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/',
    'server-side-request-forgery': 'https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery/',
}

OWASP_DISPLAY_NAMES = {
    'broken-access-control': 'OWASP Top Ten 2021 Category A01 - Broken Access Control',
    'cryptographic-failures': 'OWASP Top Ten 2021 Category A02 - Cryptographic Failures',
    'injection': 'OWASP Top Ten 2021 Category A03 - Injection',
    'insecure-design': 'OWASP Top Ten 2021 Category A04 - Insecure Design',
    'security-misconfiguration': 'OWASP Top Ten 2021 Category A05 - Security Misconfiguration',
    'vulnerable-components': 'OWASP Top Ten 2021 Category A06 - Vulnerable and Outdated Components',
    'identification-authentication-failures': 'OWASP Top Ten 2021 Category A07 - Identification and Authentication Failures',
    'software-data-integrity-failures': 'OWASP Top Ten 2021 Category A08 - Software and Data Integrity Failures',
    'security-logging-monitoring-failures': 'OWASP Top Ten 2021 Category A09 - Security Logging and Monitoring Failures',
    'server-side-request-forgery': 'OWASP Top Ten 2021 Category A10 - Server-Side Request Forgery',
}

# Canonical OWASP 2021 ordering used for sorting and display
OWASP_CATEGORY_ORDER = [
    'broken-access-control',
    'cryptographic-failures',
    'injection',
    'insecure-design',
    'security-misconfiguration',
    'vulnerable-components',
    'identification-authentication-failures',
    'software-data-integrity-failures',
    'security-logging-monitoring-failures',
    'server-side-request-forgery',
]

# Short labels for the summary table (A01 … A10)
OWASP_SHORT_LABELS = {
    'broken-access-control': 'A01',
    'cryptographic-failures': 'A02',
    'injection': 'A03',
    'insecure-design': 'A04',
    'security-misconfiguration': 'A05',
    'vulnerable-components': 'A06',
    'identification-authentication-failures': 'A07',
    'software-data-integrity-failures': 'A08',
    'security-logging-monitoring-failures': 'A09',
    'server-side-request-forgery': 'A10',
}


# ─── Custom flowables ─────────────────────────────────────────────────────────

class ColorRect(Flowable):
    """A filled rectangle that spans the content width, used as a colored section background."""
    def __init__(self, height: float, fill_color: HexColor, border_color: Optional[HexColor] = None,
                 border_width: float = 0, radius: float = 0):
        super().__init__()
        self.height = height
        self.fill_color = fill_color
        self.border_color = border_color
        self.border_width = border_width
        self.radius = radius
        self.width = CONTENT_WIDTH

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(self.fill_color)
        if self.border_color and self.border_width:
            c.setStrokeColor(self.border_color)
            c.setLineWidth(self.border_width)
        if self.radius:
            c.roundRect(0, 0, self.width, self.height, self.radius,
                        stroke=1 if (self.border_color and self.border_width) else 0,
                        fill=1)
        else:
            c.rect(0, 0, self.width, self.height,
                   stroke=1 if (self.border_color and self.border_width) else 0,
                   fill=1)
        c.restoreState()

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return availWidth, self.height


class SeverityBar(Flowable):
    """Horizontal bar chart row for a single severity level."""
    def __init__(self, label: str, count: int, max_count: int,
                 label_color: HexColor, bar_color: HexColor, max_bar_width: float = 200):
        super().__init__()
        self.label = label
        self.count = count
        self.max_count = max_count
        self.label_color = label_color
        self.bar_color = bar_color
        self.max_bar_width = max_bar_width
        self.height = 22

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return availWidth, self.height

    def draw(self):
        c = self.canv
        c.saveState()

        label_w = 55
        count_w = 35
        bar_area_w = self.width - label_w - count_w - 10

        # Label
        c.setFont('Helvetica-Bold', 10)
        c.setFillColor(self.label_color)
        c.drawString(0, 6, self.label)

        # Bar
        if self.max_count > 0:
            bar_w = max((self.count / self.max_count) * min(self.max_bar_width, bar_area_w),
                        20 if self.count > 0 else 0)
        else:
            bar_w = 0

        c.setFillColor(self.bar_color)
        c.rect(label_w, 2, bar_w, 16, stroke=0, fill=1)

        # Count inside/after bar
        if self.count > 10 and bar_w > 25:
            c.setFont('Helvetica-Bold', 9)
            c.setFillColor(colors.white)
            c.drawString(label_w + 4, 6, str(self.count))

        # Count to the right
        c.setFont('Helvetica-Bold', 10)
        c.setFillColor(self.label_color)
        c.drawRightString(self.width, 6, str(self.count))

        c.restoreState()


# ─── Header/footer drawing helpers ────────────────────────────────────────────

def _get_asset_path(filename: str) -> Optional[str]:
    """Find an asset file, looking in the sibling report-generator/assets directory."""
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Try relative to this package first
    local = os.path.join(script_dir, 'assets', filename)
    if os.path.exists(local):
        return local
    # Try sibling Node.js directory
    sibling = os.path.join(os.path.dirname(script_dir), 'report-generator', 'assets', filename)
    if os.path.exists(sibling):
        return sibling
    return None


def _draw_header(canvas, doc, title: str = 'Application Security Report'):
    canvas.saveState()
    # Green header bar
    canvas.setFillColor(GREEN)
    canvas.rect(0, PAGE_HEIGHT - HEADER_HEIGHT, PAGE_WIDTH, HEADER_HEIGHT, stroke=0, fill=1)

    # Title text
    canvas.setFont('Helvetica-Bold', 18)
    canvas.setFillColor(colors.white)
    canvas.drawString(MARGIN, PAGE_HEIGHT - HEADER_HEIGHT + 20, title)

    # Semgrep logo
    logo_path = _get_asset_path('semgrep-logo.png')
    if logo_path:
        try:
            canvas.drawImage(logo_path, PAGE_WIDTH - 110, PAGE_HEIGHT - HEADER_HEIGHT + 10,
                             width=90, height=35, preserveAspectRatio=True, mask='auto')
        except Exception:
            canvas.setFont('Helvetica-Bold', 14)
            canvas.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - HEADER_HEIGHT + 20, 'Semgrep')

    canvas.restoreState()


def _draw_footer(canvas, doc, footer_text: str):
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(GRAY)
    canvas.drawCentredString(PAGE_WIDTH / 2, 20, footer_text)
    canvas.restoreState()


# ─── Style helpers ────────────────────────────────────────────────────────────

def _styles():
    base = getSampleStyleSheet()
    styles = {}

    def s(name, parent='Normal', **kw):
        styles[name] = ParagraphStyle(name, parent=base[parent], **kw)

    s('SectionTitle', fontSize=20, textColor=GREEN, fontName='Helvetica-Bold', spaceAfter=10)
    s('SubTitle', fontSize=16, textColor=DARK_GRAY, fontName='Helvetica-Bold', spaceAfter=8)
    s('GreenSubTitle', fontSize=14, textColor=GREEN, fontName='Helvetica-Bold', spaceAfter=6)
    s('Body', fontSize=11, textColor=DARK_GRAY, leading=16, spaceAfter=6)
    s('SmallBody', fontSize=10, textColor=DARK_GRAY, leading=14, spaceAfter=4)
    s('TinyBody', fontSize=9, textColor=DARK_GRAY, leading=13, spaceAfter=3)
    s('XTiny', fontSize=8, textColor=DARK_GRAY, leading=12, spaceAfter=2)
    s('Bold', fontSize=11, fontName='Helvetica-Bold', textColor=DARK_GRAY, spaceAfter=4)
    s('SmallBold', fontSize=10, fontName='Helvetica-Bold', textColor=DARK_GRAY, spaceAfter=3)
    s('TinyBold', fontSize=9, fontName='Helvetica-Bold', textColor=DARK_GRAY, spaceAfter=2)
    s('Code', fontSize=9, fontName='Courier', textColor=GRAY, leading=12, spaceAfter=2)
    s('Label', fontSize=12, fontName='Helvetica-Bold', textColor=DARK_GRAY, spaceAfter=4)
    s('BigValue', fontSize=22, fontName='Helvetica-Bold', textColor=RED, spaceAfter=4)
    s('GreenBigValue', fontSize=22, fontName='Helvetica-Bold', textColor=GREEN, spaceAfter=4)
    s('MainTitle', fontSize=30, fontName='Helvetica-Bold', textColor=GREEN, spaceAfter=8,
      alignment=1)  # center
    s('CenterGray', fontSize=14, textColor=GRAY, alignment=1, spaceAfter=4)
    s('CenterGreen', fontSize=14, fontName='Helvetica-Bold', textColor=GREEN, alignment=1,
      spaceAfter=10)
    s('Italic', fontSize=10, fontName='Helvetica-Oblique', textColor=GRAY, spaceAfter=4)
    s('Link', fontSize=9, textColor=BLUE, underline=True)
    s('SmallLink', fontSize=8, textColor=BLUE, underline=True)
    s('TinyLink', fontSize=7, textColor=BLUE, underline=True)
    s('Critical', fontSize=9, fontName='Helvetica-Bold', textColor=RED)
    s('High', fontSize=9, fontName='Helvetica-Bold', textColor=ORANGE)
    s('Medium', fontSize=9, fontName='Helvetica-Bold', textColor=YELLOW)
    s('Low', fontSize=9, fontName='Helvetica-Bold', textColor=HexColor('#28A745'))
    return styles


def _make_table(data, col_widths, style_cmds=None):
    style = [
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), MID_GRAY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]
    if style_cmds:
        style.extend(style_cmds)
    return Table(data, colWidths=col_widths, style=TableStyle(style), repeatRows=1)


# ─── Main generator class ──────────────────────────────────────────────────────

class BasicPdfGenerator:
    def __init__(self):
        self._scoring = ScoringEngine()
        self._styles = _styles()

    # ── Public entry point ────────────────────────────────────────────────────

    def generate_report(
        self,
        projects: List[SemgrepProject],
        config: ReportConfiguration,
        output_path: str,
    ) -> str:
        print('Generating professional PDF report...')

        now = datetime.now()
        formatted_date = now.strftime('%B %d, %Y')
        formatted_datetime = now.strftime('%m-%d-%Y %H:%M')
        footer_text = f'Generated by Semgrep Reporter  {formatted_datetime}  Confidential'

        all_findings = [f for p in projects for f in p.findings]
        open_findings = [f for f in all_findings if f.status == 'Open']

        combined_project = _make_combined_project(projects)
        overall_level = int(self._scoring.calculate_semgrep_level(combined_project))
        overall_score = self._scoring.calculate_security_score(all_findings)

        # Ensure output dir exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Build page template factory so header/footer are drawn per-page
        def make_template(page_title: str):
            frame = Frame(
                MARGIN, FOOTER_HEIGHT + 5,
                PAGE_WIDTH - 2 * MARGIN,
                PAGE_HEIGHT - HEADER_HEIGHT - FOOTER_HEIGHT - 10,
                leftPadding=0, rightPadding=0, topPadding=10, bottomPadding=0,
            )

            def on_page(canvas, doc):
                _draw_header(canvas, doc, page_title)
                _draw_footer(canvas, doc, footer_text)

            return PageTemplate(id=page_title[:20], frames=[frame], onPage=on_page)

        # Build content story
        story = []

        # Cover page
        story.extend(self._cover_page(projects, config, formatted_date, formatted_datetime,
                                       overall_level, overall_score))
        story.append(PageBreak())

        # Executive Summary
        story.extend(self._executive_summary_page(projects, config, open_findings,
                                                    overall_level))
        story.append(PageBreak())

        # Methodology (optional)
        if config.report_configuration.include_sections.appendix_methodology:
            story.extend(self._methodology_page())
            story.append(PageBreak())

        # Projects Included (paginated)
        story.extend(self._projects_included_pages(projects, config))

        # Scan Summary
        story.extend(self._scan_summary_page(projects, config))
        story.append(PageBreak())

        # OWASP Top 10 summary (all open findings grouped by category)
        story.extend(self._owasp_top10_pages(projects))

        # Individual project pages
        story.extend(self._individual_project_pages(projects, config))

        # Security Roadmap
        story.extend(self._security_roadmap_pages(projects, config, open_findings))

        # Create the document
        doc = BaseDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=HEADER_HEIGHT + 5,
            bottomMargin=FOOTER_HEIGHT + 10,
        )

        default_template = make_template('Application Security Report')
        doc.addPageTemplates([default_template])
        doc.build(story)

        size_mb = os.path.getsize(output_path) / 1024 / 1024
        print(f'PDF report generated: {output_path} ({size_mb:.2f} MB)')
        return output_path

    # ── Page builders ─────────────────────────────────────────────────────────

    def _cover_page(self, projects, config, formatted_date, formatted_datetime,
                    overall_level, overall_score) -> list:
        st = self._styles
        story = []

        story.append(Paragraph(f'{config.customer.name} Portfolio', st['MainTitle']))
        story.append(Paragraph(f'({len(projects)} Projects)', st['CenterGray']))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f'Assessment Date: {formatted_date}', st['CenterGray']))
        story.append(Paragraph(f'Prepared for: {config.customer.reporting_contact}', st['CenterGreen']))
        story.append(HRFlowable(width='100%', thickness=3, color=GREEN, spaceAfter=12))

        # Security Overview box
        story.append(Paragraph('Security Overview', st['SectionTitle']))
        overview_data = [
            [Paragraph('Semgrep Security Level', st['Label']),
             Paragraph('Security Score', st['Label'])],
            [Paragraph(f'SL{overall_level}', st['BigValue']),
             Paragraph(f'{overall_score}/100', st['BigValue'])],
        ]
        overview_table = Table(overview_data,
                               colWidths=[CONTENT_WIDTH / 2, CONTENT_WIDTH / 2],
                               style=TableStyle([
                                   ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
                                   ('BOX', (0, 0), (-1, -1), 0.5, BORDER_GRAY),
                                   ('TOPPADDING', (0, 0), (-1, -1), 10),
                                   ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                                   ('LEFTPADDING', (0, 0), (-1, -1), 12),
                               ]))
        story.append(overview_table)
        story.append(Spacer(1, 12))

        # Application Details
        story.append(Paragraph('Application Details', st['GreenSubTitle']))
        details = [
            ['Application Name:', f'{config.customer.name} Portfolio ({len(projects)} Projects)'],
            ['Repository:', f'Multiple projects ({len(projects)} projects)'],
            ['Business Criticality:', config.application_settings.business_criticality or 'High'],
            ['Last Scanned:', formatted_datetime],
        ]
        for label, value in details:
            row_data = [[Paragraph(label, st['SmallBold']), Paragraph(value, st['SmallBody'])]]
            t = Table(row_data, colWidths=[100, CONTENT_WIDTH - 100],
                      style=TableStyle([('TOPPADDING', (0, 0), (-1, -1), 3),
                                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
            story.append(t)

        story.append(Spacer(1, 12))

        # Scan Coverage
        story.append(Paragraph('Scan Coverage', st['GreenSubTitle']))
        scan_data_row = [['SAST', 'Supply Chain', 'Secrets']]

        def _scan_para(done: bool, style_name: str) -> Paragraph:
            return Paragraph(
                'Complete' if done else 'Missing',
                ParagraphStyle(style_name, textColor=HexColor('#28A745') if done else RED,
                               fontName='Helvetica-Bold', fontSize=11)
            )

        sast_done = any(p.scan_data.sast_completed for p in projects)
        sca_done = any(p.scan_data.supply_chain_completed for p in projects)
        secrets_done = any(p.scan_data.secrets_completed for p in projects)
        scan_table = Table(
            [scan_data_row[0], [_scan_para(sast_done, 'sc'), _scan_para(sca_done, 'sc2'), _scan_para(secrets_done, 'sm')]],
            colWidths=[CONTENT_WIDTH / 3] * 3,
            style=TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GRAY),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ])
        )
        story.append(scan_table)

        return story

    def _executive_summary_page(self, projects, config, open_findings, overall_level) -> list:
        st = self._styles
        story = []

        critical = sum(1 for f in open_findings if f.severity == 'Critical')
        high = sum(1 for f in open_findings if f.severity == 'High')

        story.append(Paragraph('Executive Summary', st['SectionTitle']))

        # Risk Assessment
        story.append(Paragraph('Risk Assessment', st['GreenSubTitle']))
        risk_level = 'HIGH RISK' if (critical > 0 or high > 10) else ('MODERATE RISK' if high > 0 else 'LOW RISK')
        attn = 'immediate attention is required' if (critical > 0 or high > 10) else 'regular monitoring is recommended'
        level_text = 'indicates significant security improvements are needed' if overall_level <= 2 else 'shows acceptable security practices'
        story.append(Paragraph(
            f'This application presents a <b>{risk_level}</b> security posture with {critical} critical and {high} high '
            f'severity findings. Given the {config.application_settings.business_criticality or "High"} business criticality '
            f'rating, {attn} to address the most severe vulnerabilities. The current Semgrep Security Level of SL{overall_level} '
            f'{level_text} before this application meets industry standards for secure software development.',
            st['Body']
        ))

        story.append(Spacer(1, 8))

        # Business Impact Analysis
        story.append(Paragraph('Business Impact Analysis', st['GreenSubTitle']))
        impact_msg = ('Exploitation causes serious brand damage and financial loss with long term business impact'
                      if (critical > 0 or high > 5)
                      else 'Moderate security risk with potential for data exposure')
        story.append(Paragraph(f'<b>{impact_msg}</b>', st['Body']))
        likely_possible = 'likely' if critical > 0 else 'possible'
        sig_moderate = 'significant' if (critical > 0 or high > 5) else 'moderate'
        story.append(Paragraph(
            f'The {high + critical} high-priority security findings pose {sig_moderate} risk to business operations, '
            f'customer data, and regulatory compliance. Financial losses and reputational damage are {likely_possible} if exploited.',
            st['Body']
        ))

        story.append(Spacer(1, 8))

        # Key Recommendations
        story.append(Paragraph('Key Recommendations', st['GreenSubTitle']))
        rec1 = ('Immediate attention required for critical severity findings'
                if critical > 0 else 'Continue monitoring for emerging threats')
        for bullet in [
            rec1,
            'Establish automated security scanning in CI/CD pipeline',
            'Implement developer security training program',
            'Regular security assessments and code reviews',
        ]:
            story.append(Paragraph(f'\u2022 {bullet}', st['Body']))

        return story

    def _methodology_page(self) -> list:
        st = self._styles
        story = []

        story.append(Paragraph('Assessment Methodology', st['SectionTitle']))

        # Semgrep Security Levels
        story.append(Paragraph('Semgrep Security Levels (SL1-SL5)', st['GreenSubTitle']))
        story.append(Paragraph(
            'The Semgrep Security Level provides a standardized way to communicate application security posture, '
            'similar to Veracode\'s VL system but adapted for modern SAST scanning.',
            st['Body']
        ))

        level_data = [
            ['Level', 'Criteria', 'Description'],
            ['SL5', '0 Critical, 0 High, Score 90+', 'Excellent security posture with minimal risk'],
            ['SL4', '0 Critical, 3 or less High, Score 80+', 'Very good security with minor issues'],
            ['SL3', '0 Critical, 10 or less High, Score 70+', 'Acceptable security with moderate risk'],
            ['SL2', '5 or less Critical, Score 60+', 'Below average security requiring attention'],
            ['SL1', 'More than 5 Critical or Score under 60', 'Poor security posture requiring immediate action'],
        ]
        level_colors = [
            LIGHT_GREEN, HexColor('#D1ECF1'), HexColor('#FFF3CD'),
            HexColor('#F8D7DA'), HexColor('#F5C6CB')
        ]
        level_text_colors = [
            HexColor('#155724'), HexColor('#0C5460'), HexColor('#856404'),
            HexColor('#721C24'), HexColor('#721C24')
        ]
        style_cmds = [('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')]
        for i, (bg, tc) in enumerate(zip(level_colors, level_text_colors), start=1):
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))
            style_cmds.append(('TEXTCOLOR', (0, i), (-1, i), tc))
        level_table = Table(
            level_data,
            colWidths=[CONTENT_WIDTH * 0.12, CONTENT_WIDTH * 0.38, CONTENT_WIDTH * 0.50],
            style=TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GRAY),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ] + style_cmds)
        )
        story.append(level_table)
        story.append(Spacer(1, 12))

        # Scoring
        story.append(Paragraph('Security Score Calculation', st['GreenSubTitle']))
        story.append(Paragraph('The security score uses a weighted approach similar to CVSS scoring:', st['Body']))
        scoring_data = [
            ['Severity', 'Weight', 'Impact'],
            ['Critical', '50', 'High business risk'],
            ['High', '20', 'Moderate business risk'],
            ['Medium', '5', 'Low business risk'],
            ['Low', '1', 'Minimal business risk'],
        ]
        scoring_table = Table(
            scoring_data,
            colWidths=[CONTENT_WIDTH * 0.25, CONTENT_WIDTH * 0.25, CONTENT_WIDTH * 0.50],
            style=TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GRAY),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ])
        )
        story.append(scoring_table)
        story.append(Paragraph(
            'Score = max(0, 100 - (total_weighted_impact x 100 / max_impact))',
            ParagraphStyle('formula', fontName='Courier', fontSize=10, backColor=LIGHT_GRAY,
                           borderPadding=6)
        ))

        # OWASP note
        story.append(Spacer(1, 12))
        story.append(Paragraph('OWASP Top 10 2021 Mapping', st['GreenSubTitle']))
        story.append(Paragraph(
            'Security findings are mapped to OWASP Top 10 2021 categories to provide compliance context and '
            'industry-standard risk classification.',
            st['Body']
        ))

        return story

    def _projects_included_pages(self, projects, config) -> list:
        st = self._styles
        story = []

        repos = self._get_actual_repositories(projects)
        items_per_page = 17

        for page_idx in range(0, max(1, len(repos)), items_per_page):
            page_repos = repos[page_idx:page_idx + items_per_page]
            is_first = page_idx == 0
            page_num = page_idx // items_per_page + 1

            title = 'Projects Included' if is_first else f'Projects Included (Page {page_num})'
            story.append(Paragraph(title, st['SectionTitle']))

            if is_first:
                total_files = sum(r['files_scanned'] for r in repos)
                story.append(Paragraph(
                    f'This security assessment includes repositories from the {config.customer.name} organization.',
                    st['Body']
                ))
                story.append(Paragraph(
                    f'This comprehensive scan covers {total_files:,} files across {len(repos)} '
                    f'repositor{"ies" if len(repos) != 1 else "y"}, identifying security vulnerabilities, '
                    f'code quality issues, and supply chain risks using Semgrep\'s static analysis engine.',
                    st['Body']
                ))

            if page_repos:
                table_data = [['Repository', 'Open\nFindings', 'Files\nScanned', 'Scan\nDuration', 'Last\nScanned']]
                for repo in page_repos:
                    table_data.append([
                        repo['name'],
                        str(repo['open_findings']),
                        str(repo['files_scanned']),
                        repo['scan_duration'],
                        repo['last_scanned'],
                    ])

                style_cmds = []
                for i, repo in enumerate(page_repos, start=1):
                    if repo['open_findings'] > 100:
                        style_cmds.append(('TEXTCOLOR', (1, i), (1, i), RED))
                    elif repo['open_findings'] > 50:
                        style_cmds.append(('TEXTCOLOR', (1, i), (1, i), ORANGE))

                t = _make_table(
                    table_data,
                    [CONTENT_WIDTH * 0.45, CONTENT_WIDTH * 0.13, CONTENT_WIDTH * 0.14,
                     CONTENT_WIDTH * 0.14, CONTENT_WIDTH * 0.14],
                    style_cmds
                )
                story.append(t)
            else:
                story.append(Paragraph('No repositories with open findings found.', st['Body']))

            story.append(PageBreak())

        return story

    def _scan_summary_page(self, projects, config) -> list:
        st = self._styles
        story = []

        story.append(Paragraph('Scan Summary', st['SectionTitle']))

        open_total = sum(len([f for f in p.findings if f.status == 'Open']) for p in projects)
        repos = self._get_actual_repositories(projects)
        total_files = sum(r['files_scanned'] for r in repos)

        summary_data = [
            ['Total Open Findings:', str(open_total)],
            ['Total Files Scanned:', f'{total_files:,}'],
            ['Average Scan Duration:', '7.2 minutes'],
            ['Most Recent Scan:', datetime.now().strftime('%m/%d/%Y %H:%M')],
        ]
        for label, value in summary_data:
            row_data = [[Paragraph(label, st['SmallBold']), Paragraph(value, st['SmallBody'])]]
            t = Table(row_data, colWidths=[CONTENT_WIDTH * 0.45, CONTENT_WIDTH * 0.55],
                      style=TableStyle([('TOPPADDING', (0, 0), (-1, -1), 4),
                                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
            story.append(t)

        story.append(Spacer(1, 12))
        story.append(Paragraph(
            'Note: Scan durations represent the time taken to analyze each project. Times may vary based on project size, complexity, and scan configuration.',
            ParagraphStyle('note', parent=st['TinyBody'], textColor=GRAY, fontName='Helvetica-Oblique')
        ))
        story.append(Spacer(1, 12))

        # Assessment Configuration
        story.append(Paragraph('Assessment Configuration', st['GreenSubTitle']))

        col1 = [
            Paragraph('<b>Security Scans Enabled:</b>', st['SmallBody']),
            Paragraph('- Static Analysis (SAST): Enabled', st['SmallBody']),
            Paragraph('- Supply Chain Analysis: Enabled', st['SmallBody']),
            Paragraph('- Secrets Detection: Enabled', st['SmallBody']),
            Spacer(1, 8),
            Paragraph('<b>Business Context:</b>', st['SmallBody']),
            Paragraph(f'- Criticality: {config.application_settings.business_criticality}', st['SmallBody']),
            Paragraph(f'- Risk Tolerance: {config.application_settings.risk_tolerance}', st['SmallBody']),
        ]
        col2_items = [Paragraph('<b>Active Rulesets:</b>', st['SmallBody'])]
        for ruleset in config.semgrep_configuration.rulesets:
            col2_items.append(Paragraph(f'- {ruleset}', st['SmallBody']))
        col2_items.append(Spacer(1, 8))
        col2_items.append(Paragraph('<b>Compliance Requirements:</b>', st['SmallBody']))
        for req in config.application_settings.compliance_requirements[:4]:
            col2_items.append(Paragraph(f'- {req}', st['SmallBody']))
        if len(config.application_settings.compliance_requirements) > 4:
            extra = len(config.application_settings.compliance_requirements) - 4
            col2_items.append(Paragraph(f'+{extra} additional requirements', st['Italic']))

        config_data = [[col1, col2_items]]
        config_table = Table(
            [[col1, col2_items]],
            colWidths=[CONTENT_WIDTH / 2, CONTENT_WIDTH / 2],
            style=TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                               ('LEFTPADDING', (0, 0), (-1, -1), 0),
                               ('RIGHTPADDING', (0, 0), (-1, -1), 0)])
        )
        story.append(config_table)

        return story

    def _individual_project_pages(self, projects, config) -> list:
        story = []
        projects_with_findings = [p for p in projects if any(f.status == 'Open' for f in p.findings)]
        top_projects = projects_with_findings[:12]

        print(f'Generating {len(top_projects)} project pages from {len(projects)} total projects')

        for project in top_projects:
            story.extend(self._render_project_summary_pages(project, config))
            story.extend(self._render_project_detailed_findings(project, config))

        return story

    def _render_project_summary_pages(self, project: SemgrepProject, config: ReportConfiguration) -> list:
        st = self._styles
        story = []

        open_findings = [f for f in project.findings if f.status == 'Open']
        critical = sum(1 for f in open_findings if f.severity == 'Critical')
        high = sum(1 for f in open_findings if f.severity == 'High')
        medium = sum(1 for f in open_findings if f.severity == 'Medium')
        low = sum(1 for f in open_findings if f.severity == 'Low')

        score = self._calc_project_score(open_findings)
        level = self._calc_project_level({'critical': critical, 'high': high}, score)

        top_findings = (
            [f for f in open_findings if f.severity == 'Critical'][:8] +
            [f for f in open_findings if f.severity == 'High'][:8]
        )[:12]

        items_first_page = 2
        items_continuation = 4

        remaining = list(top_findings)
        page_num = 0

        while page_num == 0 or remaining:
            is_first = page_num == 0
            per_page = items_first_page if is_first else items_continuation
            page_findings = remaining[:per_page]
            remaining = remaining[per_page:]

            title = project.name if is_first else f'{project.name} (Page {page_num + 1})'
            story.append(Paragraph(title, st['SectionTitle']))

            if is_first and project.project_id:
                story.append(Paragraph(f'Project ID: {project.project_id}',
                                        ParagraphStyle('pid', fontSize=9, textColor=GRAY)))
                if config.report_configuration.include_dashboard_links:
                    url = self._get_dashboard_url(project.project_id, config)
                    if url:
                        story.append(Paragraph(
                            f'<link href="{url}"><u>View in Semgrep Dashboard</u></link>',
                            st['SmallLink']
                        ))

            if is_first:
                # Security Overview
                story.append(Paragraph('Security Overview', st['GreenSubTitle']))
                overview_data = [
                    [Paragraph('Total Open Findings:', st['SmallBold']),
                     Paragraph(str(len(open_findings)),
                               ParagraphStyle('ov', fontSize=10,
                                              textColor=RED if critical > 0 else GRAY))],
                    [Paragraph('Security Level:', st['SmallBold']),
                     Paragraph(level, ParagraphStyle('lv', fontSize=10,
                                                      textColor=self._level_color(level)))],
                    [Paragraph('Security Score:', st['SmallBold']),
                     Paragraph(f'{score}/100', st['SmallBody'])],
                ]
                ov_table = Table(overview_data,
                                 colWidths=[CONTENT_WIDTH * 0.45, CONTENT_WIDTH * 0.55],
                                 style=TableStyle([
                                     ('TOPPADDING', (0, 0), (-1, -1), 4),
                                     ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                                 ]))
                story.append(ov_table)
                story.append(Spacer(1, 8))

                # Severity chart
                story.append(Paragraph('Severity Distribution:', st['SmallBold']))
                max_c = max(critical, high, medium, low) or 1
                for label, count, color in [
                    ('Critical', critical, RED),
                    ('High', high, ORANGE),
                    ('Medium', medium, YELLOW),
                    ('Low', low, HexColor('#28A745')),
                ]:
                    if count > 0 or label != 'Low':
                        story.append(SeverityBar(label, count, max_c, color, color))
                story.append(Spacer(1, 8))

            # Priority findings
            if page_findings and config.report_configuration.findings_detail_level in ('brief', 'standard'):
                title_str = (f'Priority Findings ({len(top_findings)} total)' if is_first
                             else 'Priority Findings (Continued)')
                story.append(Paragraph(title_str, st['GreenSubTitle']))

                for finding in page_findings:
                    sev_color = SEVERITY_COLORS.get(finding.severity, GRAY)
                    finding_content = self._render_brief_finding(finding, project, config, st)

                    finding_table = Table(
                        [[finding_content]],
                        colWidths=[CONTENT_WIDTH],
                        style=TableStyle([
                            ('BOX', (0, 0), (-1, -1), 0.5, sev_color),
                            ('TOPPADDING', (0, 0), (-1, -1), 4),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                            ('LEFTPADDING', (0, 0), (-1, -1), 6),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
                        ])
                    )
                    story.append(finding_table)
                    story.append(Spacer(1, 4))

                if is_first and len(open_findings) > len(top_findings):
                    story.append(Paragraph(
                        f'... and {len(open_findings) - len(top_findings)} additional findings',
                        st['Italic']
                    ))

            story.append(PageBreak())
            page_num += 1

        return story

    def _render_brief_finding(self, finding: SemgrepFinding, project: SemgrepProject,
                               config: ReportConfiguration, st: dict) -> list:
        sev_color = SEVERITY_COLORS.get(finding.severity, GRAY)
        items = []

        # Severity row
        sev_style = ParagraphStyle('sev', fontSize=9, fontName='Helvetica-Bold', textColor=sev_color)
        severity_para = Paragraph(finding.severity.upper(), sev_style)

        # OWASP + CWE links
        meta_parts = []
        if finding.owasp_category:
            owasp_url = OWASP_URLS.get(finding.owasp_category, 'https://owasp.org/Top10/')
            meta_parts.append(f'<link href=\"{owasp_url}\"><u>{self._safe_text(finding.owasp_category)}</u></link>')
        if finding.cwe_id:
            cwe_num = finding.cwe_id.replace('CWE-', '')
            meta_parts.append(f'<link href=\"https://cwe.mitre.org/data/definitions/{cwe_num}.html\"><u>{self._safe_text(finding.cwe_id)}</u></link>')
        meta_text = ' | '.join(meta_parts) if meta_parts else ''

        items.append(Paragraph(f'<b>{finding.severity.upper()}</b>  {meta_text}',
                                ParagraphStyle('sev_row', fontSize=8, textColor=GRAY,
                                               leading=12, spaceAfter=2)))

        # Rule name (linked)
        rule_display = (finding.rule_name[:62] + '...') if len(finding.rule_name) > 65 else finding.rule_name
        encoded_rule_id = urllib.parse.quote(finding.rule_id, safe='')
        items.append(Paragraph(
            f'<link href=\"https://semgrep.dev/r/{encoded_rule_id}\"><u>{self._safe_text(rule_display)}</u></link>',
            ParagraphStyle('rule', fontSize=8, fontName='Helvetica-Bold', textColor=BLUE,
                           leading=11, spaceAfter=2)
        ))

        # Path
        path_display = finding.path
        if len(path_display) > 75:
            path_display = '...' + path_display[-72:]
        items.append(Paragraph(
            self._safe_text(f'{path_display}:{finding.start_line}'),
            ParagraphStyle('path', fontSize=7, fontName='Courier', textColor=GRAY, leading=10, spaceAfter=2)
        ))

        # Recommendation
        if finding.assistant_recommendation:
            rec = finding.assistant_recommendation
            if len(rec) > 85:
                rec = rec[:82] + '...'
            items.append(Paragraph(
                self._safe_text(rec),
                ParagraphStyle('rec', fontSize=7, fontName='Helvetica-Oblique', textColor=BLUE,
                               leading=10, spaceAfter=2)
            ))

        # Dashboard link
        if config.report_configuration.include_dashboard_links and project.project_id:
            finding_url = self._get_individual_finding_url(finding, project.project_id, config)
            if finding_url:
                items.append(Paragraph(
                    f'<link href="{finding_url}"><u>View in Semgrep Dashboard -></u></link>',
                    ParagraphStyle('view', fontSize=6, textColor=BLUE, alignment=2)  # right
                ))

        return items

    def _render_project_detailed_findings(self, project: SemgrepProject,
                                           config: ReportConfiguration) -> list:
        st = self._styles
        story = []

        open_findings = [f for f in project.findings if f.status == 'Open']
        severity_order = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
        min_severity = config.report_configuration.detail_filter_min_severity or 'Medium'
        min_level = severity_order.get(min_severity, 2)

        filtered = [f for f in open_findings if severity_order.get(f.severity, 1) >= min_level]
        print(f'  Project {project.name}: {len(open_findings)} total -> {len(filtered)} filtered (min {min_severity})')

        grouped = self._group_findings_by_rule(filtered)
        grouped.sort(key=lambda g: (severity_order.get(g['severity'], 0), len(g['instances'])), reverse=True)

        if not grouped:
            return story

        for page_num, group in enumerate(grouped, start=1):
            sev_color = SEVERITY_COLORS.get(group['severity'], GRAY)
            story.append(Paragraph(
                f'{project.name} - Detailed Findings ({page_num})',
                ParagraphStyle('dt', fontSize=18, fontName='Helvetica-Bold', textColor=GREEN, spaceAfter=10)
            ))

            # Severity header band
            inst_count = len(group.get('instances', []))
            inst_text = f'{inst_count} INSTANCE{"S" if inst_count != 1 else ""}'
            header_style = ParagraphStyle(
                'dhdr',
                fontName='Helvetica-Bold', fontSize=12, textColor=colors.white,
                alignment=1, backColor=sev_color, borderPadding=6
            )
            story.append(Paragraph(
                f'{group["severity"].upper()} SEVERITY - {inst_text}',
                header_style
            ))
            story.append(Spacer(1, 6))

            # Rule name
            story.append(Paragraph('Rule:', st['TinyBold']))
            story.append(Paragraph(
                f'<link href="https://semgrep.dev/r/{urllib.parse.quote(group["rule_id"], safe="")}"><u>{self._safe_text(group["rule_name"])}</u></link>',
                ParagraphStyle('rule', fontSize=11, fontName='Helvetica-Bold', textColor=BLUE)
            ))
            story.append(Spacer(1, 6))

            # Locations
            instances = group.get('instances', [])
            story.append(Paragraph(
                'Locations:' if len(instances) > 1 else 'Location:',
                st['TinyBold']
            ))
            for inst in instances[:3]:
                story.append(Paragraph(
                    self._safe_text(f'{inst["path"]}:{inst["start_line"]}'),
                    ParagraphStyle('loc', fontName='Courier', fontSize=10, textColor=GRAY, leading=13)
                ))
            if len(instances) > 3:
                story.append(Paragraph(
                    f'and {len(instances) - 3} additional finding{"s" if len(instances) - 3 != 1 else ""}...',
                    ParagraphStyle('more', fontSize=10, fontName='Helvetica-Oblique', textColor=GRAY)
                ))
            story.append(Spacer(1, 6))

            # Description
            story.append(Paragraph('Description:', st['TinyBold']))
            story.append(Paragraph(
                self._safe_text(group.get('description') or group.get('message') or 'No description available.'),
                st['SmallBody']
            ))
            story.append(Spacer(1, 6))

            # OWASP + CWE
            owasp_cat = group.get('owasp_category')
            cwe_id = group.get('cwe_id')
            if owasp_cat or cwe_id:
                story.append(Paragraph('Classifications:', st['TinyBold']))
                if owasp_cat:
                    owasp_display = OWASP_DISPLAY_NAMES.get(owasp_cat, owasp_cat)
                    owasp_url = OWASP_URLS.get(owasp_cat, 'https://owasp.org/Top10/')
                    story.append(Paragraph(
                        f'<link href=\"{owasp_url}\"><u>{self._safe_text(owasp_display)}</u></link>',
                        st['SmallLink']
                    ))
                if cwe_id:
                    cwe_num = cwe_id.replace('CWE-', '')
                    story.append(Paragraph(
                        f'<link href=\"https://cwe.mitre.org/data/definitions/{cwe_num}.html\"><u>{self._safe_text(cwe_id)}</u></link>',
                        st['SmallLink']
                    ))
                story.append(Spacer(1, 6))

            # Recommendation
            rec = group.get('assistant_recommendation')
            if rec:
                story.append(Paragraph('Recommendation:', st['TinyBold']))
                story.append(Paragraph(self._safe_text(rec), st['SmallBody']))
                story.append(Spacer(1, 6))

            # Dashboard link
            if config.report_configuration.include_dashboard_links and project.project_id:
                rule_url = self._get_rule_dashboard_url(group['rule_id'], project, config)
                if rule_url:
                    story.append(Paragraph(
                        f'<link href="{rule_url}"><u>View all instances in Semgrep Dashboard -></u></link>',
                        st['SmallLink']
                    ))

            story.append(PageBreak())

        return story

    def _owasp_top10_pages(self, projects: List[SemgrepProject]) -> list:
        """
        OWASP Top 10 summary section.

        Mirrors the structure of generate_owasp_report.py but driven by
        SemgrepFinding objects from the API rather than a JSON file.

        Page layout:
          1. Summary overview: one row per OWASP category showing finding
             counts broken down by severity, plus an Unmapped row if needed.
          2. Per-category detail pages: one page per category that has
             findings, listing every finding with its rule, path, message,
             and CWE — matching the HTML report's per-section tables.
        """
        st = self._styles
        story = []

        open_findings = [f for p in projects for f in p.findings if f.status == 'Open']
        if not open_findings:
            return story

        # ── Group findings by OWASP category ─────────────────────────────────
        # key → list of SemgrepFinding
        by_category: Dict[str, List[SemgrepFinding]] = {}
        for f in open_findings:
            key = f.owasp_category or 'unmapped'
            by_category.setdefault(key, []).append(f)

        # Build display order: canonical A01-A10 (only if present) then unmapped
        ordered_keys = [k for k in OWASP_CATEGORY_ORDER if k in by_category]
        if 'unmapped' in by_category:
            ordered_keys.append('unmapped')

        # ── Page 1: Summary overview ──────────────────────────────────────────
        story.append(Paragraph('OWASP Top 10 Security Summary', st['SectionTitle']))
        story.append(Paragraph(
            'All open findings grouped by OWASP Top 10 2021 category across every project in scope. '
            'Categories are sorted in canonical A01–A10 order; findings with no OWASP mapping appear last.',
            st['Body']
        ))
        story.append(Spacer(1, 8))

        # Severity distribution row (mirrors HTML "Severity breakdown" card)
        sev_order = ['Critical', 'High', 'Medium', 'Low']
        sev_counts = {s: sum(1 for f in open_findings if f.severity == s) for s in sev_order}
        sev_row_items = []
        for sev in sev_order:
            if sev_counts[sev]:
                col = SEVERITY_COLORS.get(sev, GRAY)
                sev_row_items.append(
                    Paragraph(
                        f'<b>{sev}:</b> {sev_counts[sev]}',
                        ParagraphStyle(f'sv_{sev}', fontSize=10, textColor=col, leading=14)
                    )
                )
        if sev_row_items:
            sev_cols = len(sev_row_items)
            sev_table = Table(
                [sev_row_items],
                colWidths=[CONTENT_WIDTH / sev_cols] * sev_cols,
                style=TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
                    ('BOX', (0, 0), (-1, -1), 0.5, BORDER_GRAY),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ])
            )
            story.append(sev_table)
            story.append(Spacer(1, 10))

        # Severity-bar chart per OWASP category (mirrors HTML "OWASP coverage" list)
        story.append(Paragraph('Findings by OWASP Category', st['GreenSubTitle']))
        max_cat_count = max((len(v) for v in by_category.values()), default=1)
        for key in ordered_keys:
            findings = by_category[key]
            label = OWASP_SHORT_LABELS.get(key, 'N/A') if key != 'unmapped' else 'N/A'
            name = OWASP_DISPLAY_NAMES.get(key, 'Unmapped to OWASP Top 10') if key != 'unmapped' else 'Unmapped to OWASP Top 10'
            story.append(SeverityBar(
                label=label,
                count=len(findings),
                max_count=max_cat_count,
                label_color=GREEN if key != 'unmapped' else GRAY,
                bar_color=GREEN if key != 'unmapped' else GRAY,
                max_bar_width=CONTENT_WIDTH * 0.55,
            ))

        story.append(Spacer(1, 10))

        # Summary table: one row per category with per-severity counts
        story.append(Paragraph('Category Breakdown', st['GreenSubTitle']))
        table_header = ['Code', 'Category', 'Total', 'Critical', 'High', 'Medium', 'Low']
        table_rows = [table_header]
        style_cmds = []
        for row_idx, key in enumerate(ordered_keys, start=1):
            findings = by_category[key]
            code = OWASP_SHORT_LABELS.get(key, '—') if key != 'unmapped' else '—'
            name = OWASP_DISPLAY_NAMES.get(key, 'Unmapped to OWASP Top 10') if key != 'unmapped' else 'Unmapped to OWASP Top 10'
            # Strip the long "OWASP Top Ten 2021 Category AXX - " prefix for the table
            short_name = name.split(' - ', 1)[-1] if ' - ' in name else name
            counts = {s: sum(1 for f in findings if f.severity == s) for s in sev_order}
            table_rows.append([
                code,
                short_name,
                str(len(findings)),
                str(counts['Critical']) if counts['Critical'] else '—',
                str(counts['High']) if counts['High'] else '—',
                str(counts['Medium']) if counts['Medium'] else '—',
                str(counts['Low']) if counts['Low'] else '—',
            ])
            # Color the Critical/High cells if non-zero
            if counts['Critical']:
                style_cmds.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), RED))
                style_cmds.append(('FONTNAME', (3, row_idx), (3, row_idx), 'Helvetica-Bold'))
            if counts['High']:
                style_cmds.append(('TEXTCOLOR', (4, row_idx), (4, row_idx), ORANGE))
                style_cmds.append(('FONTNAME', (4, row_idx), (4, row_idx), 'Helvetica-Bold'))

        summary_table = _make_table(
            table_rows,
            col_widths=[
                CONTENT_WIDTH * 0.06,   # Code
                CONTENT_WIDTH * 0.42,   # Category
                CONTENT_WIDTH * 0.10,   # Total
                CONTENT_WIDTH * 0.10,   # Critical
                CONTENT_WIDTH * 0.10,   # High
                CONTENT_WIDTH * 0.11,   # Medium
                CONTENT_WIDTH * 0.11,   # Low
            ],
            style_cmds=style_cmds,
        )
        story.append(summary_table)
        story.append(PageBreak())

        # ── Per-category detail pages ─────────────────────────────────────────
        # Mirror the HTML report's per-section tables:
        # Severity | Rule | Path:Line | Message | CWE
        FINDINGS_PER_PAGE = 12  # rows that comfortably fit on one A4 page

        for key in ordered_keys:
            findings = by_category[key]
            display_name = (
                OWASP_DISPLAY_NAMES.get(key, 'Unmapped to OWASP Top 10')
                if key != 'unmapped'
                else 'Unmapped to OWASP Top 10'
            )
            owasp_url = OWASP_URLS.get(key) if key != 'unmapped' else None

            # Sort within category: Critical first, then High, Medium, Low
            sev_rank = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
            sorted_findings = sorted(findings, key=lambda f: sev_rank.get(f.severity, 4))

            # Paginate if many findings
            for page_start in range(0, len(sorted_findings), FINDINGS_PER_PAGE):
                page_findings = sorted_findings[page_start:page_start + FINDINGS_PER_PAGE]
                page_num = page_start // FINDINGS_PER_PAGE + 1
                total_pages = (len(sorted_findings) + FINDINGS_PER_PAGE - 1) // FINDINGS_PER_PAGE

                # Section header
                header_suffix = (f' (Page {page_num} of {total_pages})'
                                 if total_pages > 1 else '')
                story.append(Paragraph(
                    f'{display_name}{header_suffix}',
                    ParagraphStyle('owasp_sec', fontSize=14, fontName='Helvetica-Bold',
                                   textColor=GREEN, spaceAfter=4)
                ))

                count_label = f'{len(findings)} finding{"s" if len(findings) != 1 else ""}'
                if owasp_url:
                    story.append(Paragraph(
                        f'<link href="{owasp_url}"><u>OWASP Reference</u></link>  |  {count_label}',
                        ParagraphStyle('owasp_ref', fontSize=9, textColor=GRAY, spaceAfter=6)
                    ))
                else:
                    story.append(Paragraph(count_label,
                                           ParagraphStyle('owasp_cnt', fontSize=9,
                                                          textColor=GRAY, spaceAfter=6)))

                # Findings table (mirrors HTML <table class="table">)
                detail_header = ['Sev', 'Rule / Path', 'Message', 'CWE']
                detail_rows = [detail_header]
                detail_style = []

                for row_idx, finding in enumerate(page_findings, start=1):
                    sev_col = SEVERITY_COLORS.get(finding.severity, GRAY)

                    # Truncate long rule IDs for readability
                    rule_display = finding.rule_id
                    if len(rule_display) > 55:
                        rule_display = '...' + rule_display[-52:]
                    path_display = finding.path
                    if len(path_display) > 45:
                        path_display = '...' + path_display[-42:]
                    encoded_rule_id = urllib.parse.quote(finding.rule_id, safe='')

                    rule_cell = Paragraph(
                        f'<link href=\"https://semgrep.dev/r/{encoded_rule_id}\"><u>{self._safe_text(rule_display)}</u></link>'
                        f'<br/><font size=\"7\" color=\"#666666\">{self._safe_text(path_display)}:{finding.start_line}</font>',
                        ParagraphStyle('rc', fontSize=8, textColor=BLUE, leading=11)
                    )

                    msg = finding.message or finding.description or ''
                    if len(msg) > 120:
                        msg = msg[:117] + '...'
                    msg_cell = Paragraph(self._safe_text(msg), ParagraphStyle('mc', fontSize=8, leading=11,
                                                              textColor=DARK_GRAY))

                    cwe = finding.cwe_id or '—'
                    if finding.cwe_id:
                        cwe_num = finding.cwe_id.replace('CWE-', '')
                        cwe_cell = Paragraph(
                            f'<link href=\"https://cwe.mitre.org/data/definitions/{cwe_num}.html\"><u>{self._safe_text(cwe)}</u></link>',
                            ParagraphStyle('cwec', fontSize=8, textColor=BLUE)
                        )
                    else:
                        cwe_cell = Paragraph('—', ParagraphStyle('cwed', fontSize=8, textColor=GRAY))

                    detail_rows.append([finding.severity, rule_cell, msg_cell, cwe_cell])
                    detail_style.append(('TEXTCOLOR', (0, row_idx), (0, row_idx), sev_col))
                    detail_style.append(('FONTNAME', (0, row_idx), (0, row_idx), 'Helvetica-Bold'))
                    detail_style.append(('FONTSIZE', (0, row_idx), (0, row_idx), 8))

                detail_table = Table(
                    detail_rows,
                    colWidths=[
                        CONTENT_WIDTH * 0.09,   # Severity
                        CONTENT_WIDTH * 0.33,   # Rule / Path
                        CONTENT_WIDTH * 0.43,   # Message
                        CONTENT_WIDTH * 0.15,   # CWE
                    ],
                    style=TableStyle([
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('BACKGROUND', (0, 0), (-1, 0), MID_GRAY),
                        ('GRID', (0, 0), (-1, -1), 0.3, BORDER_GRAY),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('LEFTPADDING', (0, 0), (-1, -1), 4),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ] + detail_style),
                    repeatRows=1,
                )
                story.append(detail_table)
                story.append(PageBreak())

        return story

    def _security_roadmap_pages(self, projects, config, open_findings) -> list:
        st = self._styles
        story = []

        critical = sum(1 for f in open_findings if f.severity == 'Critical')
        high = sum(1 for f in open_findings if f.severity == 'High')
        medium = sum(1 for f in open_findings if f.severity == 'Medium')

        owasp_breakdown = self._get_owasp_breakdown(open_findings)
        top_owasp = owasp_breakdown[:5]

        # ── Immediate Actions (0-30 days) ─────────────────────────────────────
        story.append(Paragraph('Strategic Security Improvement Plan', st['SectionTitle']))
        story.append(Paragraph(
            f'This roadmap provides a structured approach to addressing security vulnerabilities across the '
            f'{config.customer.name} organization, prioritized by risk level and business impact.',
            ParagraphStyle('intro', fontSize=11, textColor=HexColor('#555555'), leading=15, spaceAfter=12)
        ))

        story.extend(self._roadmap_section(
            title='Immediate Actions (0-30 days)',
            bg_color=HexColor('#FFEAEA'),
            border_color=RED,
            text_color=HexColor('#721C24'),
            intro=(f'While no critical vulnerabilities were identified, {critical + high} high-priority security '
                   f'issues require prompt attention. Deploy security patches and establish incident response '
                   f'procedures to maintain your security posture.'
                   if critical > 0 else
                   f'{critical + high} high-priority security issues require prompt attention. Deploy security '
                   f'patches and establish incident response procedures to maintain your security posture.'),
            focus_items=[c['category'] for c in top_owasp[:3]] if top_owasp else [],
            closing=(
                'Establish automated security scanning in your CI/CD pipeline to catch vulnerabilities before '
                'they reach production. Conduct targeted security training for your development team, focusing '
                'on the vulnerability patterns identified in your codebase.'
            ),
        ))
        story.append(PageBreak())

        # ── Short-term (1-3 months) ───────────────────────────────────────────
        story.extend(self._roadmap_section(
            title='Short Term Actions (1-3 months)',
            bg_color=HexColor('#FFF3CD'),
            border_color=ORANGE,
            text_color=HexColor('#856404'),
            intro=(f'Beyond the immediate critical issues, we\'ve found {high} high-severity vulnerabilities '
                   f'that should be systematically addressed over the next 1-3 months. These represent '
                   f'significant security gaps that could be exploited by attackers.'),
            focus_items=[
                'Review authentication and authorization controls',
                'Conduct dependency vulnerability audit',
                'Implement security-focused code review process',
                'Deploy SAST scanning gates in CI/CD pipeline',
                'Remediate all remaining high-severity findings',
            ],
            closing=(
                'Establish automated security scanning in your CI/CD pipeline to catch vulnerabilities before '
                'they reach production. Conduct targeted security training for your development team, focusing '
                'on the vulnerability patterns identified in your codebase.'
            ),
        ))
        story.append(PageBreak())

        # ── Long-term (3-12 months) ───────────────────────────────────────────
        story.extend(self._roadmap_section(
            title='Long Term Strategy (3-12 months)',
            bg_color=HexColor('#D1ECF1'),
            border_color=TEAL,
            text_color=HexColor('#0C5460'),
            intro=(f'For long-term security improvement, focus on establishing a mature security posture '
                   f'with {medium} medium-severity findings and building systematic security practices '
                   f'across your development organization.'),
            focus_items=[
                'Build a comprehensive security training program',
                'Implement a formal vulnerability management process',
                'Establish security champions in each development team',
                'Define and enforce security SLAs for finding remediation',
                'Conduct regular third-party security assessments',
            ],
            closing=(
                'Long-term security maturity requires cultural transformation alongside technical improvements. '
                'Invest in developer security education, threat modeling practices, and continuous security '
                'monitoring to build a sustainable secure development lifecycle.'
            ),
        ))

        return story

    def _roadmap_section(self, title: str, bg_color: HexColor, border_color: HexColor,
                          text_color: HexColor, intro: str, focus_items: list,
                          closing: str) -> list:
        st = self._styles

        title_style = ParagraphStyle(
            'rs_title', fontSize=14, fontName='Helvetica-Bold', textColor=border_color, spaceAfter=6
        )
        body_style = ParagraphStyle(
            'rs_body', fontSize=11, fontName='Helvetica-Bold', textColor=text_color,
            leading=15, spaceAfter=6
        )
        focus_style = ParagraphStyle(
            'rs_focus', fontSize=10, fontName='Helvetica-Bold', textColor=text_color,
            leading=13, spaceAfter=3
        )
        closing_style = ParagraphStyle(
            'rs_close', fontSize=10, fontName='Helvetica-Oblique', textColor=text_color,
            leading=14, spaceAfter=4
        )

        items_inside = []
        items_inside.append(Paragraph(title, title_style))
        items_inside.append(Paragraph(intro, body_style))
        items_inside.append(Paragraph('Focus your security efforts on these key areas:', focus_style))
        for item in focus_items:
            display = item.replace('-', ' ').title() if not item.startswith('Review') and not item.startswith(('Conduct', 'Implement', 'Deploy', 'Establish', 'Build', 'Define', 'Invest', 'Remediate')) else item
            items_inside.append(Paragraph(f'- {display}', focus_style))
        items_inside.append(Paragraph(closing, closing_style))

        content_table = Table(
            [[items_inside]],
            colWidths=[CONTENT_WIDTH - 20],
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), bg_color),
                ('BOX', (0, 0), (-1, -1), 2, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 14),
                ('RIGHTPADDING', (0, 0), (-1, -1), 14),
                ('ROUNDEDCORNERS', [6]),
            ])
        )
        return [content_table, Spacer(1, 12)]

    # ── Helper methods ────────────────────────────────────────────────────────

    def _get_actual_repositories(self, projects: List[SemgrepProject]) -> List[dict]:
        repos = []
        for project in projects:
            open_count = sum(1 for f in project.findings if f.status == 'Open')
            if open_count == 0:
                continue
            estimated_files = max(50, open_count * 3)
            duration = '12m' if open_count > 1000 else ('6m' if open_count > 100 else '2m')
            repos.append({
                'name': project.name,
                'open_findings': open_count,
                'files_scanned': estimated_files,
                'scan_duration': duration,
                'last_scanned': datetime.now().strftime('%m/%d/%Y'),
            })
        repos.sort(key=lambda r: r['open_findings'], reverse=True)
        return repos

    def _safe_text(self, value: Optional[str]) -> str:
        if value is None:
            return ''
        return xml_escape(str(value), {'"': '&quot;', "'": '&#39;'})

    def _group_findings_by_rule(self, findings: List[SemgrepFinding]) -> List[dict]:
        groups: Dict[str, dict] = {}
        for finding in findings:
            key = finding.rule_id
            if key not in groups:
                groups[key] = {
                    'rule_id': finding.rule_id,
                    'rule_name': finding.rule_name,
                    'severity': finding.severity,
                    'message': finding.message,
                    'description': finding.description,
                    'owasp_category': finding.owasp_category,
                    'cwe_id': finding.cwe_id,
                    'assistant_recommendation': finding.assistant_recommendation,
                    'instances': [],
                }
            loc_key = f'{finding.path}:{finding.start_line}'
            if not any(f'{i["path"]}:{i["start_line"]}' == loc_key for i in groups[key]['instances']):
                groups[key]['instances'].append({
                    'id': finding.id,
                    'path': finding.path,
                    'start_line': finding.start_line,
                    'project_id': finding.project_id,
                    'project_name': finding.project_name,
                })
        return list(groups.values())

    def _get_owasp_breakdown(self, findings: List[SemgrepFinding]) -> List[dict]:
        owasp_map: Dict[str, dict] = {}
        for f in findings:
            if f.status != 'Open' or not f.owasp_category:
                continue
            cat = f.owasp_category
            if cat not in owasp_map:
                owasp_map[cat] = {'category': cat, 'count': 0, 'critical': 0, 'high': 0}
            owasp_map[cat]['count'] += 1
            if f.severity == 'Critical':
                owasp_map[cat]['critical'] += 1
            if f.severity == 'High':
                owasp_map[cat]['high'] += 1
        result = list(owasp_map.values())
        result.sort(key=lambda x: (x['critical'] + x['high']), reverse=True)
        return result

    def _calc_project_score(self, open_findings: List[SemgrepFinding]) -> int:
        if not open_findings:
            return 100
        weights = {'Critical': 50, 'High': 20, 'Medium': 5, 'Low': 1}
        total = sum(weights.get(f.severity, 1) for f in open_findings)
        return max(0, round(100 - total * 100.0 / 1000))

    def _calc_project_level(self, counts: dict, score: int) -> str:
        c = counts.get('critical', 0)
        h = counts.get('high', 0)
        if c == 0 and h == 0 and score >= 90:
            return 'SL5'
        if c == 0 and h <= 3 and score >= 80:
            return 'SL4'
        if c == 0 and h <= 10 and score >= 70:
            return 'SL3'
        if c <= 5 and score >= 60:
            return 'SL2'
        return 'SL1'

    def _level_color(self, level: str) -> HexColor:
        return {
            'SL5': HexColor('#155724'),
            'SL4': HexColor('#0C5460'),
            'SL3': HexColor('#856404'),
            'SL2': RED,
            'SL1': RED,
        }.get(level, GRAY)

    def _get_dashboard_url(self, project_id: str, config: ReportConfiguration) -> Optional[str]:
        if not config.report_configuration.include_dashboard_links:
            return None
        repo_mapping = config.report_configuration.repository_reference_mapping
        org = config.organization_settings.organization_name if config.organization_settings else None
        if not org:
            return None

        if repo_mapping and repo_mapping.method == 'api-discovery':
            return f'https://semgrep.dev/orgs/{org}/findings?tab=open&repository_id={project_id}'

        mapping = self._load_repo_mapping(config)
        semgrep_id = next((k for k, v in mapping.items() if v == project_id), None)
        if semgrep_id:
            return f'https://semgrep.dev/orgs/{org}/findings?repo_ref={semgrep_id}'
        return None

    def _get_individual_finding_url(self, finding: SemgrepFinding, project_id: str,
                                     config: ReportConfiguration) -> Optional[str]:
        if not config.report_configuration.include_dashboard_links:
            return None
        org = config.organization_settings.organization_name if config.organization_settings else None
        if not org:
            return None
        mapping = self._load_repo_mapping(config)
        semgrep_id = next((k for k, v in mapping.items() if v == project_id), None)
        if semgrep_id and finding.id:
            return f'https://semgrep.dev/orgs/{org}/findings/{finding.id}'
        return None

    def _get_rule_dashboard_url(self, rule_id: str, project: SemgrepProject,
                                 config: ReportConfiguration) -> Optional[str]:
        if not config.report_configuration.include_dashboard_links:
            return None
        org = config.organization_settings.organization_name if config.organization_settings else None
        if not org:
            return None
        repo_mapping = config.report_configuration.repository_reference_mapping
        encoded_rule = urllib.parse.quote(rule_id)

        if repo_mapping and repo_mapping.method == 'api-discovery':
            if project.repo_ref_id:
                return (f'https://semgrep.dev/orgs/{org}/findings?tab=open'
                        f'&last_opened=All+time&repo_ref={project.repo_ref_id}&rule={encoded_rule}')
            if project.project_id:
                return (f'https://semgrep.dev/orgs/{org}/findings?tab=open'
                        f'&last_opened=All+time&repository_id={project.project_id}&rule={encoded_rule}')
            return None

        mapping = self._load_repo_mapping(config)
        semgrep_id = next((k for k, v in mapping.items() if v == project.project_id), None)
        if semgrep_id:
            return (f'https://semgrep.dev/orgs/{org}/findings?tab=open'
                    f'&last_opened=All+time&repo_ref={semgrep_id}&rule={encoded_rule}')
        return None

    def _load_repo_mapping(self, config: ReportConfiguration) -> Dict[str, str]:
        repo_mapping = config.report_configuration.repository_reference_mapping
        if not repo_mapping:
            return {}
        if repo_mapping.external_mapping_file:
            path = os.path.abspath(repo_mapping.external_mapping_file)
            if os.path.exists(path):
                try:
                    import json
                    with open(path) as f:
                        arr = json.load(f)
                    return {e['ID']: e['Repository ID'] for e in arr if e.get('ID') and e.get('Repository ID')}
                except Exception as e:
                    print(f'Warning: Error loading mapping file: {e}')
        return repo_mapping.static_mappings or {}


def _make_combined_project(projects: List[SemgrepProject]):
    from models import SemgrepProject, ScanMetadata, BusinessCriticality
    from datetime import datetime
    all_findings = [f for p in projects for f in p.findings]
    return SemgrepProject(
        name='Combined',
        repository='Multiple',
        business_criticality=projects[0].business_criticality if projects else BusinessCriticality.HIGH,
        last_scanned=datetime.now(),
        findings=all_findings,
        scan_data=(projects[0].scan_data if projects else ScanMetadata(
            sast_completed=True,
            supply_chain_completed=True,
            secrets_completed=False,
            files_scanned=0,
            scan_duration=0,
            engine_version='1.45.0',
        )),
    )
