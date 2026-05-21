"""
Report presentation enhancements (executive dashboard, headers, bookmarks, captions).

Revert: remove this module and imports/usages in report.py / report_narrative.py.
"""

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Flowable, Paragraph, Spacer, Table, TableStyle

from report_disclosures import DISCLOSURE_BY_TIER
from report_narrative import FIVE_THING_TITLES

# Re-export width constants from report at import time in functions to avoid circular import


TIER_DISPLAY = {
    "on_track": ("On Track", "#15803D", "#DCFCE7"),
    "at_risk": ("At Risk", "#B45309", "#FEF3C7"),
    "high_risk": ("High Risk", "#B91C1C", "#FEE2E2"),
}

RISK_SECTION_ORDER = [
    ("flaw_of_averages", "1"),
    ("living_too_long", "2"),
    ("dying_too_soon", "3"),
    ("underestimating_care", "4"),
    ("getting_sued", "5"),
]

CHART_CAPTIONS = {
    "profile": "Stock vs bond/alternative mix for your selected investment profile.",
    "allocation": "Split between guaranteed income assets and unprotected investments.",
    "outcomes": "Illustrative return ranges using your profile mean return and standard deviation (not Monte Carlo).",
    "cashflow": "Monthly living expenses, protection costs, estimated taxes, and extras.",
    "coverage": "Protected annual income compared with basic living expenses (annual).",
    "early_death": "Share of investable assets potentially at risk if death occurs earlier than planned.",
    "ltc": "Share of investable assets potentially needed for a modeled long-term care stay.",
    "lawsuit": "Net investable assets at risk after liability limits in the lawsuit scenario.",
    "lawsuit_income": "Annual income categories relative to the lawsuit scenario modeled.",
    "self_insurance_bar": "Dollar exposure by event risk before insurance offsets.",
    "self_insurance_pie": "Total self-insurance need compared with remaining investable assets.",
}

WHAT_WE_MEASURED = {
    "flaw_of_averages": (
        "Based on your {profile} profile, {guaranteed_pct:.0f}% in guaranteed income assets, "
        "and {unprotected_pct:.0f}% in unprotected investments."
    ),
    "living_too_long": (
        "Based on {balance_label}: monthly income {income}, expenses {expenses}, "
        "surplus/gap {surplus}."
    ),
    "dying_too_soon": (
        "Early-death exposure of {at_risk} ({pct:.0f}% of {assets} investable assets)."
    ),
    "underestimating_care": (
        "Modeled {ltc_years}-year care stay at {ltc_monthly}/month; exposure {at_risk} ({pct:.0f}% of assets)."
    ),
    "getting_sued": (
        "Lawsuit scenario {award}; net assets at risk {at_risk} ({pct:.0f}% of investable assets)."
    ),
}


class OutlineEntry(Flowable):
    """PDF bookmark (outline) entry with zero layout footprint."""

    def __init__(self, title, key, level=0):
        self.title = title
        self.key = key
        self.level = level

    def wrap(self, availWidth, availHeight):
        return 0, 0

    def draw(self):
        canv = self.canv
        canv.bookmarkPage(self.key)
        canv.addOutlineEntry(self.title, self.key, level=self.level, closed=False)


def _money(v):
    return f"${float(v or 0):,.0f}"


def _pct_ratio(value):
    v = float(value or 0)
    if abs(v) > 1:
        return v / 100.0
    return v


def tier_badge_html(tier):
    label, fg, bg = TIER_DISPLAY.get(tier, ("—", "#334155", "#F1F5F9"))
    return (
        f'<font color="{fg}"><b>{label}</b></font>'
        f' <font size="8" color="{fg}">●</font>'
    )


def risk_metric_line(section_key, data, narratives):
    investable = float(data.get("investable_assets", 0) or 0)
    tier = narratives.get(section_key, "on_track")

    if section_key == "flaw_of_averages":
        unprotected = float(data.get("stock_assets", 0) or 0) + float(
            data.get("bond_assets", 0) or 0
        )
        pct = (unprotected / investable * 100) if investable > 0 else 0
        return f"{pct:.0f}% unprotected · {tier_badge_html(tier)}"

    if section_key == "living_too_long":
        if data.get("balance_sheet_mode", "partial") == "full":
            income = float(data.get("full_balance_sheet_monthly_income", 0) or 0)
        else:
            income = float(data.get("monthly_income", 0) or 0)
        expenses = float(data.get("monthly_expenses", 0) or 0)
        gap = income - expenses
        sign = "surplus" if gap >= 0 else "gap"
        return f"{_money(abs(gap))} monthly {sign} · {tier_badge_html(tier)}"

    if section_key == "dying_too_soon":
        at_risk = float(data.get("assets_at_risk_early_death", 0) or 0)
        pct = (at_risk / investable * 100) if investable > 0 else 0
        return f"{_money(at_risk)} at risk ({pct:.0f}%) · {tier_badge_html(tier)}"

    if section_key == "underestimating_care":
        at_risk = float(data.get("assets_at_risk_ltc", 0) or 0)
        pct = (at_risk / investable * 100) if investable > 0 else 0
        return f"{_money(at_risk)} at risk ({pct:.0f}%) · {tier_badge_html(tier)}"

    if section_key == "getting_sued":
        at_risk = float(data.get("net_at_risk_lawsuit", 0) or 0)
        pct = (at_risk / investable * 100) if investable > 0 else 0
        return f"{_money(at_risk)} net at risk ({pct:.0f}%) · {tier_badge_html(tier)}"

    return tier_badge_html(tier)


def build_risk_dashboard_table(data, narratives, styles, body_width):
    header = [
        Paragraph("<b>Paycut risk</b>", styles["muted"]),
        Paragraph("<b>Status</b>", styles["muted"]),
        Paragraph("<b>Key measure</b>", styles["muted"]),
    ]
    rows = [header]
    col_risk = body_width * 0.38
    col_status = body_width * 0.22
    col_metric = body_width - col_risk - col_status

    for section_key, _num in RISK_SECTION_ORDER:
        tier = narratives.get(section_key, "on_track")
        title = FIVE_THING_TITLES.get(section_key, section_key)
        title_plain = (
            title.replace("<i>", "").replace("</i>", "").replace("  ", " ")
        )
        status_label, fg, _bg = TIER_DISPLAY.get(tier, ("—", "#334155", "#F1F5F9"))
        rows.append([
            Paragraph(title_plain, styles["body"]),
            Paragraph(f'<font color="{fg}"><b>{status_label}</b></font>', styles["body"]),
            Paragraph(risk_metric_line(section_key, data, narratives), styles["body"]),
        ])

    combined_tier = narratives.get("combined_exposure", "on_track")
    status_label, fg, _bg = TIER_DISPLAY.get(combined_tier, ("—", "#334155", "#F1F5F9"))
    need = float(data.get("self_insurance_total", 0) or 0)
    assets = float(data.get("investable_assets", 0) or 0)
    pct = (need / assets * 100) if assets > 0 else 0
    rows.append([
        Paragraph("<b>Combined self-insurance</b>", styles["body"]),
        Paragraph(f'<font color="{fg}"><b>{status_label}</b></font>', styles["body"]),
        Paragraph(
            f"{_money(need)} total ({pct:.0f}% of assets) · {tier_badge_html(combined_tier)}",
            styles["body"],
        ),
    ])

    table = Table(rows, colWidths=[col_risk, col_status, col_metric])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#E2E8F0")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def planning_inputs_glance_rows(data):
    balance_mode = data.get("balance_sheet_mode", "partial")
    balance_label = (
        "Full balance sheet"
        if balance_mode == "full"
        else "Partial balance sheet"
    )
    profile = data.get("profile_label") or data.get("risk_profile") or "growth"
    return [
        ("Balance sheet view", balance_label),
        ("Investment profile", str(profile)),
        (
            "Guaranteed / unprotected withdrawal",
            f"{_pct_ratio(data.get('guaranteed_withdrawal_rate')) * 100:.1f}% / "
            f"{_pct_ratio(data.get('unprotected_withdrawal_rate')) * 100:.1f}%",
        ),
        ("Investable assets", _money(data.get("investable_assets"))),
        ("Lawsuit scenario", _money(data.get("lawsuit_award"))),
        ("LTC scenario", (
            f"{int(float(data.get('ltc_years') or 0))} years at "
            f"{_money(data.get('monthly_ltc_cost'))}/mo"
        )),
    ]


def monthly_income_for_data(data):
    if data.get("balance_sheet_mode", "partial") == "full":
        return float(data.get("full_balance_sheet_monthly_income", 0) or 0)
    return float(data.get("monthly_income", 0) or 0)


def methodology_callout_html(report_tier):
    text = DISCLOSURE_BY_TIER.get(report_tier, DISCLOSURE_BY_TIER["free"])
    return f"<b>How this report was built</b><br/><br/>{text}"


def full_balance_sheet_callout_html():
    return (
        "<b>Full balance sheet view:</b> Income and investable assets in this report "
        "include accessible home equity per your allocator settings."
    )


def what_we_measured_text(section_key, data):
    investable = float(data.get("investable_assets", 0) or 0)
    profile = data.get("profile_label") or data.get("risk_profile") or "growth"
    guaranteed_alloc = _pct_ratio(data.get("guaranteed_income_allocation")) * 100
    unprotected = float(data.get("stock_assets", 0) or 0) + float(
        data.get("bond_assets", 0) or 0
    )
    unprotected_pct = (unprotected / investable * 100) if investable > 0 else 0

    if section_key == "flaw_of_averages":
        return WHAT_WE_MEASURED["flaw_of_averages"].format(
            profile=profile,
            guaranteed_pct=guaranteed_alloc,
            unprotected_pct=unprotected_pct,
        )

    if section_key == "living_too_long":
        if data.get("balance_sheet_mode", "partial") == "full":
            income = float(data.get("full_balance_sheet_monthly_income", 0) or 0)
            balance_label = "full balance sheet income"
        else:
            income = float(data.get("monthly_income", 0) or 0)
            balance_label = "partial balance sheet income"
        expenses = float(data.get("monthly_expenses", 0) or 0)
        return WHAT_WE_MEASURED["living_too_long"].format(
            balance_label=balance_label,
            income=_money(income),
            expenses=_money(expenses),
            surplus=_money(income - expenses),
        )

    if section_key == "dying_too_soon":
        at_risk = float(data.get("assets_at_risk_early_death", 0) or 0)
        pct = (at_risk / investable * 100) if investable > 0 else 0
        return WHAT_WE_MEASURED["dying_too_soon"].format(
            at_risk=_money(at_risk),
            pct=pct,
            assets=_money(investable),
        )

    if section_key == "underestimating_care":
        at_risk = float(data.get("assets_at_risk_ltc", 0) or 0)
        pct = (at_risk / investable * 100) if investable > 0 else 0
        return WHAT_WE_MEASURED["underestimating_care"].format(
            ltc_years=int(float(data.get("ltc_years") or 0)),
            ltc_monthly=_money(data.get("monthly_ltc_cost")),
            at_risk=_money(at_risk),
            pct=pct,
        )

    if section_key == "getting_sued":
        at_risk = float(data.get("net_at_risk_lawsuit", 0) or 0)
        pct = (at_risk / investable * 100) if investable > 0 else 0
        return WHAT_WE_MEASURED["getting_sued"].format(
            award=_money(data.get("lawsuit_award")),
            at_risk=_money(at_risk),
            pct=pct,
        )

    return ""


def append_what_we_measured(story, section_key, data, styles):
    text = what_we_measured_text(section_key, data)
    if not text:
        return
    story.append(Paragraph(f"<i>What we measured:</i> {text}", styles["muted"]))
    story.append(Spacer(1, 6))


def append_chart_caption(story, chart_key, styles):
    text = CHART_CAPTIONS.get(chart_key)
    if not text:
        return
    story.append(Spacer(1, 4))
    story.append(Paragraph(text, styles["muted"]))
    story.append(Spacer(1, 6))


def research_key_points_flowables(key_points, styles):
    if not key_points:
        return []
    parts = [Paragraph("<b>Key research points</b>", styles["h2_section"]), Spacer(1, 4)]
    for item in key_points:
        parts.append(Paragraph(f"• {item}", styles["body"]))
    return parts


def self_insurance_summary_table(data, narratives, styles, body_width):
    investable = float(data.get("investable_assets", 0) or 0)
    rows = [[
        Paragraph("<b>Risk</b>", styles["muted"]),
        Paragraph("<b>Exposure</b>", styles["muted"]),
        Paragraph("<b>% of assets</b>", styles["muted"]),
        Paragraph("<b>Tier</b>", styles["muted"]),
    ]]
    events = [
        ("dying_too_soon", "Dying too soon", "assets_at_risk_early_death"),
        ("underestimating_care", "Care costs", "assets_at_risk_ltc"),
        ("getting_sued", "Getting sued", "net_at_risk_lawsuit"),
    ]
    for key, label, field in events:
        amount = float(data.get(field, 0) or 0)
        pct = (amount / investable * 100) if investable > 0 else 0
        tier = narratives.get(key, "on_track")
        status_label, fg, _bg = TIER_DISPLAY.get(tier, ("—", "#334155", "#F1F5F9"))
        rows.append([
            Paragraph(label, styles["body"]),
            Paragraph(_money(amount), styles["body"]),
            Paragraph(f"{pct:.0f}%", styles["body"]),
            Paragraph(f'<font color="{fg}"><b>{status_label}</b></font>', styles["body"]),
        ])
    total = float(data.get("self_insurance_total", 0) or 0)
    pct_total = (total / investable * 100) if investable > 0 else 0
    combined_tier = narratives.get("combined_exposure", "on_track")
    status_label, fg, _bg = TIER_DISPLAY.get(combined_tier, ("—", "#334155", "#F1F5F9"))
    rows.append([
        Paragraph("<b>Total self-insurance</b>", styles["body"]),
        Paragraph(f"<b>{_money(total)}</b>", styles["body"]),
        Paragraph(f"<b>{pct_total:.0f}%</b>", styles["body"]),
        Paragraph(f'<font color="{fg}"><b>{status_label}</b></font>', styles["body"]),
    ])
    col_w = body_width / 4
    table = Table(rows, colWidths=[col_w] * 4)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#E2E8F0")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def make_report_page_callbacks(doc_meta):
    """Return (onFirstPage, onLaterPages) for SimpleDocTemplate.build."""

    def _draw_footer(canvas, doc, show_page_number=True):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#5C6B7F"))
        left = doc_meta["margin"]
        right = doc_meta["page_width"] - doc_meta["margin"]
        y = 0.45 * inch
        canvas.drawString(left, y, doc_meta.get("footer_left", ""))
        if show_page_number:
            canvas.drawRightString(right, y, f"Page {doc.page}")
        canvas.restoreState()

    def on_cover(canvas, doc):
        pass

    def on_later(canvas, doc):
        _draw_footer(canvas, doc, show_page_number=True)

    return on_cover, on_later


def section_outline(title, key):
    return OutlineEntry(title, key, level=0)
