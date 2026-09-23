# server/src/analytics/services/pdf_exporter.py
"""
Premium PDF export for analytics dashboard.
Enterprise-grade reports with cover page, TOC, mini charts, and rich data.
"""

from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.graphics.charts.barcharts import VerticalBarChart, HorizontalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BRAND_PRIMARY = colors.HexColor("#007AFF")  # Apple blue
BRAND_SECONDARY = colors.HexColor("#5856D6")  # Purple
BRAND_ACCENT = colors.HexColor("#0056CC")  # Deep blue

TEXT_HEADING = colors.HexColor("#1D1D1F")  # Near black
TEXT_BODY = colors.HexColor("#3C3C43")  # Dark gray
TEXT_MUTED = colors.HexColor("#6E6E73")  # Medium gray
TEXT_LIGHT = colors.HexColor("#86868B")  # Light gray

BG_CARD = colors.HexColor("#FFFFFF")
BG_SUBTLE = colors.HexColor("#F5F5F7")  # Apple gray
BG_ZEBRA = colors.HexColor("#FAFAFA")  # Even lighter

BORDER_LIGHT = colors.HexColor("#E5E5EA")
BORDER_MEDIUM = colors.HexColor("#D1D1D6")

# Semantic colors
COLOR_SUCCESS = colors.HexColor("#34C759")  # iOS green
COLOR_WARNING = colors.HexColor("#FF9500")  # iOS orange
COLOR_DANGER = colors.HexColor("#FF3B30")  # iOS red
COLOR_INFO = colors.HexColor("#5AC8FA")  # iOS light blue

# Severity colors
SEV_BLOCKED = colors.HexColor("#FF3B30")
SEV_FLAGGED = colors.HexColor("#FF9500")
SEV_WARN = colors.HexColor("#FFCC00")
SEV_INFO = colors.HexColor("#007AFF")


def _get_styles():
    """Custom paragraph styles — Apple-inspired typography."""
    styles = getSampleStyleSheet()

    # ── Cover page styles ────────────────────────────────────────────────
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Heading1"],
            fontSize=42,
            leading=48,
            textColor=TEXT_HEADING,
            alignment=TA_CENTER,
            spaceAfter=8,
            fontName="Helvetica-Bold",
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverSubtitle",
            parent=styles["Normal"],
            fontSize=16,
            leading=20,
            textColor=TEXT_MUTED,
            alignment=TA_CENTER,
            spaceAfter=40,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverMeta",
            parent=styles["Normal"],
            fontSize=11,
            textColor=TEXT_LIGHT,
            alignment=TA_CENTER,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverBrand",
            parent=styles["Normal"],
            fontSize=13,
            textColor=BRAND_PRIMARY,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            spaceAfter=6,
        )
    )

    # ── Section headings ─────────────────────────────────────────────────
    styles.add(
        ParagraphStyle(
            name="H1",
            parent=styles["Heading1"],
            fontSize=24,
            leading=28,
            textColor=TEXT_HEADING,
            spaceAfter=8,
            fontName="Helvetica-Bold",
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2",
            parent=styles["Heading2"],
            fontSize=16,
            leading=20,
            textColor=TEXT_HEADING,
            spaceAfter=6,
            spaceBefore=18,
            fontName="Helvetica-Bold",
        )
    )
    styles.add(
        ParagraphStyle(
            name="H3",
            parent=styles["Heading3"],
            fontSize=13,
            leading=16,
            textColor=TEXT_HEADING,
            spaceAfter=4,
            spaceBefore=10,
            fontName="Helvetica-Bold",
        )
    )

    # ── Body text ────────────────────────────────────────────────────────
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=TEXT_BODY,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Muted",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=TEXT_MUTED,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=TEXT_LIGHT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Meta",
            parent=styles["Normal"],
            fontSize=9,
            textColor=TEXT_MUTED,
            alignment=TA_CENTER,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubtitleWithBrand",
            parent=styles["Normal"],
            fontSize=11,
            textColor=TEXT_MUTED,
            spaceAfter=16,
        )
    )

    return styles


def _build_cover_page(
    styles, title: str, subtitle: str, date_range_label: str, tab_name: str
) -> list:
    """Beautiful cover page with brand element."""
    elements = []

    # Top spacer
    elements.append(Spacer(1, 4 * cm))

    # Brand mark (colored bar)
    brand_bar = Drawing(A4[0] - 4 * cm, 8)
    brand_bar.add(
        Rect(
            0, 0, (A4[0] - 4 * cm) * 0.15, 8, fillColor=BRAND_PRIMARY, strokeColor=None
        )
    )
    brand_bar.add(
        Rect(
            (A4[0] - 4 * cm) * 0.15,
            0,
            (A4[0] - 4 * cm) * 0.85,
            8,
            fillColor=BRAND_SECONDARY,
            strokeColor=None,
            fillOpacity=0.3,
        )
    )
    elements.append(brand_bar)
    elements.append(Spacer(1, 0.6 * cm))

    # Brand name
    elements.append(Paragraph("TRUSTSHARE", styles["CoverBrand"]))
    elements.append(Spacer(1, 0.3 * cm))

    # Main title
    elements.append(Paragraph(title, styles["CoverTitle"]))
    elements.append(Paragraph(subtitle, styles["CoverSubtitle"]))

    # Divider line
    line = Drawing(A4[0] - 6 * cm, 1)
    line.add(Line(0, 0, A4[0] - 6 * cm, 0, strokeColor=BORDER_LIGHT, strokeWidth=0.5))
    elements.append(line)
    elements.append(Spacer(1, 1 * cm))

    # Report metadata card
    meta_data = [
        ["Report Type", tab_name],
        ["Date Range", date_range_label],
        ["Generated", datetime.now().strftime("%B %d, %Y  ·  %I:%M %p")],
        ["Format", "Comprehensive Analytics"],
    ]

    meta_table = Table(meta_data, colWidths=[4 * cm, 8 * cm])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BG_SUBTLE),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                ("TEXTCOLOR", (0, 0), (0, -1), TEXT_MUTED),
                ("TEXTCOLOR", (1, 0), (1, -1), TEXT_HEADING),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 16),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                ("LINEBELOW", (0, 0), (-1, -2), 0.3, BORDER_LIGHT),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(meta_table)

    # Bottom spacer + footer text
    elements.append(Spacer(1, 5 * cm))
    elements.append(
        Paragraph(
            "This report contains confidential workspace analytics.<br/>Handle according to your organization's data policy.",
            styles["Meta"],
        )
    )

    elements.append(PageBreak())
    return elements


def _build_executive_summary(styles, kpis: list, title: str, description: str) -> list:
    """Executive summary section with prominent KPIs."""
    elements = []

    elements.append(Paragraph("Executive Summary", styles["H1"]))
    elements.append(Paragraph(description, styles["SubtitleWithBrand"]))

    # KPI cards in a 3-column grid
    kpi_rows = []
    row = []
    for i, kpi in enumerate(kpis):
        card = _build_kpi_card(kpi)
        row.append(card)
        if (i + 1) % 3 == 0:
            kpi_rows.append(row)
            row = []
    if row:
        # Pad the last row with empty cells
        while len(row) < 3:
            row.append("")
        kpi_rows.append(row)

    # Render each row
    for row in kpi_rows:
        row_table = Table([row], colWidths=[5.5 * cm] * 3)
        row_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elements.append(row_table)
        elements.append(Spacer(1, 6))

    elements.append(Spacer(1, 0.5 * cm))
    return elements


def _build_kpi_card(kpi: dict):
    """Individual KPI card with value, label, sub-text."""
    if not kpi:
        return ""

    color = kpi.get("color", BRAND_PRIMARY)
    value = kpi.get("value", "0")
    label = kpi.get("label", "")
    sub = kpi.get("sub", "")

    inner = Table(
        [
            [
                Paragraph(
                    f'<font size="24" color="{color.hexval() if hasattr(color, "hexval") else color}"><b>{value}</b></font>',
                    getSampleStyleSheet()["Normal"],
                )
            ],
            [
                Paragraph(
                    f'<font size="10" color="#3C3C43"><b>{label}</b></font>',
                    getSampleStyleSheet()["Normal"],
                )
            ],
            [
                Paragraph(
                    f'<font size="8" color="#86868B">{sub}</font>',
                    getSampleStyleSheet()["Normal"],
                )
            ],
        ],
        colWidths=[5 * cm],
    )
    inner.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("BACKGROUND", (0, 0), (-1, -1), BG_CARD),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                ("LINEBEFORE", (0, 0), (0, -1), 3, color),
            ]
        )
    )
    return inner


def _build_section_header(styles, title: str, subtitle: str = None) -> list:
    """Beautiful section header with colored accent."""
    elements = []

    # Section title with left accent
    title_table = Table(
        [
            [
                Paragraph(
                    f'<font size="16" color="#1D1D1F"><b>{title}</b></font>',
                    styles["Normal"],
                )
            ]
        ],
        colWidths=[16 * cm],
    )
    title_table.setStyle(
        TableStyle(
            [
                ("LINEBEFORE", (0, 0), (0, -1), 4, BRAND_PRIMARY),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(title_table)

    if subtitle:
        elements.append(Spacer(1, 4))
        subtitle_para = Paragraph(
            f'<font size="9" color="#86868B">{subtitle}</font>', styles["Normal"]
        )
        subtitle_table = Table([[subtitle_para]], colWidths=[16 * cm])
        subtitle_table.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 16),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        elements.append(subtitle_table)

    elements.append(Spacer(1, 8))
    return elements


def _build_table(
    headers: list,
    rows: list,
    col_widths=None,
    zebra: bool = True,
    header_color=BRAND_PRIMARY,
    first_col_bold: bool = False,
) -> Table:
    """Premium styled table with optional zebra stripes."""
    data = [headers] + rows

    style_commands = [
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        # Body rows
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), TEXT_BODY),
        ("TOPPADDING", (0, 1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Grid
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, BORDER_LIGHT),
    ]

    # Zebra stripes
    if zebra:
        for i in range(1, len(data)):
            if i % 2 == 0:
                style_commands.append(("BACKGROUND", (0, i), (-1, i), BG_ZEBRA))

    # First column bold
    if first_col_bold:
        style_commands.append(("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"))
        style_commands.append(("TEXTCOLOR", (0, 1), (0, -1), TEXT_HEADING))

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle(style_commands))
    return table



def _build_bar_chart(
    data: list,
    labels: list,
    title: str = "",
    width: int = 16 * cm,
    height: int = 6 * cm,
    bar_color=BRAND_PRIMARY,
) -> Drawing:
    """Simple bar chart for embedding in PDF."""
    drawing = Drawing(width, height)

    safe_data = [float(v) if v is not None else 0.0 for v in data]
    safe_labels = [str(l) for l in labels]

    chart = VerticalBarChart()
    chart.x = 40
    chart.y = 30
    chart.width = width - 60
    chart.height = height - 60
    chart.data = [safe_data]
    chart.categoryAxis.categoryNames = safe_labels
    chart.categoryAxis.labels.fontSize = 7
    chart.categoryAxis.labels.fillColor = TEXT_MUTED
    chart.categoryAxis.labels.angle = 0
    chart.valueAxis.labels.fontSize = 7
    chart.valueAxis.labels.fillColor = TEXT_MUTED
    chart.valueAxis.valueMin = 0

    if safe_data and max(safe_data) > 0:
        chart.valueAxis.valueMax = max(safe_data) * 1.2
    else:
        chart.valueAxis.valueMax = 1.0  # Default max if all zeros

    chart.bars[0].fillColor = bar_color
    chart.bars[0].strokeColor = None
    chart.barSpacing = 2
    chart.groupSpacing = 8

    drawing.add(chart)
    return drawing


def _make_footer(report_type: str):
    """Returns a footer function with report context."""

    def _footer(canvas_obj, doc):
        canvas_obj.saveState()

        # Bottom line
        canvas_obj.setStrokeColor(BORDER_LIGHT)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(2 * cm, 1.6 * cm, A4[0] - 2 * cm, 1.6 * cm)

        # Left: TrustShare brand
        canvas_obj.setFont("Helvetica-Bold", 8)
        canvas_obj.setFillColor(BRAND_PRIMARY)
        canvas_obj.drawString(2 * cm, 1.1 * cm, "TRUSTSHARE")

        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.setFillColor(TEXT_LIGHT)
        canvas_obj.drawString(2 * cm, 0.7 * cm, f"{report_type} · Confidential")

        # Center: timestamp
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(TEXT_MUTED)
        canvas_obj.drawCentredString(
            A4[0] / 2,
            0.9 * cm,
            f"Generated {datetime.now().strftime('%b %d, %Y · %I:%M %p')}",
        )

        # Right: page number
        canvas_obj.setFont("Helvetica-Bold", 8)
        canvas_obj.setFillColor(TEXT_MUTED)
        canvas_obj.drawRightString(A4[0] - 2 * cm, 0.9 * cm, f"Page {doc.page}")

        canvas_obj.restoreState()

    return _footer


def _cover_footer(canvas_obj, doc):
    """Simpler footer for cover page."""
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(TEXT_LIGHT)
    canvas_obj.drawCentredString(
        A4[0] / 2, 1.2 * cm, "TrustShare · Secure File Sharing Platform"
    )
    canvas_obj.restoreState()


def _build_recent_activity_section(styles, recent_activity: dict) -> list:
    """
    Builds recent activity table — used in both File and Security PDFs.
    
    FIX ISS-7: Updated dict keys to match serialized activity format
    from get_recent_activity() which now returns dicts with keys:
    event_type, user_id, file_id, ip_address, time, created_at
    (NOT "user", "file", "action", "date" — those were wrong keys)
    """
    elements   = []
    activities = recent_activity.get("activities", []) or []

    if not activities:
        return elements

    elements.extend(
        _build_section_header(
            styles,
            "Recent Activity",
            "Latest events across the workspace",
        )
    )

    rows = []
    for activity in activities[:15]:
        # All activities are now dicts (ISS-1 fix ensures this)
        if isinstance(activity, dict):
            event   = activity.get("event_type", "")
            user    = str(activity.get("user_id",  "") or "System")
            file    = str(activity.get("file_id",  "") or "—")
            time    = activity.get("time", "") or activity.get("created_at", "")
        else:
            # Fallback for any edge case
            event   = getattr(activity, "event_type", "")
            user    = str(getattr(activity, "user_id",  "") or "System")
            file    = str(getattr(activity, "file_id",  "") or "—")
            time    = getattr(activity, "time", "") or str(
                getattr(activity, "created_at", "")
            )

        rows.append([
            str(event)[:20],
            str(user)[:20],
            str(file)[:35],
            str(time)[:20],
        ])

    if rows:
        elements.append(
            _build_table(
                ["Event", "User ID", "File ID", "When"],
                rows,
                col_widths=[3 * cm, 3.5 * cm, 6.5 * cm, 3.5 * cm],
                zebra=True,
            )
        )
        elements.append(Spacer(1, 0.4 * cm))

    return elements

def generate_file_analytics_pdf(
    data: Dict[str, Any],
    date_range_label: str = "Last 30 days",
) -> bytes:
    """Generates premium PDF for the File Analytics tab."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.2 * cm,
        title="TrustShare — File Analytics Report",
        author="TrustShare Analytics",
    )
    styles = _get_styles()
    elements = []

    # ═══ COVER PAGE ═══
    elements.extend(
        _build_cover_page(
            styles,
            title="File Analytics",
            subtitle="Workspace Storage & Activity Report",
            date_range_label=date_range_label,
            tab_name="File Analytics",
        )
    )

    # ═══ EXECUTIVE SUMMARY ═══
    storage = data.get("storage", {}) or {}
    uploads = data.get("uploads", {}) or {}
    downloads = data.get("downloads", {}) or {}
    sharing = data.get("sharing", {}) or {}
    deletes = data.get("deletes", {}) or {}

    kpis = [
        {
            "value": f"{storage.get('storage_used_gb', 0):.2f} GB",
            "label": "Storage Used",
            "sub": f"of {storage.get('storage_quota_gb', 0)} GB · {storage.get('storage_percentage', 0):.1f}%",
            "color": BRAND_PRIMARY,
        },
        {
            "value": f"{uploads.get('total_uploads', 0):,}",
            "label": "Files Uploaded",
            "sub": f"{uploads.get('today_uploads', 0)} today",
            "color": BRAND_SECONDARY,
        },
        {
            "value": f"{downloads.get('total_downloads', 0):,}",
            "label": "Downloads",
            "sub": f"{downloads.get('transferred_mb', 0):.1f} MB transferred",
            "color": COLOR_INFO,
        },
        {
            "value": f"{sharing.get('active_links', 0):,}",
            "label": "Active Shares",
            "sub": f"+{sharing.get('new_this_week', 0)} this week",
            "color": COLOR_SUCCESS,
        },
        {
            "value": f"{deletes.get('total_deletes', 0):,}",
            "label": "Files Deleted",
            "sub": f"{deletes.get('this_week_deletes', 0)} this week",
            "color": COLOR_WARNING,
        },
        {
            "value": f"{storage.get('total_users', 0):,}",
            "label": "Total Users",
            "sub": "Active workspace members",
            "color": TEXT_MUTED,
        },
    ]

    elements.extend(
        _build_executive_summary(
            styles,
            kpis,
            title="Executive Summary",
            description=f"Key performance indicators for <b>{date_range_label}</b>",
        )
    )

    # ═══ STORAGE TREND ═══
    trend = storage.get("trend", [])
    if trend:
        elements.extend(
            _build_section_header(
                styles,
                "Storage Usage Over Time",
                "Cumulative storage consumption trend",
            )
        )

        # Mini bar chart
        chart_data = [t.get("gb", 0) for t in trend]
        chart_labels = [t.get("month", "") for t in trend]
        if any(v > 0 for v in chart_data):
            elements.append(
                _build_bar_chart(chart_data, chart_labels, bar_color=BRAND_PRIMARY)
            )
            elements.append(Spacer(1, 8))

        # Table
        rows = [[t.get("month", ""), f"{t.get('gb', 0):.4f} GB"] for t in trend]
        elements.append(
            _build_table(
                ["Period", "Storage"],
                rows,
                col_widths=[8 * cm, 4 * cm],
                first_col_bold=True,
            )
        )
        elements.append(Spacer(1, 0.4 * cm))

    # ═══ UPLOAD / DOWNLOAD VOLUME ═══
    volume = uploads.get("volume_weekly", [])
    if volume:
        elements.extend(
            _build_section_header(
                styles, "Upload / Download Volume", "Weekly activity breakdown"
            )
        )
        rows = [
            [v.get("week", ""), str(v.get("uploads", 0)), str(v.get("downloads", 0))]
            for v in volume
        ]
        elements.append(
            _build_table(
                ["Week Starting", "Uploads", "Downloads"],
                rows,
                col_widths=[6 * cm, 4 * cm, 4 * cm],
                first_col_bold=True,
            )
        )
        elements.append(Spacer(1, 0.4 * cm))

    # ═══ FILE TYPE DISTRIBUTION (NEW!) ═══
    file_types = data.get("file_types", []) or []
    if file_types:
        elements.extend(
            _build_section_header(
                styles, "File Type Distribution", "Breakdown by file format"
            )
        )

        # Mini chart
        chart_data = [ft.get("count", 0) for ft in file_types[:8]]
        chart_labels = [ft.get("type", "") for ft in file_types[:8]]
        if any(v > 0 for v in chart_data):
            elements.append(
                _build_bar_chart(chart_data, chart_labels, bar_color=BRAND_SECONDARY)
            )
            elements.append(Spacer(1, 8))

        rows = [
            [
                ft.get("type", ""),
                f"{ft.get('count', 0):,}",
                f"{ft.get('size_mb', 0):.2f} MB",
            ]
            for ft in file_types
        ]
        elements.append(
            _build_table(
                ["File Type", "Count", "Total Size"],
                rows,
                col_widths=[6 * cm, 4 * cm, 4 * cm],
                first_col_bold=True,
            )
        )
        elements.append(Spacer(1, 0.4 * cm))

    # ═══ TOP SHARED FILES ═══
    top_files = sharing.get("top_files", [])
    if top_files:
        elements.extend(
            _build_section_header(
                styles, "Top Shared Files", "Most accessed files in workspace"
            )
        )
        rows = [
            [
                f"#{f.get('rank', '')}",
                f.get("name", "")[:50],
                str(f.get("opens", 0)),
                str(f.get("downloads", 0)),
            ]
            for f in top_files
        ]
        elements.append(
            _build_table(
                ["Rank", "File Name", "Opens", "Downloads"],
                rows,
                col_widths=[1.5 * cm, 8.5 * cm, 2.5 * cm, 2.5 * cm],
            )
        )
        elements.append(Spacer(1, 0.4 * cm))

    # ═══ TOP ACTIVE USERS (NEW!) ═══
    top_users = data.get("top_active_users", []) or []
    if top_users:
        elements.extend(
            _build_section_header(
                styles, "Top Active Users", "Most active workspace members"
            )
        )
        rows = [
            [
                f"#{u.get('rank', '')}",
                u.get("name", "")[:25],
                u.get("email", "")[:35],
                f"{u.get('activity', 0):,}",
            ]
            for u in top_users
        ]
        elements.append(
            _build_table(
                ["Rank", "Name", "Email", "Activity"],
                rows,
                col_widths=[1.5 * cm, 4.5 * cm, 6 * cm, 3 * cm],
            )
        )
        elements.append(Spacer(1, 0.4 * cm))

    # ═══ SHARING BY DEPARTMENT ═══
    departments = sharing.get("by_department", [])
    if departments:
        elements.extend(
            _build_section_header(
                styles, "Sharing by Department", "Activity distribution across teams"
            )
        )
        rows = [[d.get("name", ""), f"{d.get('value', 0)}%"] for d in departments]
        elements.append(
            _build_table(
                ["Department", "Share of Activity"],
                rows,
                col_widths=[10 * cm, 5 * cm],
                first_col_bold=True,
            )
        )
        elements.append(Spacer(1, 0.4 * cm))

    # ═══ RECENT ACTIVITY ═══
    recent_activity = data.get("recent_activity", {}) or {}
    elements.extend(_build_recent_activity_section(styles, recent_activity))

    # ═══ BUILD PDF ═══
    footer_fn = _make_footer("File Analytics Report")
    doc.build(elements, onFirstPage=_cover_footer, onLaterPages=footer_fn)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_security_pdf(
    data: Dict[str, Any],
    date_range_label: str = "Last 30 days",
) -> bytes:
    """Generates premium PDF for the Security tab."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.2 * cm,
        title="TrustShare — Security Report",
        author="TrustShare Analytics",
    )
    styles = _get_styles()
    elements = []

    # ═══ COVER PAGE ═══
    elements.extend(
        _build_cover_page(
            styles,
            title="Security Report",
            subtitle="Authentication, Threats & Access Monitoring",
            date_range_label=date_range_label,
            tab_name="Security Analytics",
        )
    )

    security = data.get("security", {}) or {}
    security_score = data.get("security_score", {}) or {}
    mfa_adoption = data.get("mfa_adoption", {}) or {}

    # ═══ EXECUTIVE SUMMARY ═══
    kpis = [
        {
            "value": f"{security.get('login_events', 0):,}",
            "label": "Successful Logins",
            "sub": "In this period",
            "color": COLOR_SUCCESS,
        },
        {
            "value": f"{security.get('failed_logins', 0):,}",
            "label": "Failed Attempts",
            "sub": "Requires monitoring",
            "color": COLOR_WARNING,
        },
        {
            "value": f"{security.get('blocked_attacks', 0):,}",
            "label": "Blocked Attacks",
            "sub": "Threats neutralized",
            "color": COLOR_DANGER,
        },
        {
            "value": f"{security.get('security_events', 0):,}",
            "label": "Security Events",
            "sub": "Total activities",
            "color": BRAND_PRIMARY,
        },
        {
            "value": f"{security_score.get('score', 0):.0f}/100",
            "label": "Security Score",
            "sub": security_score.get("status", "N/A"),
            "color": (
                colors.HexColor(security_score.get("color", "#007AFF"))
                if security_score.get("color")
                else BRAND_PRIMARY
            ),
        },
        {
            "value": f"{mfa_adoption.get('adoption_pct', 0):.0f}%",
            "label": "MFA Adoption",
            "sub": f"{mfa_adoption.get('mfa_enabled', 0)} of {mfa_adoption.get('total_users', 0)} users",
            "color": (
                colors.HexColor(mfa_adoption.get("color", "#5856D6"))
                if mfa_adoption.get("color")
                else BRAND_SECONDARY
            ),
        },
    ]

    elements.extend(
        _build_executive_summary(
            styles,
            kpis,
            title="Executive Summary",
            description=f"Security posture overview for <b>{date_range_label}</b>",
        )
    )

    # ═══ SECURITY SCORE BREAKDOWN ═══
    if security_score and security_score.get("breakdown"):
        elements.extend(
            _build_section_header(
                styles,
                "Security Score Breakdown",
                "Component scores contributing to overall rating",
            )
        )

        breakdown = security_score.get("breakdown", {})
        rows = [
            [
                "Login Success Rate",
                f"{breakdown.get('login_success', 0):.1f}/100",
                "40%",
            ],
            [
                "Attack Response",
                f"{breakdown.get('attack_response', 0):.1f}/100",
                "30%",
            ],
            [
                "Failed Login Score",
                f"{breakdown.get('failed_score', 0):.1f}/100",
                "30%",
            ],
        ]
        elements.append(
            _build_table(
                ["Component", "Score", "Weight"],
                rows,
                col_widths=[7 * cm, 4 * cm, 4 * cm],
                first_col_bold=True,
            )
        )
        elements.append(Spacer(1, 0.4 * cm))

    # ═══ LOGIN ACTIVITY ═══
    login_activity = security.get("login_activity", [])
    if login_activity:
        elements.extend(
            _build_section_header(
                styles,
                "Login Activity",
                "Daily successful vs failed authentication attempts",
            )
        )

        # Mini chart of successful logins
        chart_data = [l.get("success", 0) for l in login_activity]
        chart_labels = [l.get("date", "") for l in login_activity]
        if any(v > 0 for v in chart_data):
            elements.append(
                _build_bar_chart(chart_data, chart_labels, bar_color=COLOR_SUCCESS)
            )
            elements.append(Spacer(1, 8))

        rows = [
            [l.get("date", ""), str(l.get("success", 0)), str(l.get("failed", 0))]
            for l in login_activity
        ]
        elements.append(
            _build_table(
                ["Date", "Successful", "Failed"],
                rows,
                col_widths=[6 * cm, 4 * cm, 4 * cm],
                first_col_bold=True,
            )
        )
        elements.append(Spacer(1, 0.4 * cm))

    # ═══ MFA ADOPTION ═══
    if mfa_adoption and mfa_adoption.get("total_users", 0) > 0:
        elements.extend(
            _build_section_header(
                styles,
                "Multi-Factor Authentication",
                "MFA adoption across workspace users",
            )
        )
        rows = [
            ["Total Users", f"{mfa_adoption.get('total_users', 0):,}"],
            ["MFA Enabled", f"{mfa_adoption.get('mfa_enabled', 0):,}"],
            ["MFA Disabled", f"{mfa_adoption.get('mfa_disabled', 0):,}"],
            ["Adoption Rate", f"{mfa_adoption.get('adoption_pct', 0):.1f}%"],
            ["Status", mfa_adoption.get("status", "N/A")],
        ]
        elements.append(
            _build_table(
                ["Metric", "Value"],
                rows,
                col_widths=[8 * cm, 6 * cm],
                first_col_bold=True,
            )
        )
        elements.append(Spacer(1, 0.4 * cm))

    # ═══ SECURITY EVENTS TIMELINE ═══
    events = security.get("events", [])
    if events:
        elements.extend(
            _build_section_header(
                styles,
                "Security Event Timeline",
                "Recent security incidents and alerts",
            )
        )
        rows = [
            [
                e.get("sev", "").upper(),
                e.get("label", "")[:30],
                e.get("detail", "")[:50],
                e.get("time", ""),
            ]
            for e in events
        ]
        elements.append(
            _build_table(
                ["Severity", "Event", "Detail", "Time"],
                rows,
                col_widths=[2.5 * cm, 4 * cm, 6.5 * cm, 3 * cm],
            )
        )
        elements.append(Spacer(1, 0.4 * cm))

    # ═══ UNAUTHORIZED ACCESS ATTEMPTS ═══
    attempts = security.get("unauthorized_attempts", [])
    if attempts:
        elements.extend(
            _build_section_header(
                styles,
                "Unauthorized Access Attempts",
                "Detected intrusion attempts by IP address",
            )
        )
        rows = [
            [
                a.get("ip", ""),
                a.get("location", ""),
                str(a.get("target", ""))[:30],
                str(a.get("attempts", 0)),
                a.get("time", ""),
                "Blocked" if a.get("blocked") else "Flagged",
            ]
            for a in attempts
        ]
        elements.append(
            _build_table(
                ["IP Address", "Location", "Target", "Attempts", "When", "Status"],
                rows,
                col_widths=[3 * cm, 2.5 * cm, 4 * cm, 2 * cm, 2.5 * cm, 2 * cm],
            )
        )
        elements.append(Spacer(1, 0.4 * cm))

    # ═══ RECENT ACTIVITY (Now in Security tab too!) ═══
    recent_activity = data.get("recent_activity", {}) or {}
    elements.extend(_build_recent_activity_section(styles, recent_activity))

    # ═══ BUILD PDF ═══
    footer_fn = _make_footer("Security Report")
    doc.build(elements, onFirstPage=_cover_footer, onLaterPages=footer_fn)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
