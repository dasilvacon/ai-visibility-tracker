"""
PDF export for executive summary.
Creates a clean 2-page summary for stakeholders.
"""

import os
from typing import Dict, List, Any
from datetime import datetime

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Frame, PageTemplate
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class PDFExporter:
    """Generates executive summary PDF."""

    def __init__(self, reports_dir: str):
        # DaSilva brand colors
        if REPORTLAB_AVAILABLE:
            self.DEEP_PLUM = colors.HexColor('#402E3A')
            self.DUSTY_ROSE = colors.HexColor('#A78E8B')
            self.CHARCOAL = colors.HexColor('#1C1C1C')
            self.OFF_WHITE = colors.HexColor('#FBFBEF')
            self.ACCENT_PINK = colors.HexColor('#D4698B')
        else:
            self.DEEP_PLUM = None
            self.DUSTY_ROSE = None
            self.CHARCOAL = None
            self.OFF_WHITE = None
            self.ACCENT_PINK = None

        """Initialize PDF exporter.

        Args:
            reports_dir: Directory to save PDF exports
        """
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)

        if not REPORTLAB_AVAILABLE:
            print("⚠️  reportlab not installed. PDF export disabled.")
            print("   Install with: pip install reportlab")

    def generate_executive_summary(self, brand_name: str,
                                   visibility_summary: Dict[str, Any],
                                   competitive_analysis: Dict[str, Any],
                                   gap_analysis: Dict[str, Any],
                                   source_analysis: Dict[str, Any]) -> str:
        """
        Generate 2-page executive summary PDF.

        Args:
            brand_name: Brand name
            visibility_summary: Visibility summary statistics
            competitive_analysis: Competitive analysis data
            gap_analysis: Gap analysis with opportunities
            source_analysis: Source analysis data

        Returns:
            Path to generated PDF
        """
        if not REPORTLAB_AVAILABLE:
            print("Cannot generate PDF: reportlab not installed")
            return ""

        pdf_path = os.path.join(
            self.reports_dir,
            f'executive_summary_{brand_name.replace(" ", "_")}.pdf'
        )

        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        # Container for PDF elements
        elements = []

        # Build page 1
        elements.extend(self._build_page1(
            brand_name, visibility_summary, competitive_analysis
        ))

        # Page break
        elements.append(PageBreak())

        # Build page 2
        elements.extend(self._build_page2(
            brand_name, gap_analysis, source_analysis
        ))

        # Generate PDF
        doc.build(elements)

        return pdf_path

    def _build_page1(self, brand_name: str,
                    visibility_summary: Dict[str, Any],
                    competitive_analysis: Dict[str, Any]) -> List:
        """Build page 1 of executive summary."""
        elements = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=self.DEEP_PLUM,
            spaceAfter=6,
            alignment=TA_LEFT
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=self.DUSTY_ROSE,
            spaceAfter=20
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=self.DEEP_PLUM,
            spaceAfter=12,
            spaceBefore=20
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            textColor=self.CHARCOAL,
            spaceAfter=12,
            leading=14
        )

        # Header
        elements.append(Paragraph(f"AI Visibility Analysis", title_style))
        elements.append(Paragraph(
            f"{brand_name} • {datetime.now().strftime('%B %d, %Y')}",
            subtitle_style
        ))

        # Key metrics cards
        vis_rate = visibility_summary.get('brand_visibility_rate', 0)
        prom_score = visibility_summary.get('average_prominence_score', 0)
        queries_tested = visibility_summary.get('total_prompts_tested', 0)

        # Get top competitor
        top_comp_name = "N/A"
        top_comp_rate = 0
        competitors = competitive_analysis.get('top_competitors', [])
        if competitors:
            top_comp_name = competitors[0]['name']
            top_comp_rate = competitors[0]['mention_rate']

        metrics_data = [
            ['Your Visibility', 'Top Competitor', 'Queries Tested'],
            [f'{vis_rate:.1f}%', f'{top_comp_name}\n{top_comp_rate:.1f}%', str(queries_tested)]
        ]

        metrics_table = Table(metrics_data, colWidths=[2.2*inch, 2.2*inch, 2.2*inch])
        metrics_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), self.DEEP_PLUM),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),

            # Data row
            ('BACKGROUND', (0, 1), (-1, 1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, 1), self.CHARCOAL),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 18),
            ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
            ('TOPPADDING', (0, 1), (-1, 1), 12),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 12),

            # Grid
            ('GRID', (0, 0), (-1, -1), 1, self.DUSTY_ROSE),
            ('BOX', (0, 0), (-1, -1), 2, self.DEEP_PLUM),
        ]))

        elements.append(metrics_table)
        elements.append(Spacer(1, 20))

        # Executive summary paragraph
        gap = top_comp_rate - vis_rate
        summary_text = f"""
        <b>Summary:</b> {brand_name} appears in {vis_rate:.1f}% of AI responses about luxury eyeshadow.
        {top_comp_name} leads at {top_comp_rate:.1f}%, creating a {gap:.1f}-point gap.
        Based on {queries_tested} queries tested across multiple personas and use cases,
        there are clear opportunities to improve visibility through targeted content creation.
        """

        elements.append(Paragraph(summary_text, body_style))
        elements.append(Spacer(1, 12))

        # Competitive landscape
        elements.append(Paragraph("Competitive Landscape", heading_style))

        if competitors:
            comp_data = [['Competitor', 'Mention Rate', 'Gap vs You']]
            for comp in competitors[:5]:  # Top 5 competitors
                comp_gap = comp['mention_rate'] - vis_rate
                comp_data.append([
                    comp['name'],
                    f"{comp['mention_rate']:.1f}%",
                    f"{comp_gap:+.1f}%"
                ])

            comp_table = Table(comp_data, colWidths=[3*inch, 1.8*inch, 1.8*inch])
            comp_table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), self.DEEP_PLUM),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
                ('ALIGN', (1, 0), (-1, 0), 'CENTER'),

                # Data rows
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),

                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.OFF_WHITE]),

                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, self.DUSTY_ROSE),
                ('BOX', (0, 0), (-1, -1), 1, self.DEEP_PLUM),
            ]))

            elements.append(comp_table)

        return elements

    def _build_page2(self, brand_name: str,
                    gap_analysis: Dict[str, Any],
                    source_analysis: Dict[str, Any]) -> List:
        """Build page 2 of executive summary."""
        elements = []
        styles = getSampleStyleSheet()

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=self.DEEP_PLUM,
            spaceAfter=12,
            spaceBefore=8
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=9,
            textColor=self.CHARCOAL,
            spaceAfter=8,
            leading=12
        )

        # Top 3 Actions
        elements.append(Paragraph("Top 3 Priority Actions", heading_style))

        opportunities = gap_analysis.get('priority_opportunities', [])
        for i, opp in enumerate(opportunities[:3], 1):
            priority = opp.get('priority', 'MEDIUM')
            gap = opp.get('gap', 0)

            action_text = f"""
            <b>{i}. {opp.get('target', 'Opportunity')} [{priority} PRIORITY]</b><br/>
            <i>Gap: {gap:.1f}% | Impact: ~{opp.get('missed_monthly', 0)} monthly mentions</i><br/>
            """

            # Add top 2 actions
            actions = opp.get('specific_actions', [])
            for action in actions[:2]:
                action_text += f"• {action}<br/>"

            elements.append(Paragraph(action_text, body_style))
            elements.append(Spacer(1, 8))

        # Sources to target
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("Sources to Target", heading_style))

        targets = source_analysis.get('recommended_targets', [])
        if targets:
            source_data = [['Source', 'Your Brand', 'Competitors', 'Priority']]

            for target in targets[:5]:  # Top 5 sources
                priority = 'HIGH' if target['opportunity_score'] >= 60 else 'MEDIUM'
                source_data.append([
                    target['source'],
                    f"{target['brand_mention_rate']:.0f}%",
                    f"{target['competitor_rate']:.0f}%",
                    priority
                ])

            source_table = Table(source_data, colWidths=[2.5*inch, 1.4*inch, 1.4*inch, 1.3*inch])
            source_table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), self.DEEP_PLUM),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (-1, 0), 'CENTER'),

                # Data rows
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),

                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.OFF_WHITE]),

                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, self.DUSTY_ROSE),
                ('BOX', (0, 0), (-1, -1), 1, self.DEEP_PLUM),
            ]))

            elements.append(source_table)
        else:
            elements.append(Paragraph(
                "No major source gaps identified. You're present where competitors appear.",
                body_style
            ))

        # Footer
        elements.append(Spacer(1, 20))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=self.DUSTY_ROSE,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            f"Full interactive report available: visibility_report_{brand_name.replace(' ', '_')}.html",
            footer_style
        ))

        return elements
