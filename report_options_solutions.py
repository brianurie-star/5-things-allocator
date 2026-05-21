"""
Premium 5 Things Report — educational strategies by risk and tier.
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
        "The addendum below summarizes withdrawal-rate illustrations and educational quote links. "
        "Tier-matched <b>options to consider</b> for each paycut risk appear in the sections above—"
        "for education only, not as recommendations."
    ),
]

PAID_REPORT_OPTIMIZATION_HEADING = "Strategies that support your income plan"

PAID_REPORT_EDUCATIONAL_DISCLOSURE = [
    "The strategies outlined above describe common approaches that may address individual risks.",
    (
        "The most effective retirement plans coordinate income sources, investment strategy, "
        "risk protection, and asset sequencing."
    ),
    (
        "<i>Retirement success is not only about how much you have—it is about how effectively "
        "your resources are structured to support income over time.</i>"
    ),
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

LONGEVITY_RESEARCH = {
    "section_title": "Longevity Risk",
    "key_research_points": [
        "Longevity is often a 25–30+ year income challenge, not a short retirement.",
        "Inflation quietly reduces purchasing power when income does not keep pace.",
        "Research links higher protected income (above Social Security) with greater retirement satisfaction.",
    ],
    "understanding_heading": "How long your income may need to last",
    "key_considerations_heading": "What to plan for",
    "optional_considerations_heading": "Later in retirement",
    "satisfaction_research_heading": "Protected income and retirement satisfaction",
    "understanding_paragraphs": [
        (
            "One of the most overlooked risks in retirement is not market performance—but how long "
            "income needs to last."
        ),
        (
            "The chart below illustrates how inflation compounds over time and erodes purchasing "
            "power across a long retirement."
        ),
    ],
    "longevity_intro": (
        "At the same time, longevity data shows that retirement may last longer than many people "
        "expect:"
    ),
    "longevity_stats": [
        "Approximately 50% of men age 65 will live beyond age 85, and 25% beyond age 92",
        "Approximately 50% of women age 65 will live beyond age 88, and 25% beyond age 94",
        (
            "There is roughly a 1 in 4 chance that one member of a couple will live beyond age 97"
        ),
    ],
    "longevity_closing": (
        "This means retirement is not a 10–15 year event—it is often a <b>25–30+ year income "
        "challenge</b>."
    ),
    "key_considerations": [
        "No one knows how long they will live—so planning must account for uncertainty",
        "A longer retirement increases exposure to inflation and market variability",
        "Income needs may change over time as lifestyle, health, and priorities evolve",
    ],
    "optional_considerations": [
        "Retirement often occurs in phases, each with different financial needs",
        "Early retirement years may look very different from later years",
    ],
    "satisfaction_research": [
        (
            "Using Health and Retirement Study (HRS) data, research suggests that "
            "<b>satisfaction tends to rise with protected income above Social Security</b>—even among "
            "higher-net-worth retirees—with a notable step around "
            "<b>$30,000–$40,000 per year</b> (about <b>$3,000 per month</b>) from pensions, annuities, "
            "or in-plan guarantees."
        ),
    ],
    "apa_references_heading": "References",
    "apa_references": [
        (
            "Pfau, W. D., &amp; Finke, M. (2020). <i>Guaranteed retirement income increases retirement "
            "satisfaction</i>. Nationwide Retirement Institute / Health and Retirement Study (HRS)."
        ),
        (
            "Society of Actuaries. (2000). <i>Annuity 2000 Mortality Tables</i>. "
            "Probability of living beyond key ages for men, women, and couples (figure in this report)."
        ),
    ],
    "figures": [
        {
            "filename": "inflation-purchasing-power.png",
            "title": "Purchasing power and inflation over time",
            "caption": "",
        },
        {
            "filename": "longevity-soa-2000.png",
            "title": "",
            "caption": (
                "Probability of living beyond key ages for men, women, and couples. "
                "<b>Source: Society of Actuaries Annuity 2000 Tables.</b>"
            ),
        },
    ],
}

DYING_TOO_SOON_RESEARCH = {
    "section_title": "Survivor Income Risk",
    "key_research_points": [
        "Survivor benefits are often lower than joint household income—not half of combined cash flow.",
        "Fixed costs frequently remain while pensions, annuities, or assets may pay differently.",
        "Planning should stress-test one-household income, not only the joint plan.",
    ],
    "understanding_heading": "When a spouse dies early",
    "understanding_paragraphs": [
        (
            "The loss of a spouse is not only emotional—it can also create a significant financial shift."
        ),
        (
            "As illustrated below, income may decline while expenses remain the same or even increase."
        ),
    ],
    "retirement_income_heading": "Effect on retirement income",
    "retirement_income_intro": (
        "A surviving spouse will often experience reduced income and potentially higher expenses "
        "at the same time."
    ),
    "income_why_heading": "Why income often drops",
    "income_why_bullets": [
        "Social Security benefits for a couple are higher than for an individual",
        "The surviving spouse receives the higher of the two benefits, not both",
        "Pension income may decrease or cease depending on the payout election",
        "Annuity income may continue at a reduced level depending on the selected option",
        "Assets may transfer to other beneficiaries, reducing available income",
    ],
    "practical_heading": "What that means for household expenses",
    "practical_bullets": [
        "Many fixed costs (housing, utilities, taxes) remain unchanged",
        (
            "Certain costs may increase when one spouse is no longer able to provide care or support"
        ),
        "Healthcare and support services may become more necessary over time",
    ],
    "enhanced_expense_closing": (
        "While household size decreases, the cost of maintaining that household often does not "
        "decrease proportionally."
    ),
    "refined_insight": (
        "The loss of a spouse does not cut expenses in half—but it often reduces income "
        "significantly."
    ),
    "apa_references_heading": "References",
    "apa_references": [
        (
            "Kaiser Family Foundation. (2024, March 14). <i>Medicare households spend more on health "
            "care than other households</i>. KFF. "
            '<a href="https://www.kff.org/medicare/medicare-households-spend-more-on-health-care-than-other-households/" '
            'color="#1B2D47"><u>https://www.kff.org/medicare/medicare-households-spend-more-on-health-care-than-other-households/</u></a>'
        ),
        (
            "McGarry, K., &amp; Schoeni, R. F. (2005). Medicare gaps and widow poverty. "
            "<i>Social Security Bulletin</i>, <i>66</i>(1), 58–74. Social Security Administration. "
            '<a href="https://www.ssa.gov/policy/docs/ssb/v66n1/v66n1p58.html" color="#1B2D47">'
            "<u>https://www.ssa.gov/policy/docs/ssb/v66n1/v66n1p58.html</u></a>"
        ),
    ],
    "key_consideration_heading": "Plan for one household, not two",
    "key_consideration": (
        "Retirement planning is not only about joint income—it must also account for individual "
        "outcomes. A plan that works for two people may not work for one."
    ),
    "figures": [
        {
            "filename": "dying-too-soon-survivor-risk.png",
            "title": "Dying Too Soon — income and expense impact",
            "caption": "",
        },
    ],
}

UNDERESTIMATING_CARE_RESEARCH = {
    "section_title": "Healthcare &amp; Long-Term Care Risk",
    "key_research_points": [
        "Healthcare in retirement is a major, unpredictable expense—often separate from long-term care.",
        "Care events can redirect a large share of investable assets away from lifestyle income.",
        "Duration and monthly cost assumptions materially change exposure.",
    ],
    "understanding_heading": "Healthcare and long-term care in retirement",
    "understanding_paragraphs": [
        "Healthcare is one of the largest and most unpredictable expenses in retirement.",
        (
            "According to Fidelity's most recent estimate, a 65-year-old couple retiring today may "
            "need approximately <b>$315,000</b> in savings to cover healthcare expenses throughout "
            "retirement—excluding long-term care."
        ),
    ],
    "fidelity_citation": (
        "Fidelity Investments. (2023). <i>Retiree health care cost estimate</i>."
    ),
    "healthcare_costs_heading": "What healthcare spending typically includes",
    "healthcare_costs_bullets": [
        "Medicare premiums",
        "Supplemental insurance",
        "Out-of-pocket medical expenses",
    ],
    "healthcare_costs_closing": (
        "They do not include long-term care, which represents a separate and often larger "
        "financial risk."
    ),
    "ltc_cost_heading": "Long-term care costs",
    "ltc_cost_paragraphs": [
        "Long-term care expenses can be significant and extended over multiple years.",
        (
            "According to Genworth's Cost of Care Survey, the national median cost of a private "
            "room in a nursing home exceeds <b>$100,000 per year</b>, and the median cost of "
            "assisted living is approximately <b>$60,000 per year</b>."
        ),
    ],
    "genworth_citation": (
        "Genworth Financial, Inc. (2023). <i>Cost of Care Survey 2023</i>."
    ),
    "ltc_duration_heading": "How long care often lasts",
    "ltc_duration_bullets": [
        "The average long-term care need lasts approximately 2–3 years",
        "Some individuals require care for significantly longer periods",
    ],
    "nchs_citation": (
        "National Center for Health Statistics. (2019). <i>Long-term care providers and services "
        "users in the United States</i>."
    ),
    "ltc_duration_closing": (
        "Even a relatively short care event can represent hundreds of thousands of dollars in "
        "expenses."
    ),
    "medicaid_heading": "Medicaid and paying for care",
    "medicaid_paragraphs": [
        (
            "Many retirees assume that Medicaid will cover long-term care costs. However, Medicaid "
            "is a means-tested program with strict eligibility requirements."
        ),
        "In general, qualifying for Medicaid requires:",
    ],
    "medicaid_bullets": [
        "Limited income (varies by state)",
        (
            "Very low countable assets (often around $2,000 for an individual, excluding certain "
            "exempt assets such as a primary residence under specific conditions)"
        ),
        "Meeting functional eligibility requirements for care",
    ],
    "medicaid_closing": (
        "In many cases, individuals must spend down their assets before qualifying."
    ),
    "kff_medicaid_citation": (
        "Kaiser Family Foundation. (2023). <i>Medicaid financial eligibility for seniors and people "
        "with disabilities</i>."
    ),
    "medicaid_strategy_note": (
        "Medicaid is not designed as a primary retirement strategy—it is a safety net after assets "
        "have been largely depleted."
    ),
    "key_insight": (
        "Healthcare costs are ongoing. Long-term care costs are episodic—but potentially catastrophic. "
        "Together, they represent one of the most significant risks to retirement income."
    ),
    "apa_references_heading": "References",
    "apa_references": [
        (
            "Fidelity Investments. (2023). <i>Retiree health care cost estimate</i>. "
            '<a href="https://www.fidelity.com/viewpoints/personal-finance/plan-for-rising-health-care-costs" '
            'color="#1B2D47"><u>https://www.fidelity.com/viewpoints/personal-finance/plan-for-rising-health-care-costs</u></a>'
        ),
        (
            "Genworth Financial, Inc. (2023). <i>Cost of care survey 2023</i>. "
            '<a href="https://www.genworth.com/americas-care-solutions/cost-of-care-explorer" '
            'color="#1B2D47"><u>https://www.genworth.com/americas-care-solutions/cost-of-care-explorer</u></a>'
        ),
        (
            "Kaiser Family Foundation. (2023). <i>Medicaid financial eligibility for seniors and "
            "people with disabilities</i>. "
            '<a href="https://www.kff.org/medicaid/issue-brief/medicaid-financial-eligibility-for-seniors-and-people-with-disabilities/" '
            'color="#1B2D47"><u>https://www.kff.org/medicaid/issue-brief/medicaid-financial-eligibility-for-seniors-and-people-with-disabilities/</u></a>'
        ),
        (
            "National Center for Health Statistics. (2019). <i>Long-term care providers and services "
            "users in the United States</i>. "
            '<a href="https://www.cdc.gov/nchs/fastats/long-term-care.htm" color="#1B2D47">'
            "<u>https://www.cdc.gov/nchs/fastats/long-term-care.htm</u></a>"
        ),
    ],
}

GETTING_SUED_RESEARCH = {
    "section_title": "Liability Risk",
    "key_research_points": [
        "Liability limits on home and auto policies are often well below large judgment scenarios.",
        "A legal event can reduce both investable assets and future income at once.",
        "Umbrella and asset-protection strategies are common educational responses—not guarantees.",
    ],
    "understanding_heading": "Lawsuits and your retirement assets",
    "understanding_paragraphs": [
        (
            "Liability risk is often overlooked in retirement planning—but it can have an immediate "
            "and significant financial impact."
        ),
    ],
    "illustration_heading": "What your liability charts show",
    "illustration_bullets": [
        "Liability coverage in home and auto policies often does not exceed $500,000",
        (
            "Yet approximately 13% of personal injury liability awards and settlements exceed "
            "$1 million"
        ),
    ],
    "jury_verdict_citation": (
        "Jury Verdict Research, as cited in Ebeling, A. (2012, March 5). <i>The #1 fear: Being sued—but "
        "shun umbrella insurance</i>. <i>Forbes</i>. "
        '<a href="https://www.forbes.com/sites/ashleaebeling/2012/03/05/the-1-fear-being-sued-but-shun-umbrella-insurance/" '
        'color="#1B2D47">'
        "<u>https://www.forbes.com/sites/ashleaebeling/2012/03/05/the-1-fear-being-sued-but-shun-umbrella-insurance/</u></a>"
    ),
    "why_matters_heading": "Why this risk is different",
    "why_matters_intro": "Unlike other retirement risks, liability events are:",
    "why_matters_traits": [
        "Sudden",
        "Unpredictable",
        "Potentially severe",
    ],
    "why_matters_sources_heading": "Common causes",
    "why_matters_sources": [
        "Auto accidents",
        "Property-related incidents",
        "Personal liability situations",
    ],
    "why_matters_paragraphs": [
        (
            "In many cases, the financial exposure from a lawsuit can exceed standard policy limits."
        ),
        (
            "This creates a situation where personal assets—including retirement savings—may be at risk."
        ),
    ],
    "key_insight": (
        "Liability risk is one of the few events that can create an immediate and irreversible "
        "reduction in retirement assets."
    ),
    "free_plan_heading": "If your coverage may not be enough",
    "free_plan_intro": "If liability coverage is lower than potential exposure:",
    "free_plan_bullets": [
        "A portion of your retirement assets may be vulnerable",
        "A single event could significantly impact long-term income",
        "Financial recovery may be difficult once assets are reduced",
    ],
    "free_plan_closing": "This risk is not gradual—it occurs all at once.",
    "practical_framing_heading": "Insurance vs. using your own assets",
    "practical_framing_paragraphs": [
        (
            "A simple way to limit exposure to lawsuits—particularly from auto-related incidents—is to "
            "increase liability coverage on home and auto policies and ensure umbrella coverage is "
            "appropriately sized."
        ),
        (
            "The alternative is to rely on personal assets—including retirement savings—to cover "
            "potential claims."
        ),
        (
            "In effect, this becomes a choice between transferring risk through insurance or retaining "
            "that risk within your balance sheet."
        ),
    ],
    "verdict_quote": (
        "Most liability coverage falls below $500,000, while multi-million dollar awards are "
        "becoming more common—and verdicts exceeding $10 million are no longer rare."
    ),
    "apa_references_heading": "References",
    "apa_references": [
        (
            "Ebeling, A. (2012, March 5). <i>The #1 fear: Being sued—but shun umbrella insurance</i>. "
            "<i>Forbes</i>. "
            '<a href="https://www.forbes.com/sites/ashleaebeling/2012/03/05/the-1-fear-being-sued-but-shun-umbrella-insurance/" '
            'color="#1B2D47">'
            "<u>https://www.forbes.com/sites/ashleaebeling/2012/03/05/the-1-fear-being-sued-but-shun-umbrella-insurance/</u></a>"
        ),
    ],
}

PAID_RISK_SECTIONS = {
    "flaw_of_averages": {
        "number": 1,
        "title": "Flaw of Averages",
        "subtitle": "Managing Market Risk &amp; Sequence Risk",
        "next_step_key": "annuity",
        "next_step_label": "Schedule a consultation with an annuity specialist",
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
        "next_step_label": "Schedule a consultation with an annuity specialist",
        "research": [
            (
                "Pfau, W. D., &amp; Finke, M. (2020). <i>Guaranteed retirement income increases "
                "retirement satisfaction</i>. Nationwide Retirement Institute / Health and "
                "Retirement Study (HRS)."
            ),
            (
                "Merrill, C. B., &amp; Finke, M. S. (2016). <i>Rational decumulation: A safe approach "
                "to retirement income</i>. Journal of Financial Planning."
            ),
        ],
    },
    "dying_too_soon": {
        "number": 3,
        "title": "Dying Too Soon",
        "subtitle": "Survivor Income Risk",
        "next_step_key": "term_life",
        "next_step_label": "Request a term life insurance quote",
        "research": [
            (
                "Social Security Administration. (n.d.). <i>Survivors benefits</i>. "
                '<a href="https://www.ssa.gov/benefits/survivors/" color="#1B2D47">'
                "<u>https://www.ssa.gov/benefits/survivors/</u></a>"
            ),
            (
                "Kaiser Family Foundation. (2024, March 14). <i>Medicare households spend more on health "
                "care than other households</i>. KFF."
            ),
            (
                "McGarry, K., &amp; Schoeni, R. F. (2005). Medicare gaps and widow poverty. "
                "<i>Social Security Bulletin</i>, <i>66</i>(1), 58–74."
            ),
        ],
    },
    "underestimating_care": {
        "number": 4,
        "title": "Underestimating Care Costs",
        "subtitle": "Healthcare &amp; Long-Term Care Risk",
        "next_step_key": "ltc",
        "next_step_label": "Request a long-term care insurance quote",
        "research": [
            "Fidelity Investments. (2023). <i>Retiree health care cost estimate</i>.",
            "Genworth Financial, Inc. (2023). <i>Cost of Care Survey 2023</i>.",
            (
                "Kaiser Family Foundation. (2023). <i>Medicaid financial eligibility for seniors "
                "and people with disabilities</i>."
            ),
            (
                "National Center for Health Statistics. (2019). <i>Long-term care providers and "
                "services users in the United States</i>."
            ),
        ],
    },
    "getting_sued": {
        "number": 5,
        "title": "Getting Sued",
        "subtitle": "Liability Risk",
        "next_step_key": "umbrella",
        "next_step_label": "Request an umbrella insurance quote",
        "research": [
            (
                "Ebeling, A. (2012, March 5). <i>The #1 fear: Being sued—but shun umbrella insurance</i>. "
                "<i>Forbes</i>."
            ),
        ],
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
                "Your plan supports your current retirement timeline, but longevity remains uncertain."
            ),
            "bullets": [
                "Adjust withdrawal rates to improve long-term sustainability",
                "Allocate a portion of assets to <b>Single Premium Immediate Annuities (SPIAs)</b>",
                "Consider annuities with <b>Guaranteed Income Benefits</b>",
            ],
        },
        "at_risk": {
            "headline": "At Risk — Longevity Pressure",
            "summary": (
                "Your plan may experience strain if retirement extends longer than expected."
            ),
            "bullets": [
                "Reduce withdrawal rate to improve probability of success",
                "Convert a portion of assets into <b>lifetime income streams</b>",
                "Blend investment withdrawals with <b>guaranteed income sources</b>",
            ],
            "after_bullets": [
                (
                    "These approaches can help shift part of the longevity risk away from your "
                    "portfolio."
                ),
            ],
        },
        "high_risk": {
            "headline": "High Risk — Income May Not Last",
            "summary": (
                "Your current withdrawal strategy may not support a long retirement."
            ),
            "bullets": [
                "Shift from withdrawal-based income toward <b>guaranteed lifetime income</b>",
                (
                    "Increase the portion of income that continues regardless of lifespan"
                ),
                "Reduce reliance on assets that must last indefinitely",
            ],
        },
    },
    "dying_too_soon": {
        "on_track": {
            "headline": "On Track — Strengthen Protection",
            "summary": (
                "Your plan provides a base level of survivor protection, but improvements may "
                "enhance long-term stability."
            ),
            "bullets": [
                "Port <b>group life insurance</b> into retirement",
                "Supplement with <b>term life insurance coverage</b>",
                "Align coverage duration with income replacement needs",
            ],
        },
        "at_risk": {
            "headline": "At Risk — Survivor Income Gap",
            "summary": (
                "Your plan indicates a potential reduction in income for a surviving spouse."
            ),
            "bullets": [
                "Add <b>10-, 15-, or 20-year term policies</b>",
                "Ladder coverage so protection decreases over time",
                "Match coverage duration to the period of greatest financial risk",
            ],
        },
        "high_risk": {
            "headline": "High Risk — Significant Survivor Risk",
            "summary": (
                "Your plan shows a high likelihood of income disruption following the loss of a spouse."
            ),
            "bullets": [
                "Add sufficient term coverage to replace lost income sources",
                (
                    "Structure coverage to help maintain the surviving spouse's lifestyle"
                ),
                "Ensure coverage aligns with long-term financial needs",
            ],
        },
    },
    "underestimating_care": {
        "on_track": {
            "headline": "On Track — Manage Exposure",
            "summary": (
                "You are positioned to absorb a portion of healthcare expenses, but exposure remains."
            ),
            "bullets": [
                "Traditional long-term care insurance",
                "Asset-based or hybrid policies",
                "Personal funding strategies",
            ],
        },
        "at_risk": {
            "headline": "At Risk — High Cost Exposure",
            "summary": (
                "Your plan shows meaningful vulnerability to extended care costs."
            ),
            "bullets": [
                "Traditional long-term care insurance",
                "Hybrid LTC strategies combining protection and asset use",
                "Rely on government (Medicaid) or family",
            ],
        },
        "high_risk": {
            "headline": "High Risk — Significant Impact Likely",
            "summary": (
                "Your plan shows substantial exposure to long-term care costs."
            ),
            "bullets": [
                "Insurance-based solutions",
                "Medicaid planning considerations",
                "Family-based care approaches",
            ],
        },
    },
    "getting_sued": {
        "on_track": {
            "headline": "On Track — Strengthen Existing Protection",
            "summary": (
                "You already have a base level of liability protection in place."
            ),
            "bullets": [
                "Increase existing umbrella insurance coverage",
                "Align liability limits with your total net worth",
                "Review coverage across home and auto policies",
            ],
        },
        "at_risk": {
            "headline": "At Risk — Coverage May Be Insufficient",
            "summary": (
                "Your current liability limits may not fully align with your exposure."
            ),
            "bullets": [
                "Increase umbrella coverage limits",
                "Extend protection beyond base policies",
                "Align coverage with total asset value",
            ],
        },
        "high_risk": {
            "headline": "High Risk — Exposure Exceeds Protection",
            "summary": (
                "Your potential liability exposure may exceed your current coverage."
            ),
            "bullets": [
                "Significantly increase umbrella coverage",
                "Align protection with your full balance sheet",
                "Reduce exposure to large liability events",
            ],
        },
    },
}


def paid_next_step_url(step_key):
    return PAID_REPORT_NEXT_STEP_URLS.get(step_key, PAID_REPORT_NEXT_STEP_URLS["annuity"])


PAID_QUOTE_LINKS = [
    {
        "key": "annuity",
        "label": "Schedule a consultation with an annuity specialist",
        "note": "Market &amp; sequence risk, longevity (sections 1–2)",
    },
    {
        "key": "term_life",
        "label": "Request a term life insurance quote",
        "note": "Survivor income protection (section 3)",
    },
    {
        "key": "ltc",
        "label": "Request a long-term care insurance quote",
        "note": "Healthcare &amp; long-term care (section 4)",
    },
    {
        "key": "umbrella",
        "label": "Request an umbrella insurance quote",
        "note": "Liability protection (section 5)",
    },
]


def get_paid_tier_block(section_key, tier):
    tier = tier if tier in ("on_track", "at_risk", "high_risk") else "on_track"
    return PAID_TIER_CONTENT[section_key][tier]
