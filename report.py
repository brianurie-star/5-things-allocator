import base64
import io
import math
import os

from PIL import Image as PILImage
from reportlab.lib import colors
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
from report_narrative import (
    FIVE_THING_TITLES,
    FLAW_SEQUENCE_EXAMPLE_PARAGRAPHS,
    NARRATIVE_COPY,
    classify_all_narratives,
    get_narrative_block,
)
from report_options_solutions import (
    PAID_QUOTE_LINKS,
    PAID_REPORT_EDUCATIONAL_DISCLOSURE,
    PAID_REPORT_FINAL_POSITIONING,
    PAID_REPORT_INTRO,
    PAID_RISK_SECTIONS,
    RISK_SOLUTION_ORDER,
    get_paid_tier_block,
    paid_next_step_url,
)

REPORT_TIER_LABELS = {
    "free": "Free Report",
    "options": "$99 Premium Retirement Optimization Report",
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

# Body width inside SimpleDocTemplate frame; card inner = body minus horizontal padding once
REPORT_BODY_W = 6.5 * inch
CARD_PAD = 14
CARD_INNER_W = REPORT_BODY_W - 2 * CARD_PAD
STRAT_GUTTER = 8
STRAT_HALF_FRAME_W = (REPORT_BODY_W - STRAT_GUTTER) / 2
CHART_TILE_PAD = 5
STRAT_IMG_HALF_MAX_W = STRAT_HALF_FRAME_W - 2 * CHART_TILE_PAD
# Max display size per chart role (uniform scale to fit inside box)
PIE_HALF_MAX_H = 3.4 * inch
PIE_FULL_MAX_H = 3.65 * inch
BAR_FULL_MAX_H = 3.75 * inch
OUTCOMES_MAX_H = 3.35 * inch
# Compact outcomes under profile/allocation so all three fit on one report page
OUTCOMES_STRATEGY_MAX_H = 2.15 * inch
ASSUMP_COL_GUTTER = 14
ASSUMP_COL_W = (CARD_INNER_W - ASSUMP_COL_GUTTER) / 2
REPORT_HERO_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "static",
    "hero-background.png",
)
COVER_HERO_MAX_H = 2.85 * inch


def money(v):
    return f"${float(v or 0):,.0f}"


def _safe_float(value, default=0.0):
    try:
        if value in ("", None):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


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


def chart_image_fit(path, max_width, max_height):
    """
    Embed chart PNG without distortion. Forcing unequal width/height squashes pie charts
    into arcs; we scale uniformly to fit inside the max box (same aspect as canvas export).
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
    scale = min(mw / w_px, mh / h_px)
    dw = w_px * scale
    dh = h_px * scale
    return Image(path, width=dw, height=dh)


def pie_chart_half_fit(path):
    """Side-by-side pies (profile/allocation, lawsuit pair, etc.)."""
    return chart_image_fit(path, STRAT_IMG_HALF_MAX_W, PIE_HALF_MAX_H)


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
    """Site hero landscape for PDF cover (uniform scale, full body width)."""
    return chart_image_fit(REPORT_HERO_PATH, REPORT_BODY_W, COVER_HERO_MAX_H)


def append_report_cover(story, data, tier_label, styles):
    hero = report_cover_hero_image()
    if hero:
        hero_row = Table([[hero]], colWidths=[REPORT_BODY_W])
        hero_row.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(hero_row)
        story.append(Spacer(1, 14))
    else:
        story.append(Spacer(1, 0.5 * inch))

    story.append(Paragraph("READY TO RETIRE?", styles["title"]))
    story.append(Paragraph("Personalized Retirement Readiness Report", styles["muted"]))
    story.append(Paragraph(tier_label, styles["muted"]))
    story.append(Paragraph("The five things that can cause a paycut", styles["muted"]))
    story.append(Spacer(1, 18))
    story.append(Paragraph(f"<b>Client:</b> {data.get('client_name', '')}", styles["body"]))
    story.append(Paragraph(f"<b>Date:</b> {data.get('report_date', '')}", styles["body"]))
    story.append(PageBreak())


def nice_axis_max(value):
    if value is None or value <= 0:
        return 1.0
    exp = 10 ** math.floor(math.log10(value))
    step = exp if value / exp <= 10 else exp * 2
    return math.ceil(value / step) * step * 1.02


def build_styles():
    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=30,
            textColor=colors.HexColor(THEME["text"]),
            spaceAfter=12,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=22,
            textColor=colors.HexColor(THEME["text"]),
            spaceAfter=8,
        ),
        "h2_section": ParagraphStyle(
            "h2_section",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor(THEME["text"]),
            spaceBefore=0,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#334155"),
            spaceAfter=8,
        ),
        "muted": ParagraphStyle(
            "muted",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor(THEME["muted"]),
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
            fontName="Helvetica-Oblique",
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
        colWidths=[6.5 * inch - 28],
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


def narrative_section_block(section_key, tier, styles):
    block = get_narrative_block(section_key, tier)
    if not block:
        return []

    headline_style = narrative_headline_style(tier, styles)
    flowables = [
        Paragraph(f'<b>{block.get("headline", "")}</b>', headline_style),
    ]

    for para in block.get("paragraphs", []):
        flowables.append(Paragraph(para, styles["body"]))

    for bullet in block.get("bullets", []):
        flowables.append(Paragraph(f"• {bullet}", styles["body"]))

    for para in block.get("after_bullets", []):
        flowables.append(Paragraph(para, styles["body"]))

    quote = block.get("quote")
    if quote:
        flowables.append(Spacer(1, 6))
        flowables.append(pull_quote_box(f'"{quote}"', styles))

    return flowables


def append_narrative(story, section_key, tier, styles):
    parts = narrative_section_block(section_key, tier, styles)
    if not parts:
        return
    story.append(Spacer(1, 12))
    story.append(modern_card_stack(parts))


def append_paid_risk_solutions(story, section_key, narratives, styles, include_research=False):
    """Tier-matched strategies and next-step link for premium ($99) reports."""
    if section_key not in PAID_RISK_SECTIONS:
        return

    meta = PAID_RISK_SECTIONS[section_key]
    tier = narratives.get(section_key, "on_track")
    block = get_paid_tier_block(section_key, tier)
    next_step_url = paid_next_step_url(meta["next_step_key"])

    parts = []
    if include_research and meta.get("research"):
        parts.append(Paragraph("<b>Research context</b>", styles["h2_section"]))
        parts.append(Spacer(1, 4))
        for paragraph in meta["research"]:
            parts.append(Paragraph(paragraph, styles["body"]))
            parts.append(Spacer(1, 4))
        parts.append(Spacer(1, 6))

    parts.extend([
        Paragraph(f"<b>{block['headline']}</b>", styles["h2_section"]),
        Paragraph(block["summary"], styles["body"]),
        Spacer(1, 6),
        Paragraph("<b>Options to consider</b>", styles["h2_section"]),
    ])
    for bullet in block["bullets"]:
        parts.append(Paragraph(f"• {bullet}", styles["body"]))
    parts.append(Spacer(1, 8))
    parts.append(Paragraph(
        f'<b>Request a quote / next step:</b> '
        f'<a href="{next_step_url}" color="#1B2D47"><u>{meta["next_step_label"]}</u></a>',
        styles["body"],
    ))
    parts.append(Paragraph(
        f'<font color="{THEME["muted"]}">{next_step_url}</font>',
        styles["muted"],
    ))
    story.append(Spacer(1, 10))
    story.append(modern_card_stack(parts))


def append_paid_quote_links_section(story, styles):
    """Summary of all quote and consultation links for the premium report."""
    story.append(Paragraph("<b>Request Quotes &amp; Next Steps</b>", styles["h1"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "The links below correspond to the strategies discussed in this report. "
        "They are provided for educational planning—not as a solicitation.",
        styles["body"],
    ))
    story.append(Spacer(1, 10))

    parts = []
    for item in PAID_QUOTE_LINKS:
        url = paid_next_step_url(item["key"])
        parts.append(Paragraph(
            f'• <b>{item["label"]}</b> <font color="{THEME["muted"]}">({item["note"]})</font><br/>'
            f'<a href="{url}" color="#1B2D47"><u>{url}</u></a>',
            styles["body"],
        ))
        parts.append(Spacer(1, 8))
    story.append(modern_card_stack(parts))
    story.append(Spacer(1, 14))


def append_narrative_with_premium(story, section_key, tier, narratives, styles, report_tier):
    append_narrative(story, section_key, tier, styles)
    if report_tier == "options" and section_key in RISK_SOLUTION_ORDER:
        append_paid_risk_solutions(story, section_key, narratives, styles)


def five_thing_heading(number, section_key, subtitle, styles):
    title = FIVE_THING_TITLES[section_key]
    return section_heading_row(f"{number}. {title}", subtitle, styles)


def static_asset_path(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", filename)


def append_flaw_of_averages_example(story, styles):
    """Sequence-of-returns illustration (Scenario A vs B) for Thing 1."""
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "<b>Example: Same average return, different outcomes</b>",
            styles["h2_section"],
        )
    )
    story.append(Spacer(1, 6))
    for paragraph in FLAW_SEQUENCE_EXAMPLE_PARAGRAPHS:
        story.append(Paragraph(paragraph, styles["body"]))
        story.append(Spacer(1, 8))

    img_path = static_asset_path("sequence-returns-example.png")
    img = chart_image_fit(img_path, CARD_INNER_W, PIE_FULL_MAX_H)
    if img:
        story.append(chart_card(img, width=REPORT_BODY_W))
    else:
        story.append(
            callout_box(
                "Scenario comparison table unavailable. Both scenarios use a 5% arithmetic mean return; "
                "early losses shorten portfolio life while early gains extend it.",
                styles,
            )
        )


def callout_box(text, styles):
    table = Table(
        [[Paragraph(text, styles["body"])]],
        colWidths=[6.5 * inch],
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
    """Investment profile, asset allocation, and outcomes on one page."""
    img_prof = pie_chart_half_fit(charts.get("profile"))
    img_alloc = pie_chart_half_fit(charts.get("allocation"))
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
    block = [pie_row, Spacer(1, 6), outcomes_chart_block(charts, styles, compact=True)]
    return KeepTogether(block)


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
    accent_w = 0.1 * inch
    text_col_w = 6.5 * inch - accent_w
    accent = Table(
        [[Paragraph("", styles["body"])]],
        colWidths=[accent_w],
        rowHeights=[44],
    )
    accent.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(THEME["accent"])),
        ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    titles = Table(
        [
            [Paragraph(f"<b>{title}</b>", styles["h1"])],
            [Paragraph(subtitle or "", styles["muted"])],
        ],
        colWidths=[max(text_col_w - 24, 72)],
    )
    titles.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    inner = Table([[accent, titles]], colWidths=[accent_w, text_col_w])
    inner.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), 0),
        ("TOPPADDING", (0, 0), (0, -1), 0),
        ("BOTTOMPADDING", (0, 0), (0, -1), 0),
        ("LEFTPADDING", (1, 0), (-1, -1), 0),
        ("RIGHTPADDING", (1, 0), (-1, -1), 0),
    ]))
    row = Table([[inner]], colWidths=[REPORT_BODY_W])
    row.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(THEME["card"])),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor(THEME["border"])),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
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


def _years_until_depleted(initial, annual_withdrawal, annual_return, years_max=40):
    balance = initial
    withdrawal = annual_withdrawal
    for year in range(1, years_max + 1):
        if balance <= 0:
            return year - 1
        balance -= withdrawal
        if balance <= 0:
            return year
        balance *= 1 + annual_return
        withdrawal *= 1.03
    return years_max


def append_disclosure_section(story, tier, styles):
    text = DISCLOSURE_BY_TIER.get(tier, DISCLOSURE_BY_TIER["free"])
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
    """$99 tier: research summaries for each paycut risk (solutions appear inline in main sections)."""
    story.append(
        Paragraph(
            "<b>Turning Risk Exposure into Income Stability</b>",
            styles["h2_section"],
        )
    )
    story.append(Spacer(1, 8))
    for paragraph in PAID_REPORT_INTRO:
        story.append(Paragraph(paragraph, styles["body"]))
        story.append(Spacer(1, 6))
    story.append(Spacer(1, 10))

    for section_key in RISK_SOLUTION_ORDER:
        meta = PAID_RISK_SECTIONS[section_key]
        story.append(
            Paragraph(
                f"<b>{meta['number']}. {meta['title']}</b>",
                styles["h1"],
            )
        )
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>{meta['subtitle']}</b>", styles["h2_section"]))
        story.append(Spacer(1, 8))
        append_paid_risk_solutions(
            story, section_key, narratives, styles, include_research=True
        )
        story.append(Spacer(1, 14))


def append_paid_report_closing(story, styles):
    story.append(Paragraph("<b>Final Positioning</b>", styles["h1"]))
    story.append(Spacer(1, 8))
    for paragraph in PAID_REPORT_FINAL_POSITIONING:
        story.append(Paragraph(paragraph, styles["body"]))
        story.append(Spacer(1, 6))
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Important Disclosures</b>", styles["h1"]))
    story.append(Spacer(1, 8))
    for paragraph in PAID_REPORT_EDUCATIONAL_DISCLOSURE:
        story.append(Paragraph(paragraph, styles["body"]))
        story.append(Spacer(1, 6))


def append_options_report_section(story, data, styles):
    investable = float(data.get("investable_assets", 0) or 0)
    prefix = data.get("risk_profile") or "growth"
    mean_return = float(data.get(f"{prefix}_mean", 9.89) or 9.89) / 100.0

    narratives = classify_all_narratives(data)

    story.append(PageBreak())
    story.append(
        Paragraph("<b>$99 Premium Retirement Optimization Report</b>", styles["h1"])
    )
    story.append(Spacer(1, 10))
    append_paid_optimization_sections(story, narratives, styles)
    append_paid_quote_links_section(story, styles)

    story.append(Paragraph("<b>Withdrawal-Rate Comparison</b>", styles["h1"]))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "The table below illustrates fixed withdrawal-rate scenarios using your investable assets. "
            f"Each scenario assumes average returns of {mean_return * 100:.1f}% per year with 3% "
            "inflation on withdrawals—not Monte Carlo probabilities.",
            styles["muted"],
        )
    )
    story.append(Spacer(1, 10))

    rows = [
        [
            Paragraph("<b>Withdrawal rate</b>", styles["body"]),
            Paragraph("<b>Initial annual income</b>", styles["body"]),
            Paragraph("<b>Est. years assets last</b>", styles["body"]),
        ]
    ]
    for rate_pct in (3.0, 3.5, 4.0, 4.5, 5.0, 6.0):
        rate = rate_pct / 100.0
        annual = investable * rate
        years_left = _years_until_depleted(investable, annual, mean_return)
        rows.append([
            Paragraph(f"{rate_pct:.1f}%", styles["body"]),
            Paragraph(money(annual), styles["body"]),
            Paragraph(f"{years_left} years", styles["body"]),
        ])

    table = Table(rows, colWidths=[1.4 * inch, 2.2 * inch, 2.0 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#E2E8F0")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(modern_card_stack([table], width=REPORT_BODY_W))
    append_paid_report_closing(story, styles)


def append_monte_carlo_section(story, data, styles):
    mc = run_retirement_monte_carlo(data)

    story.append(Spacer(1, 14))
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


def generate_premium_client_report(data, charts, output_path, report_tier="free"):
    styles = build_styles()
    narratives = classify_all_narratives(data)
    report_tier = (report_tier or "free").lower()
    tier_label = REPORT_TIER_LABELS.get(report_tier, REPORT_TIER_LABELS["free"])

    doc = SimpleDocTemplate(
        output_path,
        pagesize=LETTER,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    story = []

    balance_sheet_mode = data.get("balance_sheet_mode", "partial")
    if balance_sheet_mode == "full":
        monthly_income = float(data.get("full_balance_sheet_monthly_income", 0))
    else:
        monthly_income = float(data.get("monthly_income", 0))

    monthly_expenses = float(data.get("monthly_expenses", 0))
    difference = monthly_income - monthly_expenses

    append_report_cover(story, data, tier_label, styles)

    story.append(Paragraph("Executive Summary", styles["h1"]))

    tiles = Table([[
        kpi_tile("Monthly Income", money(monthly_income), styles),
        kpi_tile("Monthly Expenses", money(monthly_expenses), styles),
        kpi_tile("Surplus / Gap", money(difference), styles),
    ]], colWidths=[2.15 * inch, 2.15 * inch, 2.15 * inch])

    tiles.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    story.append(tiles)
    story.append(Spacer(1, 12))
    story.append(callout_box(
        "This report evaluates the five things that can cause a retirement paycut: "
        "relying on the <i>flaw</i> of averages, living too long, dying too soon, "
        "underestimating care costs, and getting sued.",
        styles,
    ))

    # 1 — The flaw of averages (sequence of returns)
    story.append(Spacer(1, 14))
    story.append(five_thing_heading(
        1,
        "flaw_of_averages",
        "How the sequence—not just the average—of investment returns can change how long your money lasts.",
        styles,
    ))
    story.append(Spacer(1, 8))
    story.append(flaw_of_averages_charts_block(charts, styles))
    story.append(Spacer(1, 8))
    append_flaw_of_averages_example(story, styles)
    append_narrative_with_premium(
        story, "flaw_of_averages", narratives["flaw_of_averages"], narratives, styles, report_tier
    )

    # 2 — Living too long
    story.append(Spacer(1, 14))
    story.append(five_thing_heading(
        2,
        "living_too_long",
        "Whether income and resources can sustain your lifestyle if you live longer than expected.",
        styles,
    ))
    story.append(Spacer(1, 10))

    story.append(embed_pie_chart(charts.get("cashflow"), styles, "Monthly Expenses", full_width=True))

    cov_path = charts.get("coverage")
    cov_img = bar_chart_full_fit(cov_path) if cov_path else None
    story.append(Spacer(1, 8))
    if cov_img:
        story.append(chart_card(cov_img))
    else:
        story.append(chart_unavailable_block("Annual Coverage", styles))

    append_narrative_with_premium(
        story, "living_too_long", narratives["living_too_long"], narratives, styles, report_tier
    )

    # 3 — Dying too soon
    story.append(Spacer(1, 14))
    story.append(five_thing_heading(
        3,
        "dying_too_soon",
        "Impact on household assets and survivor income if death occurs earlier than planned.",
        styles,
    ))
    story.append(Spacer(1, 10))
    story.append(embed_pie_chart(charts.get("early_death"), styles, "Dying Too Soon", full_width=True))
    append_narrative_with_premium(
        story, "dying_too_soon", narratives["dying_too_soon"], narratives, styles, report_tier
    )

    # 4 — Underestimating care costs
    story.append(Spacer(1, 14))
    story.append(five_thing_heading(
        4,
        "underestimating_care",
        "Exposure when long-term care costs exceed assumptions or insurance protection.",
        styles,
    ))
    story.append(Spacer(1, 10))
    story.append(embed_pie_chart(charts.get("ltc"), styles, "Underestimating Care Costs", full_width=True))
    append_narrative_with_premium(
        story, "underestimating_care", narratives["underestimating_care"], narratives, styles, report_tier
    )

    # 5 — Getting sued
    story.append(Spacer(1, 14))
    story.append(five_thing_heading(
        5,
        "getting_sued",
        "Net asset and income exposure after auto, home, and umbrella liability coverage.",
        styles,
    ))
    story.append(Spacer(1, 10))
    lawsuit_row = Table(
        [[
            risk_chart_cell("lawsuit", charts, styles),
            risk_chart_cell("lawsuit_income", charts, styles),
        ]],
        colWidths=[STRAT_HALF_FRAME_W, STRAT_HALF_FRAME_W],
    )
    lawsuit_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(lawsuit_row)
    append_narrative_with_premium(
        story, "getting_sued", narratives["getting_sued"], narratives, styles, report_tier
    )

    story.append(PageBreak())
    story.append(section_heading_row(
        "Combined Paycut Exposure",
        "Total self-insurance need across dying too soon, care costs, and liability—things 3, 4, and 5.",
        styles,
    ))
    story.append(Spacer(1, 14))

    self_insurance_total = float(data.get("self_insurance_total", 0))
    story.append(modern_card_stack([
        Paragraph("<b>Total self-insurance need</b>", styles["kpi_label"]),
        Paragraph(money(self_insurance_total), styles["kpi_value"]),
    ], well_bg=False))

    story.append(Spacer(1, 14))

    bar_block = [
        Paragraph("<b>Need by risk category</b>", styles["h2_section"]),
        Paragraph(
            "Estimated dollars at risk from early death, long-term care, and liability scenarios.",
            styles["muted"],
        ),
        Spacer(1, 8),
    ]
    _sip = charts.get("self_insurance")
    img_si_bar = bar_chart_full_fit(_sip) if _sip else None
    if img_si_bar:
        bar_block.append(img_si_bar)
    else:
        bar_block.append(self_insurance_bar_fallback(data))
    story.append(modern_card_stack(bar_block))

    story.append(Spacer(1, 10))

    pie_block = [
        Paragraph("<b>Share of investable assets</b>", styles["h2_section"]),
        Paragraph(
            "Self-insurance need versus assets still available after covering those gaps.",
            styles["muted"],
        ),
        Spacer(1, 8),
    ]
    _sipp = charts.get("self_insurance_pie")
    img_si_pie = pie_chart_full_fit(_sipp) if _sipp else None
    if img_si_pie:
        pie_block.append(chart_card(img_si_pie))
    else:
        pie_block.append(self_insurance_pie_fallback(data))
    pie_block.extend(self_insurance_pie_caption(data, styles))
    story.append(modern_card_stack(pie_block))

    append_narrative(story, "combined_exposure", narratives["combined_exposure"], styles)

    if float(data.get("net_home_equity", 0) or 0) > 0:
        story.append(Spacer(1, 12))
        story.append(callout_box(NARRATIVE_COPY["balance_sheet_planning_note"], styles))

    story.append(PageBreak())
    story.append(callout_box(NARRATIVE_COPY["closing_bridge"], styles))
    story.append(Spacer(1, 16))
    story.append(Paragraph("Recommended Next Steps", styles["h1"]))

    for item in [
        "Increase protected income for essential expenses",
        "Reduce reliance on market withdrawals",
        "Review insurance coverage",
        "Plan for survivor income changes",
        "Re-evaluate plan annually",
    ]:
        story.append(Paragraph(f"• {item}", styles["body"]))

    if report_tier == "options":
        append_options_report_section(story, data, styles)
    elif report_tier == "monte_carlo":
        append_monte_carlo_section(story, data, styles)

    append_assumptions_section(story, data, styles)
    append_disclosure_section(story, report_tier, styles)

    doc.build(story)