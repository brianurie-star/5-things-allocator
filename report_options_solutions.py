"""
$99 Premium Retirement Optimization Report — educational strategies by risk and tier.
"""

import os

PAID_REPORT_NEXT_STEP_URLS = {
    "annuity": os.environ.get(
        "ANNUITY_APPOINTMENT_URL",
        os.environ.get("ADVISOR_APPOINTMENT_URL", "https://www.macu.com/burie"),
    ),
    "term_life": os.environ.get(
        "TERM_LIFE_URL",
        "https://vivecp.com/fa4c2632-3f3c-42db-8d9c-73241d4ac9e5",
    ),
    "ltc": os.environ.get("LTC_QUOTE_URL", "https://www.macu.com/burie"),
    "umbrella": os.environ.get("UMBRELLA_QUOTE_URL", "https://www.macu.com/burie"),
}

PAID_REPORT_INTRO = [
    (
        "This section builds on your prior analysis by outlining <b>available strategies</b> to "
        "address the risks identified in your retirement plan."
    ),
    (
        "These strategies are grounded in academic research and commonly used planning approaches. "
        "They are presented to help you understand your options—not as specific recommendations."
    ),
]

PAID_REPORT_FINAL_POSITIONING = [
    "The strategies outlined above are designed to address individual risks.",
    (
        "The most effective retirement plans coordinate income sources, investment strategy, "
        "risk protection, and asset sequencing."
    ),
    (
        "<i>Retirement success is not only about how much you have—it is about how effectively "
        "your resources are structured to support income over time.</i>"
    ),
]

PAID_REPORT_EDUCATIONAL_DISCLOSURE = [
    (
        "The strategies and options presented in this report are provided for "
        "<b>educational and informational purposes only</b> and should "
        "<b>not be interpreted as personalized recommendations</b>."
    ),
    (
        "This report does not take into account your full financial situation, objectives, "
        "risk tolerance, tax status, or legal considerations."
    ),
    (
        "Before implementing any strategy, you should consult with the appropriate licensed "
        "professional, including a financial advisor for investment decisions; an insurance "
        "professional for coverage needs; a licensed annuity specialist for guaranteed income "
        "products; a tax advisor or CPA for tax implications; and an attorney for legal or "
        "estate planning matters."
    ),
    (
        "Investment, insurance, and annuity products involve risk and are not guaranteed. "
        "Past performance and academic research are not guarantees of future results."
    ),
]

RISK_SOLUTION_ORDER = [
    "flaw_of_averages",
    "living_too_long",
    "dying_too_soon",
    "underestimating_care",
    "getting_sued",
]

PAID_RISK_SECTIONS = {
    "flaw_of_averages": {
        "number": 1,
        "title": "Flaw of Averages",
        "subtitle": "Managing Market Risk &amp; Sequence Risk",
        "next_step_key": "annuity",
        "next_step_label": "Schedule annuity consultation",
        "research": [
            (
                "Traditional retirement planning often relies on average returns. However, the "
                "sequence in which returns occur can significantly impact outcomes."
            ),
            (
                "Research on <i>Rational Decumulation</i> suggests that combining investment "
                "portfolios with guaranteed income sources can improve retirement outcomes and "
                "reduce reliance on market timing."
            ),
            (
                "Merrill, C. B., &amp; Finke, M. S. (2016). <i>Rational decumulation: A safe approach "
                "to retirement income</i>. Journal of Financial Planning."
            ),
            (
                "In addition, Wade Pfau's research indicates that guaranteed income annuities can "
                "help absorb a larger share of withdrawals early in retirement, reducing pressure on "
                "investment portfolios during vulnerable years."
            ),
            (
                "Pfau, W. D. (2014). <i>Reducing retirement risk with a rising equity glide path</i>. "
                "Journal of Financial Planning."
            ),
            (
                "It is also important to note that the commonly cited <b>4% withdrawal rule assumes "
                "a meaningful allocation to equities</b>. Adjustments to equity exposure should be "
                "made carefully."
            ),
        ],
    },
    "living_too_long": {
        "number": 2,
        "title": "Living Too Long",
        "subtitle": "Longevity Risk",
        "next_step_key": "annuity",
        "next_step_label": "Schedule annuity consultation",
        "research": [
            (
                "Longevity risk can be addressed by converting a portion of assets into income "
                "that cannot be outlived."
            ),
            (
                "Pfau's research highlights that guaranteed income sources can support sustainable "
                "income over longer lifespans and reduce the need to preserve portfolio assets "
                "solely for longevity protection."
            ),
        ],
    },
    "dying_too_soon": {
        "number": 3,
        "title": "Dying Too Soon",
        "subtitle": "Survivor Income Risk",
        "next_step_key": "term_life",
        "next_step_label": "Request term life quote",
        "research": [],
    },
    "underestimating_care": {
        "number": 4,
        "title": "Long-Term Care Costs",
        "subtitle": "Healthcare &amp; Extended Care Risk",
        "next_step_key": "ltc",
        "next_step_label": "Request LTC quote",
        "research": [],
    },
    "getting_sued": {
        "number": 5,
        "title": "Getting Sued",
        "subtitle": "Liability Risk",
        "next_step_key": "umbrella",
        "next_step_label": "Request umbrella quote",
        "research": [],
    },
}

PAID_TIER_CONTENT = {
    "flaw_of_averages": {
        "on_track": {
            "headline": "On Track — Improve Stability",
            "summary": (
                "Your portfolio supports long-term growth but remains sensitive to market variability."
            ),
            "bullets": [
                "Modestly rebalance toward <b>fixed income or lower-volatility assets</b>",
                "Incorporate <b>buffered ETFs (e.g., BUFB)</b>",
                "Allocate a portion of assets to <b>guaranteed income strategies</b>",
            ],
        },
        "at_risk": {
            "headline": "At Risk — Reduce Sequence Sensitivity",
            "summary": "Your plan shows increased dependence on favorable market timing.",
            "bullets": [
                "Adjust allocation toward <b>lower volatility assets</b>",
                "Introduce <b>structured ETFs</b> to help limit downside risk",
                "Shift a portion of income needs to <b>guaranteed income sources</b>",
            ],
        },
        "high_risk": {
            "headline": "High Risk — Income Needs Stabilization",
            "summary": "Your income strategy is highly dependent on market performance.",
            "bullets": [
                "Rebalance toward a <b>more stable asset mix</b>",
                "Increase allocation to <b>income-producing strategies</b>",
                (
                    "Allow <b>guaranteed income to cover a greater share of withdrawals early "
                    "in retirement</b>"
                ),
            ],
        },
    },
    "living_too_long": {
        "on_track": {
            "headline": "On Track — Extend Income Duration",
            "summary": (
                "Your plan supports your current timeline, but longevity remains uncertain."
            ),
            "bullets": [
                "Adjust withdrawal rate as needed",
                "Allocate a portion of assets to <b>Single Premium Immediate Annuities (SPIAs)</b>",
                "Consider annuities with <b>Guaranteed Income Benefits</b>",
            ],
        },
        "at_risk": {
            "headline": "At Risk — Longevity Pressure",
            "summary": (
                "Your plan may experience strain if retirement lasts longer than expected."
            ),
            "bullets": [
                "Reduce withdrawal rate",
                "Introduce <b>lifetime income streams</b>",
                "Blend investment withdrawals with <b>guaranteed income</b>",
            ],
        },
        "high_risk": {
            "headline": "High Risk — Income May Not Last",
            "summary": "Your withdrawal strategy may not support a long retirement.",
            "bullets": [
                "Shift from withdrawals toward <b>guaranteed lifetime income</b>",
                (
                    "Increase the portion of income that continues regardless of lifespan"
                ),
            ],
        },
    },
    "dying_too_soon": {
        "on_track": {
            "headline": "On Track — Strengthen Protection",
            "summary": "Your plan includes a foundation of survivor protection.",
            "bullets": [
                "Port <b>group life insurance</b> into retirement",
                "Supplement with <b>term life insurance coverage</b>",
                "Align coverage duration with your risk window",
            ],
        },
        "at_risk": {
            "headline": "At Risk — Survivor Income Gap",
            "summary": (
                "Your plan indicates potential income reduction for a surviving spouse."
            ),
            "bullets": [
                "Add <b>10-, 15-, or 20-year term policies</b>",
                "<b>Ladder coverage</b> over time",
                "Match insurance to declining financial obligations",
            ],
        },
        "high_risk": {
            "headline": "High Risk — Significant Survivor Risk",
            "summary": (
                "Your plan shows a high likelihood of income disruption after the first death."
            ),
            "bullets": [
                "Add sufficient term coverage to replace lost income",
                "Structure coverage to maintain lifestyle continuity",
            ],
        },
    },
    "underestimating_care": {
        "on_track": {
            "headline": "On Track — Manage Exposure",
            "summary": (
                "You are positioned to absorb some healthcare costs, but exposure remains."
            ),
            "bullets": [
                "<b>Traditional long-term care insurance</b>",
                "<b>Asset-based or hybrid LTC policies</b>",
                "Self-funding strategies",
            ],
        },
        "at_risk": {
            "headline": "At Risk — High Cost Exposure",
            "summary": (
                "Your plan shows meaningful vulnerability to extended care costs."
            ),
            "bullets": [
                "Hybrid LTC strategies combining protection and asset use",
                "Coverage designed for multi-year care events",
                "Defined funding strategies",
            ],
        },
        "high_risk": {
            "headline": "High Risk — Significant Impact Likely",
            "summary": (
                "Your plan shows substantial exposure to long-term care costs."
            ),
            "bullets": [
                "Insurance-based coverage solutions",
                "Medicaid planning considerations",
                "Family-based care approaches",
            ],
        },
    },
    "getting_sued": {
        "on_track": {
            "headline": "On Track — Strengthen Existing Protection",
            "summary": "You already have a base level of liability protection.",
            "bullets": [
                "<b>Increase existing umbrella insurance coverage</b>",
                "Align coverage with your total net worth",
                "Review limits across home and auto policies",
            ],
        },
        "at_risk": {
            "headline": "At Risk — Coverage May Be Insufficient",
            "summary": (
                "Your liability limits may not fully align with your exposure."
            ),
            "bullets": [
                "Increase umbrella coverage limits",
                "Expand liability protection beyond base policies",
                "Align coverage with total assets",
            ],
        },
        "high_risk": {
            "headline": "High Risk — Exposure Exceeds Protection",
            "summary": (
                "Your potential liability exposure may exceed your current coverage."
            ),
            "bullets": [
                "Increase umbrella coverage significantly",
                "Align protection with your full balance sheet",
                "Reduce exposure to large liability risks",
            ],
        },
    },
}


def paid_next_step_url(step_key):
    return PAID_REPORT_NEXT_STEP_URLS.get(step_key, PAID_REPORT_NEXT_STEP_URLS["annuity"])


PAID_QUOTE_LINKS = [
    {
        "key": "annuity",
        "label": "Schedule annuity consultation",
        "note": "Market &amp; sequence risk, longevity (sections 1–2)",
    },
    {
        "key": "term_life",
        "label": "Request term life quote",
        "note": "Survivor income protection (section 3)",
    },
    {
        "key": "ltc",
        "label": "Request LTC quote",
        "note": "Long-term care costs (section 4)",
    },
    {
        "key": "umbrella",
        "label": "Request umbrella quote",
        "note": "Liability protection (section 5)",
    },
]


def get_paid_tier_block(section_key, tier):
    tier = tier if tier in ("on_track", "at_risk", "high_risk") else "on_track"
    return PAID_TIER_CONTENT[section_key][tier]
