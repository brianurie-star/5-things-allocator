"""
Modular report narrative copy and tier classification for PDF export.
The five paycut risks match the Ready to Retire presentation framework.
"""

FLAW_SEQUENCE_EXAMPLE_PARAGRAPHS = [
    (
        "The flaw in relying solely on a basic calculator you can find on hundreds of websites is that "
        "it forces you to select an average growth rate for your savings. While varied returns do not "
        "skew the results much when you are saving for retirement, the sequence of returns that make up "
        "an average can make a huge difference."
    ),
    (
        "Take the sequence of returns in Scenario A. They add up to a 5% (arithmetic mean) average. But, "
        "because the first three years suffered 10% losses, the funds—when withdrawing 3.5% from $1M the "
        "first year, then adjusting for inflation thereafter—run out in 24 years."
    ),
    (
        "Conversely, if we flip the sequence, as in Scenario B, not only do the funds last, there is over "
        "a million dollars left after 30 years with the exact same withdrawals, even though the average "
        "growth rate (again arithmetic mean) is the same."
    ),
]

FIVE_THING_TITLES = {
    "flaw_of_averages": "Relying on the <i>Flaw</i> of Averages",
    "living_too_long": "Living Too Long",
    "dying_too_soon": "Dying Too Soon",
    "underestimating_care": "Underestimating Care Costs",
    "getting_sued": "Getting Sued",
}


def _f(data, key, default=0.0):
    try:
        v = data.get(key, default)
        if v in ("", None):
            return float(default)
        return float(v)
    except (TypeError, ValueError):
        return float(default)


def _monthly_income_for_mode(data):
    if data.get("balance_sheet_mode", "partial") == "full":
        return _f(data, "full_balance_sheet_monthly_income")
    return _f(data, "monthly_income")


def _risk_ratio(at_risk, assets):
    if assets <= 0:
        return 1.0 if at_risk > 0 else 0.0
    return at_risk / assets


def _tier_from_ratio(ratio):
    if ratio >= 0.45:
        return "high_risk"
    if ratio >= 0.22:
        return "at_risk"
    return "on_track"


def classify_living_too_long(data):
    monthly_income = _monthly_income_for_mode(data)
    monthly_expenses = _f(data, "monthly_expenses")
    surplus = monthly_income - monthly_expenses
    if surplus <= 0:
        return "high_risk"

    protected_annual = _f(data, "protected_monthly_income") * 12
    basic_annual = _f(data, "monthly_living_expenses") * 12
    margin_ratio = surplus / max(monthly_expenses, 1)

    if protected_annual < basic_annual:
        return "at_risk"
    if margin_ratio < 0.10:
        return "at_risk"
    return "on_track"


def classify_flaw_of_averages(data):
    investable = _f(data, "investable_assets")
    unprotected = _f(data, "stock_assets") + _f(data, "bond_assets")
    guaranteed_alloc = _f(data, "guaranteed_income_allocation")
    unprotected_share = (unprotected / investable) if investable > 0 else 1.0

    if unprotected_share >= 0.80 and guaranteed_alloc <= 0.12:
        return "high_risk"
    if unprotected_share >= 0.55 or guaranteed_alloc <= 0.18:
        return "at_risk"
    return "on_track"


def classify_dying_too_soon(data):
    return _tier_from_ratio(
        _risk_ratio(_f(data, "assets_at_risk_early_death"), _f(data, "investable_assets"))
    )


def classify_underestimating_care(data):
    return _tier_from_ratio(
        _risk_ratio(_f(data, "assets_at_risk_ltc"), _f(data, "investable_assets"))
    )


def classify_getting_sued(data):
    return _tier_from_ratio(
        _risk_ratio(_f(data, "net_at_risk_lawsuit"), _f(data, "investable_assets"))
    )


def classify_combined_exposure(data):
    need = _f(data, "self_insurance_total")
    assets = _f(data, "investable_assets")
    if assets <= 0:
        return "high_risk" if need > 0 else "on_track"
    ratio = need / assets
    if ratio > 1.0:
        return "high_risk"
    if ratio >= 0.60:
        return "at_risk"
    return "on_track"


def classify_all_narratives(data):
    return {
        "flaw_of_averages": classify_flaw_of_averages(data),
        "living_too_long": classify_living_too_long(data),
        "dying_too_soon": classify_dying_too_soon(data),
        "underestimating_care": classify_underestimating_care(data),
        "getting_sued": classify_getting_sued(data),
        "combined_exposure": classify_combined_exposure(data),
    }


NARRATIVE_COPY = {
    "flaw_of_averages": {
        "on_track": {
            "headline": "On Track — With Exposure",
            "paragraphs": [
                "Your plan uses investment assets to support retirement income, which is common and can work well "
                "when markets cooperate.",
                "However, relying on an average growth rate can hide a critical risk: the <b>sequence</b> of returns. "
                "The same arithmetic average can produce very different outcomes depending on whether losses occur "
                "early in retirement or later.",
            ],
            "quote": "Average returns are not the same as dependable income.",
        },
        "at_risk": {
            "headline": "At Risk — Sequence Sensitivity",
            "paragraphs": [
                "Your results show meaningful dependence on portfolio withdrawals during retirement.",
                "When withdrawals continue through a weak market—especially in the early years—recovery may be difficult. "
                "In one illustration, identical average returns left one scenario out of money in 24 years and another "
                "with more than $1.8 million remaining after 30 years.",
            ],
            "quote": "The timing of returns can matter as much as the returns themselves.",
        },
        "high_risk": {
            "headline": "High Risk — Paycut from Market Timing",
            "paragraphs": [
                "A large share of your retirement income appears tied to investment performance and ongoing withdrawals.",
                "This creates a paycut risk if returns are unfavorable when you need income most. The flaw in averages "
                "is not the math—it is assuming the sequence of returns will always cooperate.",
            ],
            "quote": "A bad sequence early in retirement can permanently reduce what your plan can pay you.",
        },
    },
    "living_too_long": {
        "on_track": {
            "headline": "On Track — With Exposure",
            "paragraphs": [
                "Your current income exceeds expenses, which supports sustainability today.",
                "Still, longevity risk asks whether income sources will keep pace for decades—not just this year. "
                "Inflation, taxes, and rising costs can quietly reduce purchasing power over time.",
            ],
            "quote": "Living longer is a gift—but it can become a paycut if income does not last as long as you do.",
        },
        "at_risk": {
            "headline": "At Risk — Income May Not Keep Pace",
            "paragraphs": [
                "Income and expenses are closely aligned, leaving limited cushion for living longer than expected.",
                "Essential expenses are not fully covered by predictable income, which increases reliance on withdrawals "
                "and market outcomes to sustain your lifestyle over time.",
            ],
            "quote": "Small gaps today can compound into a meaningful paycut over a long retirement.",
        },
        "high_risk": {
            "headline": "High Risk — Longevity Paycut Pressure",
            "paragraphs": [
                "Expenses meet or exceed income under current assumptions, indicating the plan may already require "
                "asset drawdowns to maintain lifestyle.",
                "If you live longer than expected, the pressure on remaining assets increases—raising the likelihood "
                "of future income reductions.",
            ],
            "quote": "Outliving your income plan is one of the most common ways retirement pay gets cut.",
        },
    },
    "dying_too_soon": {
        "on_track": {
            "headline": "On Track — With Exposure",
            "paragraphs": [
                "Your plan includes protection for typical retirement risks, but premature death can still create "
                "financial stress for a surviving spouse or household.",
                "The chart shows measurable—but not overwhelming—exposure if income must be replaced.",
            ],
            "quote": "Dying too soon can cut income for those who depend on you.",
        },
        "at_risk": {
            "headline": "At Risk — Survivor Income Gap",
            "paragraphs": [
                "A premature death could create a meaningful gap between available resources and what the household "
                "would need to maintain its standard of living.",
                "This is not a gradual risk—it tends to arrive suddenly and concentrate financial pressure.",
            ],
            "quote": "The paycut may be felt by the survivor, not only by the portfolio.",
        },
        "high_risk": {
            "headline": "High Risk — Severe Survivor Impact",
            "paragraphs": [
                "Your results show significant asset exposure if death occurs earlier than expected.",
                "Without adequate protection, a surviving spouse or family may need to reduce spending, draw down "
                "assets faster, or both.",
            ],
            "quote": "Dying too soon can force a lasting paycut for those left behind.",
        },
    },
    "underestimating_care": {
        "on_track": {
            "headline": "On Track — With Exposure",
            "paragraphs": [
                "Your plan acknowledges potential care needs, and current assumptions show manageable exposure "
                "relative to assets.",
                "Even so, long-term care costs are often underestimated until a health event occurs.",
            ],
            "quote": "Care costs rarely announce themselves in advance.",
        },
        "at_risk": {
            "headline": "At Risk — Care Costs Could Bite",
            "paragraphs": [
                "Long-term care exposure is material in your results.",
                "A sustained care need could redirect cash flow away from lifestyle spending and toward medical and "
                "caregiving costs—functionally reducing retirement pay.",
            ],
            "quote": "Underestimating care is a common path to a retirement paycut.",
        },
        "high_risk": {
            "headline": "High Risk — Care Cost Paycut Likely",
            "paragraphs": [
                "Your plan shows substantial potential exposure to long-term care costs.",
                "If care is needed at or above assumed levels, a large portion of investable assets could be "
                "redirected—leaving less income for everything else.",
            ],
            "quote": "A care event can cut lifestyle income even when investments are otherwise fine.",
        },
    },
    "getting_sued": {
        "on_track": {
            "headline": "On Track — With Exposure",
            "paragraphs": [
                "Liability protection appears to offset a meaningful portion of the lawsuit scenario modeled here.",
                "However, legal events are unpredictable, and uncovered amounts can still affect assets or cash flow.",
            ],
            "quote": "Getting sued is not predictable—but it can be expensive.",
        },
        "at_risk": {
            "headline": "At Risk — Liability Gap Present",
            "paragraphs": [
                "Your results show a significant net amount at risk after liability coverage is applied.",
                "A judgment or settlement above coverage limits could require assets to be used—reducing what "
                "your plan can otherwise provide.",
            ],
            "quote": "A lawsuit can become an involuntary paycut from your balance sheet.",
        },
        "high_risk": {
            "headline": "High Risk — Major Liability Exposure",
            "paragraphs": [
                "The modeled lawsuit scenario could affect a large share of investable assets.",
                "Income vulnerable to legal action may also be at risk, depending on how awards are structured "
                "and what protections are in place.",
            ],
            "quote": "Getting sued can cut both assets and future income.",
        },
    },
    "combined_exposure": {
        "on_track": {
            "headline": "On Track — Combined Exposure Manageable",
            "paragraphs": [
                "Taken together, the paycut risks from dying too soon, care costs, and liability are noticeable "
                "but appear absorbable relative to your assets.",
                "This does not eliminate the risks—it suggests room to respond if one event occurs.",
            ],
            "quote": "One event may be manageable; multiple events are harder.",
        },
        "at_risk": {
            "headline": "At Risk — Limited Room for Multiple Events",
            "paragraphs": [
                "Combined exposure from the three event risks approaches a level where trade-offs may be required.",
                "Covering one scenario could reduce flexibility to handle another without adjusting income or spending.",
            ],
            "quote": "The paycut risks stack when more than one event occurs.",
        },
        "high_risk": {
            "headline": "High Risk — Total Exposure Strains Resources",
            "paragraphs": [
                "Total potential exposure from dying too soon, care costs, and getting sued exceeds a comfortable "
                "margin relative to investable assets.",
                "If multiple risks materialize, income or assets may need to be reduced.",
            ],
            "quote": "Cumulative paycut risk can exceed what the plan can self-fund.",
        },
    },
    "closing_bridge_free": (
        "Observations above show where your plan appears on track, at risk, or under higher pressure "
        "from the inputs and charts in this report."
    ),
    "closing_bridge": (
        "Educational options and probability outputs, where shown, are for context—not personalized "
        "advice or recommendations."
    ),
    "balance_sheet_planning_note": (
        "<b>Planning note:</b> Partial and full balance sheet views in the allocator let you include accessible "
        "home equity in your analysis. That is a planning lens—not one of the five paycut risks above—but it can "
        "inform how resources are sequenced alongside investments."
    ),
}


def get_narrative_block(section_key, tier):
    return NARRATIVE_COPY.get(section_key, {}).get(tier, {})


def _money(v):
    return f"${float(v or 0):,.0f}"


def client_context_paragraph(section_key, data):
    """One client-specific sentence appended to tier observations."""
    investable = _f(data, "investable_assets")
    if section_key == "flaw_of_averages":
        unprotected = _f(data, "stock_assets") + _f(data, "bond_assets")
        pct = (unprotected / investable * 100) if investable > 0 else 0
        g = _f(data, "guaranteed_income_allocation")
        guaranteed_pct = g * 100 if abs(g) <= 1 else g
        return (
            f"In your inputs, <b>{pct:.0f}%</b> of investable assets are unprotected and "
            f"<b>{guaranteed_pct:.0f}%</b> is allocated to guaranteed income—key drivers of "
            "sequence sensitivity."
        )

    if section_key == "living_too_long":
        income = _monthly_income_for_mode(data)
        expenses = _f(data, "monthly_expenses")
        gap = income - expenses
        protected_annual = _f(data, "protected_monthly_income") * 12
        basic_annual = _f(data, "monthly_living_expenses") * 12
        if gap >= 0:
            return (
                f"Your inputs show <b>{_money(gap)}</b> monthly surplus and protected income of "
                f"<b>{_money(protected_annual)}</b>/year vs basic expenses of "
                f"<b>{_money(basic_annual)}</b>/year."
            )
        return (
            f"Your inputs show a <b>{_money(abs(gap))}</b> monthly gap and protected income of "
            f"<b>{_money(protected_annual)}</b>/year vs basic expenses of "
            f"<b>{_money(basic_annual)}</b>/year."
        )

    if section_key == "dying_too_soon":
        at_risk = _f(data, "assets_at_risk_early_death")
        pct = (at_risk / investable * 100) if investable > 0 else 0
        return (
            f"Your early-death scenario shows <b>{_money(at_risk)}</b> at risk "
            f"(<b>{pct:.0f}%</b> of {_money(investable)} investable assets)."
        )

    if section_key == "underestimating_care":
        at_risk = _f(data, "assets_at_risk_ltc")
        pct = (at_risk / investable * 100) if investable > 0 else 0
        years = int(_f(data, "ltc_years"))
        return (
            f"Your modeled <b>{years}-year</b> care stay implies <b>{_money(at_risk)}</b> exposure "
            f"(<b>{pct:.0f}%</b> of investable assets)."
        )

    if section_key == "getting_sued":
        at_risk = _f(data, "net_at_risk_lawsuit")
        pct = (at_risk / investable * 100) if investable > 0 else 0
        return (
            f"Your lawsuit scenario of <b>{_money(data.get('lawsuit_award'))}</b> leaves "
            f"<b>{_money(at_risk)}</b> net at risk (<b>{pct:.0f}%</b> of investable assets)."
        )

    if section_key == "combined_exposure":
        need = _f(data, "self_insurance_total")
        pct = (need / investable * 100) if investable > 0 else 0
        return (
            f"Combined self-insurance need in your inputs is <b>{_money(need)}</b> "
            f"(<b>{pct:.0f}%</b> of {_money(investable)} investable assets)."
        )

    return ""


def flaw_sequence_bridge_paragraph(data):
    """Tie the sequence example to this household's allocation."""
    investable = _f(data, "investable_assets")
    unprotected = _f(data, "stock_assets") + _f(data, "bond_assets")
    pct = (unprotected / investable * 100) if investable > 0 else 0
    profile = data.get("profile_label") or data.get("risk_profile") or "growth"
    return (
        f"<b>For your plan:</b> With a <b>{profile}</b> profile and roughly "
        f"<b>{pct:.0f}%</b> of assets subject to market withdrawals, sequence risk is not "
        "abstract—it applies directly to the income your plan expects from investments."
    )
