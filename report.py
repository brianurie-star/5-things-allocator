import base64
import io
import math
import os

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
    Table,
    TableStyle,
    KeepTogether,
)

from monte_carlo import run_retirement_monte_carlo
from report_disclosures import DISCLOSURE_BY_TIER
from report_enhancements import (
    CHART_CAPTIONS,
    build_risk_dashboard_table,
    full_balance_sheet_callout_html,
    make_report_page_callbacks,
    methodology_callout_html,
    monthly_income_for_data,
    planning_inputs_glance_rows,
    research_key_points_flowables,
    section_outline,
    self_insurance_summary_table,
    what_we_measured_text,
)
from report_narrative import (
    FIVE_THING_TITLES,
    FLAW_SEQUENCE_EXAMPLE_PARAGRAPHS,
    NARRATIVE_COPY,
    classify_all_narratives,
    client_context_paragraph,
    flaw_sequence_bridge_paragraph,
    get_narrative_block,
)
from report_options_solutions import (
    DYING_TOO_SOON_RESEARCH,
    GETTING_SUED_RESEARCH,
    LONGEVITY_RESEARCH,
    UNDERESTIMATING_CARE_RESEARCH,
    PAID_QUOTE_LINKS,
    PAID_REPORT_EDUCATIONAL_DISCLOSURE,
    PAID_REPORT_INTRO,
    PAID_REPORT_OPTIMIZATION_HEADING,
    PAID_RISK_SECTIONS,
    RISK_SOLUTION_ORDER,
    get_paid_tier_block,
    paid_next_step_url,
)
from report_upgrade_tiles import free_options_upgrade_tile_copy

REPORT_TIER_LABELS = {
    "free": "Complimentary Report",
    "options": "Premium 5 Things Report",
    "monte_carlo": "Probability Study (Monte Carlo)",
}

# Aligns with static/styles.css :root tokens
THEME = {
    "text": "#1B2D47",
    "muted": "#5C6B7F",
    "border": "#D8DEE6",
    "card": "#FFFFFF",
    "well": "#F5F4F1",
    "accent": "#C4A574",
    "bar_fill": "#1B2D47",
    "pie_need": "#DC2626",
    "pie_remain": "#22C55E",
}

# Match SimpleDocTemplate margins: body = page width minus left/right margin
REPORT_MARGIN = 0.75 * inch
REPORT_PAGE_W = LETTER[0]
REPORT_BODY_W = REPORT_PAGE_W - 2 * REPORT_MARGIN
CARD_PAD = 14
CARD_INNER_W = REPORT_BODY_W - 2 * CARD_PAD
STRAT_GUTTER = 8
STRAT_HALF_FRAME_W = (REPORT_BODY_W - STRAT_GUTTER) / 2
CHART_TILE_PAD = 2
STRAT_IMG_HALF_MAX_W = STRAT_HALF_FRAME_W - 2 * CHART_TILE_PAD
# Max display size per chart role — fill tile width; height caps are generous for readability
PIE_HALF_MAX_H = 3.55 * inch
PIE_FULL_MAX_H = 4.0 * inch
BAR_FULL_MAX_H = 3.85 * inch
OUTCOMES_MAX_H = 3.85 * inch
# Outcomes under profile/allocation in flaw-of-averages section
OUTCOMES_STRATEGY_MAX_H = 3.25 * inch
SEQUENCE_EXAMPLE_MAX_H = 3.5 * inch
ASSUMP_COL_GUTTER = 14
ASSUMP_COL_W = (CARD_INNER_W - ASSUMP_COL_GUTTER) / 2
REPORT_HERO_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "static",
    "hero-background.png",
)
RESEARCH_FIGURE_MAX_H = 3.35 * inch


def money(v):
    return f"${float(v or 0):,.0f}"


def _safe_float(value, default=0.0):
    try:
        if value in ("", None):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _annual_rate_from_input(value, default=0.0):
    """Convert user ratio or percent input to a decimal annual rate."""
    v = _safe_float(value, default)
    if abs(v) > 1:
        return v / 100.0
    return v


def _retirement_return_rate(data):
    """Expected return from the user's selected investment profile (Mean % input)."""
    if data.get("market_mean") not in (None, ""):
        return _annual_rate_from_input(data.get("market_mean"), 9.89)
    prefix = data.get("risk_profile") or "growth"
    return _annual_rate_from_input(data.get(f"{prefix}_mean"), 9.89)


def _inflation_rate(data):
    return _annual_rate_from_input(data.get("inflation"), 0.03)


def _pct(value):
    v = _safe_float(value)
    if v > 1:
        return f"{v:.1f}%"
    return f"{v * 100:.1f}%"


def _home_equity_factor(age):
    if age < 62:
        return 0.00
    if age < 65:
        return 0.35
    if age < 70:
        return 0.40
    if age < 75:
        return 0.45
    if age < 80:
        return 0.50
    return 0.55


def _profile_assumption_rows(data):
    key = data.get("risk_profile") or "growth"
    labels = {
        "aggressive": "Aggressive",
        "growth": "Growth",
        "growthIncome": "Growth With Income",
        "intermediate": "Intermediate Growth",
    }
    prefix = key if key in labels else "growth"
    return [
        ("Investment profile", labels.get(key, data.get("profile_label", key))),
        (
            "Expected return (mean)",
            f"{_safe_float(data.get(f'{prefix}_mean')):.2f}%",
        ),
        (
            "Standard deviation",
            f"{_safe_float(data.get(f'{prefix}_stdev')):.2f}%",
        ),
        ("Equity allocation", _pct(data.get(f"{prefix}_equity"))),
    ]


def build_assumption_groups(data):
    his_age = _safe_float(data.get("his_age"))
    her_age = _safe_float(data.get("her_age"))
    planning_age = max(his_age, her_age)
    equity_factor = _home_equity_factor(planning_age)
    balance_mode = data.get("balance_sheet_mode", "partial")
    balance_label = (
        "Full balance sheet (home equity included in investable assets)"
        if balance_mode == "full"
        else "Partial balance sheet (financial assets only)"
    )

    groups = [
        (
            "Client & planning",
            [
                ("Client", data.get("client_name", "")),
                ("Report date", data.get("report_date", "")),
                ("His age / life expectancy", f"{int(his_age)} / {int(_safe_float(data.get('his_life_expectancy')))}"),
                ("Her age / life expectancy", f"{int(her_age)} / {int(_safe_float(data.get('her_life_expectancy')))}"),
                ("Balance sheet view", balance_label),
            ],
        ),
        (
            "Income & expenses",
            [
                ("His Social Security (monthly)", money(data.get("his_social_security"))),
                ("Her Social Security (monthly)", money(data.get("her_social_security"))),
                ("His pension (monthly)", money(data.get("his_pension"))),
                ("Her pension (monthly)", money(data.get("her_pension"))),
                ("His other income (monthly)", money(data.get("his_other_income"))),
                ("Her other income (monthly)", money(data.get("her_other_income"))),
                ("Basic living expenses (monthly)", money(data.get("monthly_living_expenses"))),
                ("Estimated tax rate", _pct(data.get("tax_rate"))),
                ("Guaranteed withdrawal rate", _pct(data.get("guaranteed_withdrawal_rate"))),
                ("Unprotected withdrawal rate", _pct(data.get("unprotected_withdrawal_rate"))),
                ("Inflation assumption", _pct(data.get("inflation"))),
            ],
        ),
        (
            "Assets",
            [
                ("Retirement assets", money(data.get("retirement_assets"))),
                ("Non-retirement assets", money(data.get("non_retirement_assets"))),
                ("Home value", money(data.get("home_value"))),
                ("Mortgage balance", money(data.get("mortgage_balance"))),
                ("Guaranteed income allocation", _pct(data.get("guaranteed_income_allocation"))),
                ("Accessible home equity factor (by age)", _pct(equity_factor)),
                ("Home equity income rate", "5.0% annually on accessible equity"),
            ],
        ),
        (
            "Investment profile",
            _profile_assumption_rows(data),
        ),
        (
            "Protection & risk scenarios",
            [
                ("Life insurance protection", money(data.get("life_insurance_protection"))),
                ("LTC insurance protection", money(data.get("ltc_insurance_protection"))),
                ("Auto liability protection", money(data.get("auto_insurance_protection"))),
                ("Home liability protection", money(data.get("home_insurance_protection"))),
                ("Umbrella protection", money(data.get("umbrella_insurance_protection"))),
                ("Monthly LTC cost", money(data.get("monthly_ltc_cost"))),
                ("LTC duration (years)", f"{int(_safe_float(data.get('ltc_years')))}"),
                ("Lawsuit award scenario", money(data.get("lawsuit_award"))),
                ("Life insurance premium (monthly)", money(data.get("life_insurance_monthly_cost"))),
                ("LTC premium (monthly)", money(data.get("ltc_insurance_monthly_cost"))),
                ("Auto premium (monthly)", money(data.get("auto_insurance_monthly_cost"))),
                ("Home premium (monthly)", money(data.get("home_insurance_monthly_cost"))),
                ("Umbrella premium (monthly)", money(data.get("umbrella_insurance_monthly_cost"))),
            ],
        ),
        (
            "Model calculations",
            [
                (
                    "Protected monthly income",
                    "Social Security + pensions + guaranteed withdrawals on protected assets",
                ),
                (
                    "Estimated taxes",
                    "Total monthly income × tax rate",
                ),
                (
                    "Early death exposure",
                    "25% of investable assets minus life insurance protection",
                ),
                (
                    "Long-term care exposure",
                    "Monthly LTC cost × 12 × years × 2 minus LTC insurance protection",
                ),
                (
                    "Lawsuit net amount at risk",
                    "Lawsuit award minus the greater of auto or home liability protection, minus umbrella",
                ),
                (
                    "Self-insurance total",
                    "Sum of early death, LTC, and lawsuit net amounts at risk",
                ),
                (
                    "Outcome ranges (68% / 98%)",
                    "Profile mean return ± 1 or 2 standard deviations",
                ),
            ],
        ),
    ]
    return groups


def assumptions_table(rows, styles, width=ASSUMP_COL_W):
    label_w = width * 0.46
    value_w = width - label_w
    table_rows = []
    for label, value in rows:
        table_rows.append([
            Paragraph(label, styles["muted"]),
            Paragraph(str(value), styles["body"]),
        ])
    table = Table(table_rows, colWidths=[label_w, value_w])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.HexColor(THEME["border"])),
    ]))
    return table


def _assumption_group_stack(title, rows, styles):
    return [
        Paragraph(f"<b>{title}</b>", styles["h2_section"]),
        Spacer(1, 4),
        assumptions_table(rows, styles),
    ]


def _assumption_group_cell(title, rows, styles):
    stack = _assumption_group_stack(title, rows, styles)
    cell = Table([[f] for f in stack], colWidths=[ASSUMP_COL_W])
    cell.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return cell


def append_assumptions_section(story, data, styles):
    groups = build_assumption_groups(data)
    split_at = (len(groups) + 1) // 2
    left_groups = groups[:split_at]
    right_groups = groups[split_at:]
    pair_count = max(len(left_groups), len(right_groups))

    story.append(Spacer(1, 20))
    story.append(section_outline("Assumptions & Methodology", "assumptions"))
    story.append(section_heading_row(
        "Assumptions",
        "Client inputs and model rules used to generate this report.",
        styles,
    ))
    story.append(Spacer(1, 10))

    table_rows = []
    for i in range(pair_count):
        left = left_groups[i] if i < len(left_groups) else None
        right = right_groups[i] if i < len(right_groups) else None
        if left:
            left_cell = _assumption_group_cell(left[0], left[1], styles)
        else:
            left_cell = Spacer(ASSUMP_COL_W, 1)
        if right:
            right_cell = _assumption_group_cell(right[0], right[1], styles)
        else:
            right_cell = Spacer(ASSUMP_COL_W, 1)
        table_rows.append([left_cell, right_cell])

    assumptions_grid = Table(table_rows, colWidths=[ASSUMP_COL_W, ASSUMP_COL_W], repeatRows=0)
    assumptions_grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), ASSUMP_COL_GUTTER / 2),
        ("LEFTPADDING", (1, 0), (1, -1), ASSUMP_COL_GUTTER / 2),
        ("RIGHTPADDING", (1, 0), (1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.HexColor(THEME["border"])),
    ]))
    story.append(assumptions_grid)


def save_base64_png(data_url, folder, filename):
    if not data_url or "," not in data_url:
        return None

    try:
        _, encoded = data_url.split(",", 1)
        binary = base64.b64decode(encoded, validate=True)
    except Exception:
        return None

    path = os.path.join(folder, filename)
    try:
        # Normalize any valid browser canvas image into a clean PNG.
        with PILImage.open(io.BytesIO(binary)) as img:
            img.save(path, format="PNG")
    except Exception:
        return None

    return path


def safe_image(path, width, height):
    if not path:
        return None
    if not os.path.exists(path):
        return None
    return Image(path, width=width, height=height)


def chart_image_fit(path, max_width, max_height, prefer_width=True):
    """
    Embed chart PNG without distortion. Scales uniformly; when prefer_width is True,
    uses the full max_width first (then shrinks only if height exceeds max_height).
    """
    if not path or not os.path.exists(path):
        return None
    try:
        with PILImage.open(path) as im:
            w_px, h_px = im.size
    except Exception:
        return None
    if w_px <= 0 or h_px <= 0:
        return None
    mw = float(max_width)
    mh = float(max_height)
    if prefer_width:
        scale = mw / w_px
        dh = h_px * scale
        if dh > mh:
            scale = mh / h_px
    else:
        scale = min(mw / w_px, mh / h_px)
    dw = w_px * scale
    dh = h_px * scale
    return Image(path, width=dw, height=dh)


def chart_image_fit_budget(path, max_width, heights_budget, height_share=1.0):
    """Scale a chart to fit width and a share of a vertical budget (for stacked tiles)."""
    share = max(0.55 * inch, float(heights_budget) * float(height_share))
    return chart_image_fit(path, max_width, share, prefer_width=True)


def pie_chart_half_fit(path):
    """Side-by-side pies (profile/allocation, lawsuit pair, etc.)."""
    return chart_image_fit(path, STRAT_IMG_HALF_MAX_W, PIE_HALF_MAX_H, prefer_width=True)


def pie_chart_full_fit(path):
    """Single-column pies — use full body width instead of a centered half slot."""
    return chart_image_fit(path, CARD_INNER_W, PIE_FULL_MAX_H)


def pie_chart_image_fit(path):
    return pie_chart_half_fit(path)


def bar_chart_full_fit(path):
    return chart_image_fit(path, CARD_INNER_W, BAR_FULL_MAX_H)


def outcomes_chart_image_fit(path):
    """Full-width outcomes chart, capped height so it scales up without overflowing the page."""
    return chart_image_fit(path, CARD_INNER_W, OUTCOMES_MAX_H)


def outcomes_chart_strategy_fit(path):
    """Sample range chart sized to sit below profile/allocation on the same page."""
    return chart_image_fit(path, CARD_INNER_W, OUTCOMES_STRATEGY_MAX_H)


def report_cover_hero_image():
    """Site hero scaled to the same width as the cover title tile (REPORT_BODY_W)."""
    path = REPORT_HERO_PATH
    if not path or not os.path.exists(path):
        return None
    try:
        with PILImage.open(path) as im:
            w_px, h_px = im.size
    except Exception:
        return None
    if w_px <= 0 or h_px <= 0:
        return None
    dw = float(REPORT_BODY_W)
    dh = h_px * (dw / w_px)
    return Image(path, width=dw, height=dh)


def append_report_cover(story, data, tier_label, styles, report_tier="free"):
    """Cover: site hero image with home-page typography and centered copy."""
    hero = report_cover_hero_image()
    if hero:
        hero_row = Table([[hero]], colWidths=[REPORT_BODY_W])
        hero_row.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(hero_row)

    client_name = data.get("client_name", "") or ""
    report_date = data.get("report_date", "") or ""
    overlay_rows = [
        [Paragraph("READY TO RETIRE?", styles["cover_brand"])],
        [Spacer(1, 8)],
        [Paragraph("The Five Things That Can Cause a Paycut", styles["cover_hero_title"])],
        [Spacer(1, 10)],
        [
            Paragraph(
                "Each item below is a decision point—<br/>"
                "or a decision you may be forced into if the risk shows up.",
                styles["cover_hero_lead"],
            )
        ],
        [Spacer(1, 12)],
        [Paragraph("Personalized Retirement Readiness Report", styles["cover_hero_sub"])],
        [Paragraph(tier_label, styles["cover_hero_sub"])],
    ]
    if client_name or report_date:
        overlay_rows.append([Spacer(1, 14)])
        if client_name:
            overlay_rows.append([Paragraph(f"Client: {client_name}", styles["cover_hero_meta"])])
        if report_date:
            overlay_rows.append([Paragraph(f"Date: {report_date}", styles["cover_hero_meta"])])

    overlay_inner = Table(overlay_rows, colWidths=[REPORT_BODY_W - 48])
    overlay_inner.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    overlay_wrap = Table([[overlay_inner]], colWidths=[REPORT_BODY_W])
    overlay_wrap.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0F1F35")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 24),
        ("RIGHTPADDING", (0, 0), (-1, -1), 24),
        ("TOPPADDING", (0, 0), (-1, -1), 22),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 22),
    ]))
    story.append(overlay_wrap)
    story.append(PageBreak())


def nice_axis_max(value):
    if value is None or value <= 0:
        return 1.0
    exp = 10 ** math.floor(math.log10(value))
    step = exp if value / exp <= 10 else exp * 2
    return math.ceil(value / step) * step * 1.02


def build_styles():
    base = getSampleStyleSheet()
    serif_bold = "Times-Bold"
    serif = "Times-Roman"
    sans = "Helvetica"
    sans_bold = "Helvetica-Bold"
    navy = colors.HexColor(THEME["text"])
    muted = colors.HexColor(THEME["muted"])

    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName=serif_bold,
            fontSize=26,
            leading=30,
            textColor=navy,
            spaceAfter=12,
        ),
        "cover_brand": ParagraphStyle(
            "cover_brand",
            parent=base["Normal"],
            fontName=sans_bold,
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#E8D9C0"),
            spaceAfter=0,
        ),
        "cover_hero_title": ParagraphStyle(
            "cover_hero_title",
            parent=base["Title"],
            fontName=serif_bold,
            fontSize=22,
            leading=26,
            alignment=TA_CENTER,
            textColor=colors.white,
            spaceAfter=0,
        ),
        "cover_hero_lead": ParagraphStyle(
            "cover_hero_lead",
            parent=base["BodyText"],
            fontName=sans,
            fontSize=10.5,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#F8FAFC"),
            spaceAfter=0,
        ),
        "cover_hero_sub": ParagraphStyle(
            "cover_hero_sub",
            parent=base["BodyText"],
            fontName=sans,
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#E8EEF4"),
            spaceAfter=4,
        ),
        "cover_hero_meta": ParagraphStyle(
            "cover_hero_meta",
            parent=base["BodyText"],
            fontName=sans,
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#C4A574"),
            spaceAfter=2,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName=serif_bold,
            fontSize=17,
            leading=22,
            alignment=TA_CENTER,
            textColor=navy,
            spaceAfter=6,
        ),
        "h1_section": ParagraphStyle(
            "h1_section",
            parent=base["Heading1"],
            fontName=serif_bold,
            fontSize=17,
            leading=22,
            alignment=TA_LEFT,
            textColor=navy,
            spaceAfter=6,
        ),
        "h2_section": ParagraphStyle(
            "h2_section",
            parent=base["Heading2"],
            fontName=serif_bold,
            fontSize=13,
            leading=17,
            textColor=navy,
            spaceBefore=0,
            spaceAfter=4,
        ),
        "h2_subsection": ParagraphStyle(
            "h2_subsection",
            parent=base["Heading2"],
            fontName=serif_bold,
            fontSize=13,
            leading=17,
            alignment=TA_CENTER,
            textColor=navy,
            spaceBefore=0,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName=sans,
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#334155"),
            spaceAfter=8,
        ),
        "muted": ParagraphStyle(
            "muted",
            parent=base["BodyText"],
            fontName=sans,
            fontSize=10,
            leading=14,
            textColor=muted,
            spaceAfter=0,
        ),
        "muted_center": ParagraphStyle(
            "muted_center",
            parent=base["BodyText"],
            fontName=sans,
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=muted,
            spaceAfter=0,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor(THEME["muted"]),
            spaceAfter=6,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=32,
            textColor=colors.HexColor(THEME["text"]),
            spaceAfter=0,
        ),
        "narrative_headline": ParagraphStyle(
            "narrative_headline",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor(THEME["text"]),
            spaceBefore=4,
            spaceAfter=8,
        ),
        "quote": ParagraphStyle(
            "quote",
            parent=base["BodyText"],
            fontName="Times-Italic",
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor(THEME["text"]),
            spaceAfter=0,
        ),
    }


def kpi_tile(label, value, styles):
    table = Table(
        [[Paragraph(f"<b>{label}</b>", styles["kpi_label"])],
         [Paragraph(value, styles["kpi_value"])]],
        colWidths=[2.15 * inch],
        rowHeights=[None, None],
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(THEME["card"])),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor(THEME["border"])),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def pull_quote_box(text, styles):
    table = Table(
        [[Paragraph(text, styles["quote"])]],
        colWidths=[CARD_INNER_W],
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor(THEME["border"])),
        ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor(THEME["accent"])),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return table


def narrative_headline_style(tier, styles):
    accents = {
        "on_track": "#15803D",
        "at_risk": "#B45309",
        "high_risk": "#B91C1C",
    }
    accent = accents.get(tier, THEME["text"])
    return ParagraphStyle(
        f"narrative_headline_{tier}",
        parent=styles["narrative_headline"],
        textColor=colors.HexColor(accent),
    )


def narrative_section_block(section_key, tier, styles, data=None):
    block = get_narrative_block(section_key, tier)
    if not block:
        return [], None

    headline_style = narrative_headline_style(tier, styles)
    flowables = [
        Paragraph(f'<b>{block.get("headline", "")}</b>', headline_style),
    ]

    for para in block.get("paragraphs", []):
        flowables.append(Paragraph(para, styles["body"]))

    if data:
        ctx = client_context_paragraph(section_key, data)
        if ctx:
            flowables.append(Paragraph(ctx, styles["body"]))

    for bullet in block.get("bullets", []):
        flowables.append(Paragraph(f"• {bullet}", styles["body"]))

    for para in block.get("after_bullets", []):
        flowables.append(Paragraph(para, styles["body"]))

    return flowables, block.get("quote")


def append_chart_caption(story, chart_key, styles):
    text = CHART_CAPTIONS.get(chart_key)
    if not text:
        return
    story.append(Spacer(1, 4))
    story.append(Paragraph(text, styles["muted"]))
    story.append(Spacer(1, 6))


def append_what_we_measured(story, section_key, data, styles):
    text = what_we_measured_text(section_key, data)
    if not text:
        return
    story.append(Paragraph(f"<i>What we measured:</i> {text}", styles["muted"]))
    story.append(Spacer(1, 6))


def append_narrative(story, section_key, tier, styles, data=None):
    parts, quote = narrative_section_block(section_key, tier, styles, data=data)
    if not parts:
        return
    story.append(Spacer(1, 12))
    append_flow_block(story, parts, trailing_spacer=8 if quote else 12)
    if quote:
        story.append(pull_quote_box(f'"{quote}"', styles))
        story.append(Spacer(1, 12))


def options_consider_tile_box(flowables, styles):
    """Gold-accent tile for tier-matched Options to consider (premium) or upgrade (free)."""
    inner_w = CARD_INNER_W
    inner = Table([[f] for f in flowables], colWidths=[inner_w])
    inner.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    outer = Table([[inner]], colWidths=[REPORT_BODY_W])
    outer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F0E8")),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#E8D9C0")),
        ("LINEBEFORE", (0, 0), (0, -1), 4, colors.HexColor(THEME["accent"])),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    return outer


def append_free_options_upgrade_tile(story, section_key, upgrade_url, styles):
    """Separate Options to consider tile in the complimentary report (premium content lives here)."""
    copy = free_options_upgrade_tile_copy(section_key)
    if not copy.get("summary"):
        return

    parts = [
        Paragraph(
            '<font color="#A88652"><b>PREMIUM 5 THINGS REPORT</b></font>',
            styles["muted"],
        ),
        Paragraph("<b>Options to consider:</b>", styles["h2_section"]),
    ]
    subtitle = copy.get("section_subtitle", "")
    if subtitle:
        parts.append(Paragraph(
            f'<font color="{THEME["muted"]}">'
            f'{copy.get("section_title", "")} · {subtitle}</font>',
            styles["muted"],
        ))
    parts.append(Paragraph(copy["summary"], styles["body"]))
    parts.append(Spacer(1, 8))
    if upgrade_url:
        parts.append(Paragraph(
            '<b>Upgrade:</b> '
            f'<a href="{upgrade_url}" color="#1B2D47">'
            "<u>Download Premium 5 Things Report</u></a>",
            styles["body"],
        ))
        parts.append(Paragraph(
            f'<font color="{THEME["muted"]}">{upgrade_url}</font>',
            styles["muted"],
        ))
    else:
        parts.append(Paragraph(
            "After exporting from the 5 Things™ Allocator, open the upgrade page to "
            "download the premium report with your saved inputs.",
            styles["body"],
        ))

    story.append(Spacer(1, 10))
    story.append(options_consider_tile_box(parts, styles))


def append_paid_risk_solutions(story, section_key, narratives, styles, report_tier="options"):
    """Tier-matched strategies for Premium 5 Things reports — context card + Options tile."""
    if (report_tier or "").lower() != "options":
        return
    if section_key not in PAID_RISK_SECTIONS:
        return

    meta = PAID_RISK_SECTIONS[section_key]
    tier = narratives.get(section_key, "on_track")
    block = get_paid_tier_block(section_key, tier)
    next_step_url = paid_next_step_url(meta["next_step_key"])

    context_parts = [
        Paragraph(f"<b>{block['headline']}</b>", styles["h2_section"]),
        Paragraph(block["summary"], styles["body"]),
    ]
    story.append(Spacer(1, 10))
    append_flow_block(story, context_parts, trailing_spacer=8)

    options_parts = [
        Paragraph("<b>Options to consider:</b>", styles["h2_section"]),
        Spacer(1, 6),
    ]
    for bullet in block["bullets"]:
        options_parts.append(Paragraph(f"• {bullet}", styles["body"]))
    for para in block.get("after_bullets", []):
        options_parts.append(Spacer(1, 4))
        options_parts.append(Paragraph(para, styles["body"]))
    options_parts.append(Spacer(1, 8))
    action_label = meta.get("next_step_label") or "Take the next step"
    options_parts.append(Paragraph(
        f'<a href="{next_step_url}" color="#1B2D47"><u>{action_label}</u></a>',
        styles["body"],
    ))
    story.append(Spacer(1, 8))
    story.append(options_consider_tile_box(options_parts, styles))


def append_paid_quote_links_section(story, styles):
    """Summary of all quote and consultation links for the premium report."""
    story.append(Paragraph("<b>Take Action</b>", styles["h1"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "The links below correspond to the options discussed in this report. "
        "They are provided for educational planning—not as recommendations or a solicitation.",
        styles["body"],
    ))
    story.append(Spacer(1, 10))

    parts = []
    for item in PAID_QUOTE_LINKS:
        url = paid_next_step_url(item["key"])
        parts.append(Paragraph(
            f'• <a href="{url}" color="#1B2D47"><u>{item["label"]}</u></a> '
            f'<font color="{THEME["muted"]}">— {item["note"]}</font>',
            styles["body"],
        ))
        parts.append(Spacer(1, 8))
    append_flow_block(story, parts, trailing_spacer=14)


def append_narrative_with_premium(
    story, section_key, tier, narratives, styles, report_tier, upgrade_url=None, data=None
):
    append_narrative(story, section_key, tier, styles, data=data)
    if report_tier == "free" and section_key in RISK_SOLUTION_ORDER:
        append_free_options_upgrade_tile(story, section_key, upgrade_url, styles)
    elif report_tier == "options" and section_key in RISK_SOLUTION_ORDER:
        append_paid_risk_solutions(
            story, section_key, narratives, styles, report_tier=report_tier
        )


def five_thing_heading(number, section_key, subtitle, styles):
    title = FIVE_THING_TITLES[section_key]
    return section_heading_row(f"{number}. {title}", subtitle, styles)


def static_asset_path(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", filename)


def append_research_figure(story, filename, title, caption, styles):
    """Static figure: title and caption in flow; image only in a chart tile."""
    if title:
        story.append(Paragraph(f"<b>{title}</b>", styles["h2_section"]))
        story.append(Spacer(1, 6))
    img_path = static_asset_path(filename)
    img = chart_image_fit(img_path, CARD_INNER_W, RESEARCH_FIGURE_MAX_H)
    if img:
        story.append(chart_card(img, width=REPORT_BODY_W))
    else:
        story.append(Paragraph("Figure unavailable during export.", styles["muted"]))
    if caption:
        story.append(Spacer(1, 6))
        story.append(Paragraph(caption, styles["muted"]))
    story.append(Spacer(1, 8))


def append_longevity_research_evidence(story, styles):
    """Longevity risk context, inflation/longevity figures, and satisfaction research."""
    lr = LONGEVITY_RESEARCH
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>{lr['section_title']}</b>", styles["h2_subsection"]))
    story.append(Spacer(1, 6))
    append_flow_block(story, research_key_points_flowables(lr.get("key_research_points"), styles))

    understanding_parts = [
        Paragraph(f"<b>{lr['understanding_heading']}</b>", styles["h2_section"]),
        Spacer(1, 4),
    ]
    for para in lr["understanding_paragraphs"]:
        understanding_parts.append(Paragraph(para, styles["body"]))
    append_flow_block(story, understanding_parts)

    for figure in lr["figures"]:
        append_research_figure(
            story,
            figure["filename"],
            figure["title"],
            figure["caption"],
            styles,
        )

    longevity_parts = [
        Paragraph(lr["longevity_intro"], styles["body"]),
        Spacer(1, 4),
    ]
    for stat in lr["longevity_stats"]:
        longevity_parts.append(Paragraph(f"• {stat}", styles["body"]))
    longevity_parts.append(Spacer(1, 4))
    longevity_parts.append(Paragraph(lr["longevity_closing"], styles["body"]))
    append_flow_block(story, longevity_parts)

    key_parts = [
        Paragraph(f"<b>{lr['key_considerations_heading']}</b>", styles["h2_section"]),
        Spacer(1, 4),
    ]
    for item in lr["key_considerations"]:
        key_parts.append(Paragraph(f"• {item}", styles["body"]))
    append_flow_block(story, key_parts)

    optional_parts = [
        Paragraph(f"<b>{lr['optional_considerations_heading']}</b>", styles["h2_section"]),
        Spacer(1, 4),
    ]
    for item in lr["optional_considerations"]:
        optional_parts.append(Paragraph(f"• {item}", styles["body"]))
    append_flow_block(story, optional_parts)

    satisfaction_parts = [
        Paragraph(f"<b>{lr['satisfaction_research_heading']}</b>", styles["h2_section"]),
        Spacer(1, 4),
    ]
    for para in lr["satisfaction_research"]:
        satisfaction_parts.append(Paragraph(para, styles["body"]))
        satisfaction_parts.append(Spacer(1, 4))
    append_flow_block(story, satisfaction_parts)

    ref_parts = [
        Paragraph(f"<b>{lr['apa_references_heading']}</b>", styles["h2_section"]),
        Spacer(1, 6),
    ]
    for ref in lr["apa_references"]:
        ref_parts.append(Paragraph(ref, styles["body"]))
        ref_parts.append(Spacer(1, 8))
    append_flow_block(story, ref_parts, trailing_spacer=0)


def append_dying_too_soon_research_evidence(story, styles):
    """Survivor income risk context, slide figure, and retirement income impact."""
    ds = DYING_TOO_SOON_RESEARCH
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>{ds['section_title']}</b>", styles["h2_subsection"]))
    story.append(Spacer(1, 6))
    append_flow_block(story, research_key_points_flowables(ds.get("key_research_points"), styles))

    understanding_parts = [
        Paragraph(f"<b>{ds['understanding_heading']}</b>", styles["h2_section"]),
        Spacer(1, 4),
    ]
    for para in ds["understanding_paragraphs"]:
        understanding_parts.append(Paragraph(para, styles["body"]))
    append_flow_block(story, understanding_parts)

    for figure in ds["figures"]:
        append_research_figure(
            story,
            figure["filename"],
            figure["title"],
            figure["caption"],
            styles,
        )

    retirement_parts = [
        Paragraph(f"<b>{ds['retirement_income_heading']}</b>", styles["h2_section"]),
        Spacer(1, 4),
        Paragraph(ds["retirement_income_intro"], styles["body"]),
        Spacer(1, 6),
        Paragraph(f"<b>{ds['income_why_heading']}</b>", styles["h2_section"]),
        Spacer(1, 4),
    ]
    for item in ds["income_why_bullets"]:
        retirement_parts.append(Paragraph(f"• {item}", styles["body"]))
    retirement_parts.append(Spacer(1, 10))
    retirement_parts.append(Paragraph(f"<b>{ds['practical_heading']}</b>", styles["h2_section"]))
    retirement_parts.append(Spacer(1, 4))
    for item in ds["practical_bullets"]:
        retirement_parts.append(Paragraph(f"• {item}", styles["body"]))
    retirement_parts.append(Spacer(1, 6))
    retirement_parts.append(Paragraph(ds["enhanced_expense_closing"], styles["body"]))
    append_flow_block(story, retirement_parts)

    story.append(callout_box(f"<b>{ds['refined_insight']}</b>", styles))
    story.append(Spacer(1, 10))

    story.append(
        callout_box(
            f"<b>{ds['key_consideration_heading']}</b><br/><br/>{ds['key_consideration']}",
            styles,
        )
    )
    story.append(Spacer(1, 10))

    ref_parts = [
        Paragraph(f"<b>{ds['apa_references_heading']}</b>", styles["h2_section"]),
        Spacer(1, 6),
    ]
    for ref in ds["apa_references"]:
        ref_parts.append(Paragraph(ref, styles["body"]))
        ref_parts.append(Spacer(1, 8))
    append_flow_block(story, ref_parts, trailing_spacer=0)


def append_underestimating_care_research_evidence(story, styles):
    """Healthcare and long-term care cost research with APA references."""
    uc = UNDERESTIMATING_CARE_RESEARCH
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>{uc['section_title']}</b>", styles["h2_subsection"]))
    story.append(Spacer(1, 6))
    append_flow_block(story, research_key_points_flowables(uc.get("key_research_points"), styles))

    understanding_parts = [
        Paragraph(f"<b>{uc['understanding_heading']}</b>", styles["h2_section"]),
        Spacer(1, 4),
    ]
    for para in uc["understanding_paragraphs"]:
        understanding_parts.append(Paragraph(para, styles["body"]))
    understanding_parts.append(Spacer(1, 4))
    understanding_parts.append(Paragraph(uc["fidelity_citation"], styles["muted"]))
    understanding_parts.append(Spacer(1, 6))
    understanding_parts.append(
        Paragraph(f"<b>{uc['healthcare_costs_heading']}</b>", styles["h2_section"])
    )
    understanding_parts.append(Spacer(1, 4))
    for item in uc["healthcare_costs_bullets"]:
        understanding_parts.append(Paragraph(f"• {item}", styles["body"]))
    understanding_parts.append(Spacer(1, 6))
    understanding_parts.append(Paragraph(uc["healthcare_costs_closing"], styles["body"]))
    append_flow_block(story, understanding_parts)

    ltc_parts = [
        Paragraph(f"<b>{uc['ltc_cost_heading']}</b>", styles["h2_section"]),
        Spacer(1, 4),
    ]
    for para in uc["ltc_cost_paragraphs"]:
        ltc_parts.append(Paragraph(para, styles["body"]))
    ltc_parts.append(Spacer(1, 4))
    ltc_parts.append(Paragraph(uc["genworth_citation"], styles["muted"]))
    ltc_parts.append(Spacer(1, 6))
    ltc_parts.append(
        Paragraph(f"<b>{uc['ltc_duration_heading']}</b>", styles["h2_section"])
    )
    ltc_parts.append(Spacer(1, 4))
    for item in uc["ltc_duration_bullets"]:
        ltc_parts.append(Paragraph(f"• {item}", styles["body"]))
    ltc_parts.append(Spacer(1, 4))
    ltc_parts.append(Paragraph(uc["nchs_citation"], styles["muted"]))
    ltc_parts.append(Spacer(1, 6))
    ltc_parts.append(Paragraph(uc["ltc_duration_closing"], styles["body"]))
    append_flow_block(story, ltc_parts)

    medicaid_parts = [
        Paragraph(f"<b>{uc['medicaid_heading']}</b>", styles["h2_section"]),
        Spacer(1, 4),
    ]
    for para in uc["medicaid_paragraphs"]:
        medicaid_parts.append(Paragraph(para, styles["body"]))
    medicaid_parts.append(Spacer(1, 4))
    for item in uc["medicaid_bullets"]:
        medicaid_parts.append(Paragraph(f"• {item}", styles["body"]))
    medicaid_parts.append(Spacer(1, 6))
    medicaid_parts.append(Paragraph(uc["medicaid_closing"], styles["body"]))
    medicaid_parts.append(Spacer(1, 4))
    medicaid_parts.append(Paragraph(uc["kff_medicaid_citation"], styles["muted"]))
    medicaid_parts.append(Spacer(1, 6))
    medicaid_parts.append(Paragraph(uc["medicaid_strategy_note"], styles["body"]))
    append_flow_block(story, medicaid_parts)

    story.append(callout_box(f"<b>{uc['key_insight']}</b>", styles))
    story.append(Spacer(1, 10))

    ref_parts = [
        Paragraph(f"<b>{uc['apa_references_heading']}</b>", styles["h2_section"]),
        Spacer(1, 6),
    ]
    for ref in uc["apa_references"]:
        ref_parts.append(Paragraph(ref, styles["body"]))
        ref_parts.append(Spacer(1, 8))
    append_flow_block(story, ref_parts, trailing_spacer=0)


def lawsuit_charts_row(charts, styles):
    """Side-by-side lawsuit impact on investable assets and income."""
    row = Table(
        [[
            risk_chart_cell("lawsuit", charts, styles),
            risk_chart_cell("lawsuit_income", charts, styles),
        ]],
        colWidths=[STRAT_HALF_FRAME_W, STRAT_HALF_FRAME_W],
    )
    row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return row


def append_getting_sued_research_evidence(story, styles, report_tier=None, charts=None):
    """Liability risk research and plan-impact framing (same in free and premium)."""
    gs = GETTING_SUED_RESEARCH
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>{gs['section_title']}</b>", styles["h2_subsection"]))
    story.append(Spacer(1, 6))
    append_flow_block(story, research_key_points_flowables(gs.get("key_research_points"), styles))

    understanding_parts = [
        Paragraph(f"<b>{gs['understanding_heading']}</b>", styles["h2_section"]),
        Spacer(1, 4),
    ]
    for para in gs["understanding_paragraphs"]:
        understanding_parts.append(Paragraph(para, styles["body"]))
    append_flow_block(story, understanding_parts, trailing_spacer=6)
    story.append(
        Paragraph(f"<b>{gs['illustration_heading']}</b>", styles["h2_section"])
    )
    if charts:
        story.append(Spacer(1, 8))
        story.append(lawsuit_charts_row(charts, styles))
        append_chart_caption(story, "lawsuit", styles)
        append_chart_caption(story, "lawsuit_income", styles)
    illustration_follow = []
    for item in gs["illustration_bullets"]:
        illustration_follow.append(Paragraph(f"• {item}", styles["body"]))
    illustration_follow.append(Spacer(1, 6))
    illustration_follow.append(Paragraph(gs["jury_verdict_citation"], styles["muted"]))
    append_flow_block(story, illustration_follow)

    why_parts = [
        Paragraph(f"<b>{gs['why_matters_heading']}</b>", styles["h2_section"]),
        Spacer(1, 4),
        Paragraph(gs["why_matters_intro"], styles["body"]),
        Spacer(1, 4),
    ]
    for item in gs["why_matters_traits"]:
        why_parts.append(Paragraph(f"• {item}", styles["body"]))
    why_parts.append(Spacer(1, 6))
    why_parts.append(
        Paragraph(f"<b>{gs['why_matters_sources_heading']}</b>", styles["h2_section"])
    )
    why_parts.append(Spacer(1, 4))
    for item in gs["why_matters_sources"]:
        why_parts.append(Paragraph(f"• {item}", styles["body"]))
    why_parts.append(Spacer(1, 6))
    for para in gs["why_matters_paragraphs"]:
        why_parts.append(Paragraph(para, styles["body"]))
    append_flow_block(story, why_parts)

    story.append(callout_box(f"<b>{gs['key_insight']}</b>", styles))
    story.append(Spacer(1, 10))

    plan_parts = [
        Paragraph(f"<b>{gs['free_plan_heading']}</b>", styles["h2_section"]),
        Spacer(1, 4),
        Paragraph(gs["free_plan_intro"], styles["body"]),
        Spacer(1, 4),
    ]
    for item in gs["free_plan_bullets"]:
        plan_parts.append(Paragraph(f"• {item}", styles["body"]))
    plan_parts.append(Spacer(1, 6))
    plan_parts.append(Paragraph(gs["free_plan_closing"], styles["body"]))
    append_flow_block(story, plan_parts)

    practical_parts = [
        Paragraph(f"<b>{gs['practical_framing_heading']}</b>", styles["h2_section"]),
        Spacer(1, 4),
    ]
    for para in gs["practical_framing_paragraphs"]:
        practical_parts.append(Paragraph(para, styles["body"]))
        practical_parts.append(Spacer(1, 6))
    append_flow_block(story, practical_parts)

    story.append(pull_quote_box(f'"{gs["verdict_quote"]}"', styles))
    story.append(Spacer(1, 10))

    ref_parts = [
        Paragraph(f"<b>{gs['apa_references_heading']}</b>", styles["h2_section"]),
        Spacer(1, 6),
    ]
    for ref in gs["apa_references"]:
        ref_parts.append(Paragraph(ref, styles["body"]))
    append_flow_block(story, ref_parts, trailing_spacer=0)


def append_flaw_of_averages_example(story, styles, data=None):
    """Sequence-of-returns illustration (Scenario A vs B) kept with preceding explanation."""
    example_flow = [
        Paragraph(
            "<b>Example: Same average return, different outcomes</b>",
            styles["h2_section"],
        ),
        Spacer(1, 6),
    ]
    for idx, paragraph in enumerate(FLAW_SEQUENCE_EXAMPLE_PARAGRAPHS):
        example_flow.append(Paragraph(paragraph, styles["body"]))
        if idx < len(FLAW_SEQUENCE_EXAMPLE_PARAGRAPHS) - 1:
            example_flow.append(Spacer(1, 6))

    example_flow.append(Spacer(1, 8))
    img_path = static_asset_path("sequence-returns-example.png")
    img = chart_image_fit(img_path, CARD_INNER_W, SEQUENCE_EXAMPLE_MAX_H)
    if img:
        example_flow.append(chart_card(img, width=REPORT_BODY_W))
    else:
        example_flow.append(
            callout_box(
                "Scenario comparison table unavailable. Both scenarios use a 5% arithmetic mean return; "
                "early losses shorten portfolio life while early gains extend it.",
                styles,
            )
        )

    if data:
        example_flow.append(Spacer(1, 8))
        example_flow.append(Paragraph(flaw_sequence_bridge_paragraph(data), styles["body"]))

    story.append(Spacer(1, 8))
    story.append(KeepTogether(example_flow))


def callout_box(text, styles):
    table = Table(
        [[Paragraph(text, styles["body"])]],
        colWidths=[REPORT_BODY_W],
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F0E8")),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#E8D9C0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))

    return table


def chart_card(flowable, width=REPORT_BODY_W, well_bg=True, pad=None):
    tile_pad = CHART_TILE_PAD if pad is None else pad
    bg = colors.HexColor(THEME["well"]) if well_bg else colors.HexColor(THEME["card"])
    card = Table([[flowable]], colWidths=[width])
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor(THEME["border"])),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), tile_pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), tile_pad),
        ("TOPPADDING", (0, 0), (-1, -1), tile_pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), tile_pad),
    ]))
    return card


def embed_pie_chart(path, styles, title, full_width=True):
    fit = pie_chart_full_fit if full_width else pie_chart_half_fit
    img = fit(path) if path else None
    if img:
        w = REPORT_BODY_W if full_width else STRAT_HALF_FRAME_W
        return chart_card(img, width=w)
    return chart_unavailable_block(
        title,
        styles,
        outer_width=REPORT_BODY_W if full_width else STRAT_HALF_FRAME_W,
    )


def outcomes_chart_block(charts, styles, compact=False):
    """Full-width sample range of investment outcomes chart."""
    pth = charts.get("outcomes")
    fit = outcomes_chart_strategy_fit if compact else outcomes_chart_image_fit
    img = fit(pth) if pth else None
    if img:
        return chart_card(img, width=REPORT_BODY_W)
    return chart_unavailable_block("Sample Range of Investment Outcomes", styles)


def flaw_of_averages_charts_block(charts, styles):
    """Investment profile, asset allocation, and outcomes (split tiles to avoid page-break gaps)."""
    stack_budget = PIE_HALF_MAX_H + OUTCOMES_STRATEGY_MAX_H + 0.15 * inch
    img_prof = chart_image_fit_budget(
        charts.get("profile"), STRAT_IMG_HALF_MAX_W, stack_budget, 0.48
    )
    img_alloc = chart_image_fit_budget(
        charts.get("allocation"), STRAT_IMG_HALF_MAX_W, stack_budget, 0.48
    )
    cell_prof = (
        chart_card(img_prof, width=STRAT_HALF_FRAME_W)
        if img_prof
        else chart_unavailable_block("Investment Profile", styles, STRAT_HALF_FRAME_W)
    )
    cell_alloc = (
        chart_card(img_alloc, width=STRAT_HALF_FRAME_W)
        if img_alloc
        else chart_unavailable_block("Asset Allocation", styles, STRAT_HALF_FRAME_W)
    )
    pie_row = Table(
        [[cell_prof, cell_alloc]],
        colWidths=[STRAT_HALF_FRAME_W, STRAT_HALF_FRAME_W],
    )
    pie_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return [
        pie_row,
        Spacer(1, 6),
        outcomes_chart_block(charts, styles, compact=True),
    ]


def risk_chart_cell(chart_key, charts, styles):
    pth = charts.get(chart_key)
    img = pie_chart_image_fit(pth) if pth else None
    title = chart_key.replace("_", " ").title()
    if img:
        return chart_card(img, width=STRAT_HALF_FRAME_W)
    return chart_unavailable_block(title, styles, STRAT_HALF_FRAME_W)


def risk_charts_grid(charts, styles):
    keys = ["early_death", "ltc", "lawsuit", "lawsuit_income"]
    cells = [risk_chart_cell(key, charts, styles) for key in keys]
    grid = Table(
        [[cells[0], cells[1]], [cells[2], cells[3]]],
        colWidths=[STRAT_HALF_FRAME_W, STRAT_HALF_FRAME_W],
    )
    grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
    ]))
    return grid


def chart_unavailable_block(title, styles, outer_width=REPORT_BODY_W):
    return modern_card_stack(
        [
            Paragraph(f"<b>{title}</b>", styles["h2_section"]),
            Paragraph(
                "Chart image was unavailable during export. Recalculate and export again.",
                styles["muted"],
            ),
        ],
        width=outer_width,
    )


def append_flow_block(story, flowables, trailing_spacer=10):
    """Body copy outside tiles so ReportLab can break pages between blocks.

    Key call-outs (callout_box, pull_quote_box) stay separate—not passed through here.
    """
    for item in flowables:
        story.append(item)
    if trailing_spacer:
        story.append(Spacer(1, trailing_spacer))


def modern_card_stack(flowables, width=REPORT_BODY_W, well_bg=True):
    inner_w = width - 28
    inner = Table([[f] for f in flowables], colWidths=[inner_w])
    inner.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    bg = colors.HexColor(THEME["well"]) if well_bg else colors.HexColor(THEME["card"])
    outer = Table([[inner]], colWidths=[width])
    outer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor(THEME["border"])),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    return outer


def section_heading_row(title, subtitle, styles):
    """Risk section header: numbered title left, descriptive subtitle centered."""
    rows = [[Paragraph(title, styles["h1_section"])]]
    title_table_style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
    ]
    if subtitle:
        rows.append([Paragraph(subtitle, styles["muted_center"])])
        title_table_style.append(("ALIGN", (0, 1), (0, 1), "CENTER"))
    titles = Table(rows, colWidths=[REPORT_BODY_W - 40])
    titles.setStyle(TableStyle(title_table_style))
    row = Table([[titles]], colWidths=[REPORT_BODY_W])
    row.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(THEME["card"])),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor(THEME["border"])),
        ("LINEBELOW", (0, 0), (-1, 0), 3, colors.HexColor(THEME["accent"])),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    return row


def self_insurance_bar_fallback(data):
    drawing = Drawing(CARD_INNER_W, BAR_FULL_MAX_H)
    values = [
        float(data.get("assets_at_risk_early_death", 0) or 0),
        float(data.get("assets_at_risk_ltc", 0) or 0),
        float(data.get("net_at_risk_lawsuit", 0) or 0),
    ]

    vmax = nice_axis_max(max(values) if values else 0)

    chart = VerticalBarChart()
    chart.x = 42
    chart.y = 34
    chart.height = 112
    chart.width = float(CARD_INNER_W) - 72
    chart.data = [values]
    chart.categoryAxis.categoryNames = ["Early Death", "Long-Term Care", "Lawsuit"]
    chart.categoryAxis.labels.angle = 0
    chart.categoryAxis.labels.dy = -8
    chart.categoryAxis.labels.fontSize = 9
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = vmax
    chart.valueAxis.visibleGrid = 1
    chart.valueAxis.gridStrokeColor = colors.HexColor("#E2E8F0")
    chart.valueAxis.gridStrokeWidth = 0.5
    chart.valueAxis.strokeColor = colors.HexColor("#CBD5E1")
    chart.valueAxis.labels.fontSize = 8
    chart.categoryAxis.strokeColor = colors.HexColor("#CBD5E1")
    chart.barWidth = 56
    chart.groupSpacing = 10
    chart.bars[0].fillColor = colors.HexColor(THEME["bar_fill"])
    chart.bars[0].strokeColor = colors.HexColor(THEME["bar_fill"])
    chart.bars[0].strokeWidth = 0.35

    drawing.add(chart)
    return drawing


def self_insurance_pie_fallback(data):
    drawing = Drawing(CARD_INNER_W, PIE_FULL_MAX_H)

    need = float(data.get("self_insurance_total", 0) or 0)
    assets = float(data.get("investable_assets", 0) or 0)
    remaining = max(assets - need, 0)

    pie = Pie()
    pie_w = min(130, float(CARD_INNER_W) * 0.42)
    pie.x = (float(CARD_INNER_W) - pie_w) / 2
    pie.y = 24
    pie.width = pie_w
    pie.height = pie_w
    pie.data = [need, remaining]
    pie.labels = []
    pie.slices[0].fillColor = colors.HexColor(THEME["pie_need"])
    pie.slices[1].fillColor = colors.HexColor(THEME["pie_remain"])
    pie.slices[0].strokeWidth = 0.75
    pie.slices[1].strokeWidth = 0.75
    pie.slices[0].strokeColor = colors.HexColor("#FFFFFF")
    pie.slices[1].strokeColor = colors.HexColor("#FFFFFF")

    drawing.add(pie)
    return drawing


def self_insurance_pie_caption(data, styles):
    need = float(data.get("self_insurance_total", 0) or 0)
    assets = float(data.get("investable_assets", 0) or 0)
    remaining = max(assets - need, 0)

    if assets > 0:
        pct_need = min(100.0, (need / assets) * 100.0)
        pct_rem = max(0.0, 100.0 - pct_need)
    else:
        pct_need = 100.0 if need > 0 else 0.0
        pct_rem = 0.0

    lines = []
    lines.append(
        Paragraph(
            f"<b>{pct_need:.0f}%</b> of investable assets for self-insurance · "
            f"<b>{pct_rem:.0f}%</b> remaining",
            styles["body"],
        )
    )
    lines.append(
        Paragraph(
            f"Need {money(need)} · Investable {money(assets)} · Remaining {money(remaining)}",
            styles["muted"],
        )
    )
    if need > assets and assets > 0:
        lines.append(
            Paragraph(
                "<i>Need exceeds total investable assets — remaining assets shown as $0.</i>",
                styles["muted"],
            )
        )
    legend = Table(
        [
            [
                Paragraph(
                    f'<font color="{THEME["pie_need"]}">●</font> Self-insurance need',
                    styles["body"],
                )
            ],
            [
                Paragraph(
                    f'<font color="{THEME["pie_remain"]}">●</font> Remaining assets',
                    styles["body"],
                )
            ],
        ],
        colWidths=[CARD_INNER_W - 8],
    )
    legend.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    lines.append(legend)
    return lines


def append_disclosure_section(story, tier, styles):
    tier_key = (tier or "free").lower()
    if tier_key not in DISCLOSURE_BY_TIER:
        tier_key = "free"
    text = DISCLOSURE_BY_TIER[tier_key]
    story.append(Spacer(1, 14))
    story.append(
        modern_card_stack(
            [
                Paragraph("<b>Important disclosure — methodology</b>", styles["h2_section"]),
                Paragraph(text, styles["body"]),
            ],
            well_bg=False,
        )
    )


def _append_paid_bullet_list(story, bullets, styles):
    rows = [[Paragraph(f"• {item}", styles["body"])] for item in bullets]
    table = Table(rows, colWidths=[CARD_INNER_W])
    table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(table)


def append_paid_optimization_sections(story, narratives, styles):
    """Premium 5 Things Report: intro before withdrawal-rate comparison (strategies inline per section)."""
    story.append(
        Paragraph(
            f"<b>{PAID_REPORT_OPTIMIZATION_HEADING}</b>",
            styles["h2_section"],
        )
    )
    story.append(Spacer(1, 8))
    for paragraph in PAID_REPORT_INTRO:
        story.append(Paragraph(paragraph, styles["body"]))
    story.append(Spacer(1, 10))


def append_paid_report_closing(story, styles):
    story.append(Paragraph("<b>Important Disclosures</b>", styles["h1"]))
    story.append(Spacer(1, 8))
    for paragraph in PAID_REPORT_EDUCATIONAL_DISCLOSURE:
        story.append(Paragraph(paragraph, styles["body"]))
        story.append(Spacer(1, 6))


def append_options_report_section(story, data, styles):
    investable = float(data.get("investable_assets", 0) or 0)
    mean_return = _retirement_return_rate(data)
    inflation_rate = _inflation_rate(data)
    profile_label = data.get("profile_label") or (data.get("risk_profile") or "growth")

    narratives = classify_all_narratives(data)

    story.append(PageBreak())
    story.append(section_outline("Premium 5 Things Report", "premium_addendum"))
    story.append(
        Paragraph("<b>Premium 5 Things Report</b>", styles["h1"])
    )
    story.append(Spacer(1, 10))
    append_paid_optimization_sections(story, narratives, styles)
    append_paid_quote_links_section(story, styles)

    story.append(Paragraph("<b>Withdrawal-Rate Comparison</b>", styles["h1"]))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "The table below compares common withdrawal-rate scenarios against your investable assets "
            f"({money(investable)}), showing the <b>initial annual income</b> each rate would produce. "
            "This is an illustrative dollar comparison only—it does not estimate how long assets may "
            "last, sequence-of-returns risk, or probability of success. "
            f"(Your planning inputs use a <b>{profile_label}</b> profile with "
            f"{mean_return * 100:.1f}% expected return and {inflation_rate * 100:.1f}% inflation "
            "elsewhere in this report.)",
            styles["muted"],
        )
    )
    story.append(Spacer(1, 10))

    rows = [
        [
            Paragraph("<b>Withdrawal rate</b>", styles["body"]),
            Paragraph("<b>Initial annual income</b>", styles["body"]),
        ]
    ]
    for rate_pct in (3.0, 3.5, 4.0, 4.5, 5.0, 6.0):
        rate = rate_pct / 100.0
        annual = investable * rate
        rows.append([
            Paragraph(f"{rate_pct:.1f}%", styles["body"]),
            Paragraph(money(annual), styles["body"]),
        ])

    col_w = CARD_INNER_W / 2
    table = Table(rows, colWidths=[col_w, col_w])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#E2E8F0")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    centered_table = Table([[table]], colWidths=[CARD_INNER_W])
    centered_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("VALIGN", (0, 0), (0, 0), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(modern_card_stack([centered_table], width=REPORT_BODY_W))
    append_paid_report_closing(story, styles)


def append_monte_carlo_section(story, data, styles):
    mc = run_retirement_monte_carlo(data)

    story.append(Spacer(1, 14))
    story.append(section_outline("Monte Carlo Probability Study", "monte_carlo"))
    story.append(Paragraph("<b>Probability Study — Monte Carlo</b>", styles["h1"]))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            f"Based on {mc['simulations']:,} simulated paths over {mc['planning_years']} years using "
            f"{mc['mean_return_pct']:.1f}% expected return and {mc['stdev_pct']:.1f}% volatility.",
            styles["muted"],
        )
    )
    story.append(Spacer(1, 12))

    kpi_rows = [
        ["Probability plan sustains withdrawals", f"{mc['success_rate_pct']:.1f}%"],
        ["Starting portfolio", money(mc["initial_assets"])],
        ["Starting annual withdrawal", money(mc["annual_withdrawal_start"])],
        ["Median ending wealth", money(mc["median_ending"])],
        ["10th percentile ending wealth", money(mc["p10_ending"])],
        ["90th percentile ending wealth", money(mc["p90_ending"])],
    ]
    if mc.get("median_depletion_year") is not None:
        kpi_rows.append(
            ["Median depletion year (failed paths only)", f"Year {int(mc['median_depletion_year'])}"]
        )

    table_rows = [
        [Paragraph(label, styles["muted"]), Paragraph(f"<b>{value}</b>", styles["body"])]
        for label, value in kpi_rows
    ]
    table = Table(table_rows, colWidths=[CARD_INNER_W * 0.55, CARD_INNER_W * 0.45])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(modern_card_stack([table]))


def append_planning_inputs_glance(story, data, styles):
    rows = planning_inputs_glance_rows(data)
    parts = [
        Paragraph("<b>Planning inputs at a glance</b>", styles["h2_section"]),
        Spacer(1, 4),
        Paragraph(
            "Key inputs behind this report. Full assumptions and formulas appear in the "
            "<b>Assumptions &amp; Methodology</b> section at the end.",
            styles["muted"],
        ),
        Spacer(1, 6),
        assumptions_table(rows, styles, width=CARD_INNER_W),
    ]
    story.append(modern_card_stack(parts, width=REPORT_BODY_W))
    story.append(Spacer(1, 10))


def append_executive_summary(story, data, narratives, styles):
    monthly_income = monthly_income_for_data(data)
    monthly_expenses = float(data.get("monthly_expenses", 0) or 0)
    difference = monthly_income - monthly_expenses

    story.append(section_outline("Executive Summary", "executive_summary"))
    story.append(Paragraph("Executive Summary", styles["h1"]))

    tiles = Table([[
        kpi_tile("Monthly Income", money(monthly_income), styles),
        kpi_tile("Monthly Expenses", money(monthly_expenses), styles),
        kpi_tile("Surplus / Gap", money(difference), styles),
    ]], colWidths=[2.15 * inch, 2.15 * inch, 2.15 * inch])
    tiles.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(tiles)
    story.append(Spacer(1, 10))

    if data.get("balance_sheet_mode", "partial") == "full":
        story.append(callout_box(full_balance_sheet_callout_html(), styles))
        story.append(Spacer(1, 8))

    story.append(callout_box(
        "This report evaluates the five things that can cause a retirement paycut: "
        "relying on the <i>flaw</i> of averages, living too long, dying too soon, "
        "underestimating care costs, and getting sued.",
        styles,
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Five paycut risks at a glance</b>", styles["h2_section"]))
    story.append(Spacer(1, 6))
    story.append(build_risk_dashboard_table(data, narratives, styles, REPORT_BODY_W))
    story.append(Spacer(1, 10))
    append_planning_inputs_glance(story, data, styles)


def generate_premium_client_report(
    data, charts, output_path, report_tier="free", upgrade_url=None
):
    styles = build_styles()
    narratives = classify_all_narratives(data)
    report_tier = (report_tier or "free").lower()
    tier_label = REPORT_TIER_LABELS.get(report_tier, REPORT_TIER_LABELS["free"])

    client_name = data.get("client_name", "") or "Client"
    report_date = data.get("report_date", "") or ""
    footer_left = f"{client_name}  ·  {tier_label}"
    if report_date:
        footer_left += f"  ·  {report_date}"

    doc = SimpleDocTemplate(
        output_path,
        pagesize=LETTER,
        rightMargin=REPORT_MARGIN,
        leftMargin=REPORT_MARGIN,
        topMargin=REPORT_MARGIN,
        bottomMargin=REPORT_MARGIN,
    )
    on_cover, on_later = make_report_page_callbacks({
        "margin": REPORT_MARGIN,
        "page_width": REPORT_PAGE_W,
        "footer_left": footer_left,
    })

    story = []

    append_report_cover(story, data, tier_label, styles, report_tier=report_tier)

    story.append(section_outline("How this report was built", "methodology"))
    story.append(callout_box(methodology_callout_html(report_tier), styles))
    story.append(Spacer(1, 12))

    append_executive_summary(story, data, narratives, styles)

    # 1 — The flaw of averages (sequence of returns)
    story.append(Spacer(1, 14))
    story.append(section_outline("1. Flaw of Averages", "risk_1"))
    story.append(five_thing_heading(
        1,
        "flaw_of_averages",
        "How the sequence—not just the average—of investment returns can change how long your money lasts.",
        styles,
    ))
    append_what_we_measured(story, "flaw_of_averages", data, styles)
    story.append(Spacer(1, 6))
    for chart_flowable in flaw_of_averages_charts_block(charts, styles):
        story.append(chart_flowable)
    append_chart_caption(story, "profile", styles)
    append_chart_caption(story, "allocation", styles)
    append_chart_caption(story, "outcomes", styles)
    story.append(Spacer(1, 4))
    append_flaw_of_averages_example(story, styles, data=data)
    append_narrative_with_premium(
        story,
        "flaw_of_averages",
        narratives["flaw_of_averages"],
        narratives,
        styles,
        report_tier,
        upgrade_url,
        data=data,
    )

    # 2 — Living too long
    story.append(Spacer(1, 14))
    story.append(section_outline("2. Living Too Long", "risk_2"))
    story.append(five_thing_heading(
        2,
        "living_too_long",
        "Whether income and resources can sustain your lifestyle if you live longer than expected.",
        styles,
    ))
    append_what_we_measured(story, "living_too_long", data, styles)
    protected_annual = float(data.get("protected_monthly_income", 0) or 0) * 12
    basic_annual = float(data.get("monthly_living_expenses", 0) or 0) * 12
    story.append(Spacer(1, 6))
    story.append(callout_box(
        f"<b>Coverage snapshot:</b> Protected income <b>{money(protected_annual)}</b>/year vs "
        f"basic living expenses <b>{money(basic_annual)}</b>/year.",
        styles,
    ))
    story.append(Spacer(1, 8))

    living_chart_budget = PIE_FULL_MAX_H + BAR_FULL_MAX_H + 0.12 * inch
    cash_img = chart_image_fit_budget(
        charts.get("cashflow"), CARD_INNER_W, living_chart_budget, 0.5
    )
    cash_cell = (
        chart_card(cash_img)
        if cash_img
        else chart_unavailable_block("Monthly Expenses", styles)
    )
    cov_path = charts.get("coverage")
    cov_img = (
        chart_image_fit_budget(cov_path, CARD_INNER_W, living_chart_budget, 0.5)
        if cov_path
        else None
    )
    story.append(cash_cell)
    append_chart_caption(story, "cashflow", styles)
    story.append(Spacer(1, 6))
    if cov_img:
        story.append(chart_card(cov_img))
    else:
        story.append(chart_unavailable_block("Annual Coverage", styles))
    append_chart_caption(story, "coverage", styles)

    append_longevity_research_evidence(story, styles)

    append_narrative_with_premium(
        story,
        "living_too_long",
        narratives["living_too_long"],
        narratives,
        styles,
        report_tier,
        upgrade_url,
        data=data,
    )

    # 3 — Dying too soon
    story.append(Spacer(1, 14))
    story.append(section_outline("3. Dying Too Soon", "risk_3"))
    story.append(five_thing_heading(
        3,
        "dying_too_soon",
        "Impact on household assets and survivor income if death occurs earlier than planned.",
        styles,
    ))
    append_what_we_measured(story, "dying_too_soon", data, styles)
    story.append(Spacer(1, 8))
    story.append(embed_pie_chart(charts.get("early_death"), styles, "Dying Too Soon", full_width=True))
    append_chart_caption(story, "early_death", styles)
    append_dying_too_soon_research_evidence(story, styles)
    append_narrative_with_premium(
        story,
        "dying_too_soon",
        narratives["dying_too_soon"],
        narratives,
        styles,
        report_tier,
        upgrade_url,
        data=data,
    )

    # 4 — Underestimating care costs
    story.append(Spacer(1, 14))
    story.append(section_outline("4. Underestimating Care Costs", "risk_4"))
    story.append(five_thing_heading(
        4,
        "underestimating_care",
        "Exposure when long-term care costs exceed assumptions or insurance protection.",
        styles,
    ))
    append_what_we_measured(story, "underestimating_care", data, styles)
    story.append(Spacer(1, 8))
    story.append(embed_pie_chart(charts.get("ltc"), styles, "Underestimating Care Costs", full_width=True))
    append_chart_caption(story, "ltc", styles)
    append_underestimating_care_research_evidence(story, styles)
    append_narrative_with_premium(
        story,
        "underestimating_care",
        narratives["underestimating_care"],
        narratives,
        styles,
        report_tier,
        upgrade_url,
        data=data,
    )

    # 5 — Getting sued
    story.append(Spacer(1, 14))
    story.append(section_outline("5. Getting Sued", "risk_5"))
    story.append(five_thing_heading(
        5,
        "getting_sued",
        "Net asset and income exposure after auto, home, and umbrella liability coverage.",
        styles,
    ))
    append_what_we_measured(story, "getting_sued", data, styles)
    story.append(Spacer(1, 8))
    append_getting_sued_research_evidence(story, styles, report_tier, charts=charts)
    append_narrative_with_premium(
        story,
        "getting_sued",
        narratives["getting_sued"],
        narratives,
        styles,
        report_tier,
        upgrade_url,
        data=data,
    )

    story.append(PageBreak())
    story.append(section_outline("Combined Paycut Exposure", "combined_exposure"))
    story.append(section_heading_row(
        "Combined Paycut Exposure",
        "Total self-insurance need across dying too soon, care costs, and liability—things 3, 4, and 5.",
        styles,
    ))
    story.append(Spacer(1, 10))
    story.append(self_insurance_summary_table(data, narratives, styles, REPORT_BODY_W))
    story.append(Spacer(1, 12))

    self_insurance_total = float(data.get("self_insurance_total", 0))
    story.append(modern_card_stack([
        Paragraph("<b>Total self-insurance need</b>", styles["kpi_label"]),
        Paragraph(money(self_insurance_total), styles["kpi_value"]),
    ], well_bg=False))

    story.append(Spacer(1, 14))

    append_flow_block(
        story,
        [
            Paragraph("<b>Need by risk category</b>", styles["h2_section"]),
            Paragraph(
                "Estimated dollars at risk from early death, long-term care, and liability scenarios.",
                styles["muted"],
            ),
        ],
        trailing_spacer=8,
    )
    _sip = charts.get("self_insurance")
    img_si_bar = bar_chart_full_fit(_sip) if _sip else None
    if img_si_bar:
        story.append(chart_card(img_si_bar))
    else:
        story.append(chart_card(self_insurance_bar_fallback(data)))
    append_chart_caption(story, "self_insurance_bar", styles)
    story.append(Spacer(1, 8))

    append_flow_block(
        story,
        [
            Paragraph("<b>Share of investable assets</b>", styles["h2_section"]),
            Paragraph(
                "Self-insurance need versus assets still available after covering those gaps.",
                styles["muted"],
            ),
        ],
        trailing_spacer=8,
    )
    _sipp = charts.get("self_insurance_pie")
    img_si_pie = pie_chart_full_fit(_sipp) if _sipp else None
    if img_si_pie:
        story.append(chart_card(img_si_pie))
    else:
        story.append(chart_card(self_insurance_pie_fallback(data)))
    append_chart_caption(story, "self_insurance_pie", styles)
    append_flow_block(story, self_insurance_pie_caption(data, styles))

    append_narrative(story, "combined_exposure", narratives["combined_exposure"], styles, data=data)

    if float(data.get("net_home_equity", 0) or 0) > 0:
        story.append(Spacer(1, 12))
        story.append(callout_box(NARRATIVE_COPY["balance_sheet_planning_note"], styles))

    story.append(PageBreak())
    if report_tier == "monte_carlo":
        closing_key = "closing_bridge"
    else:
        closing_key = "closing_bridge_free"
    story.append(callout_box(NARRATIVE_COPY[closing_key], styles))

    if report_tier == "options":
        append_options_report_section(story, data, styles)
    elif report_tier == "monte_carlo":
        append_monte_carlo_section(story, data, styles)

    append_assumptions_section(story, data, styles)
    append_disclosure_section(story, report_tier, styles)

    doc.build(story, onFirstPage=on_cover, onLaterPages=on_later)