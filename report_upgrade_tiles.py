"""
Upgrade tiles for the free PDF — placed where the Premium 5 Things Report shows tier-matched strategies.

Free and premium reports share educational copy, research, and observations. The Premium 5 Things Report
only adds the tier-matched "Options to consider" block—not shown in free.
"""

import os

from report_options_solutions import PAID_RISK_SECTIONS, RISK_SOLUTION_ORDER

_ADVISOR_URL = os.environ.get("ADVISOR_APPOINTMENT_URL", "https://www.macu.com/burie")

FREE_ADVISOR_PROBABILITY_INVITE = {
    "eyebrow": "Advisor-driven",
    "title": "Advanced- Probability review",
    "price": "$999",
    "summary": (
        "Everything in this complimentary report, plus a <b>Monte Carlo probability study</b> with "
        "success rates and ending-wealth percentiles across simulated market paths—and consultation "
        "with an advisor to interpret what the results mean for your plan."
    ),
    "note": (
        "This is an advisor-led review, not an instant PDF download. Schedule a consultation to "
        "request the advanced probability review."
    ),
    "cta_label": "Schedule a consultation",
    "appointment_url": _ADVISOR_URL,
}

FREE_OPTIONS_UPGRADE_TILES = {
    "flaw_of_averages": {
        "summary": (
            "Premium report adds a tier-matched <b>options to consider</b> list for your "
            "<b>sequence-of-returns</b> classification, plus withdrawal-rate comparisons."
        ),
    },
    "living_too_long": {
        "summary": (
            "Premium report adds tier-matched <b>options to consider</b> for your "
            "<b>longevity income</b> tier."
        ),
    },
    "dying_too_soon": {
        "summary": (
            "Premium report adds tier-matched <b>options to consider</b> for your "
            "<b>survivor income</b> tier, including life-income protection concepts."
        ),
    },
    "underestimating_care": {
        "summary": (
            "Premium report adds tier-matched <b>options to consider</b> for your "
            "<b>care-cost exposure</b> tier (insurance, funding approaches, and related ideas)."
        ),
    },
    "getting_sued": {
        "summary": (
            "Premium report adds tier-matched <b>options to consider</b> for your "
            "<b>liability</b> tier."
        ),
    },
}


def free_options_upgrade_tile_copy(section_key):
    meta = PAID_RISK_SECTIONS.get(section_key, {})
    tile = FREE_OPTIONS_UPGRADE_TILES.get(section_key, {})
    return {
        "section_title": meta.get("title", section_key.replace("_", " ").title()),
        "section_subtitle": meta.get("subtitle", ""),
        **tile,
    }


def iter_free_options_upgrade_sections():
    for key in RISK_SOLUTION_ORDER:
        if key in FREE_OPTIONS_UPGRADE_TILES:
            yield key, free_options_upgrade_tile_copy(key)
