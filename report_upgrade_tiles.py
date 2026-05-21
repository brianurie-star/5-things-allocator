"""
Upgrade tiles for the free PDF — placed where the Premium 5 Things Report shows tier-matched strategies.

Free and premium reports share educational copy, research, and observations. The Premium 5 Things Report
only adds the tier-matched "Options to consider" block—not shown in free.
"""

from report_options_solutions import PAID_RISK_SECTIONS, RISK_SOLUTION_ORDER

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
            "<b>longevity income</b> tier (guaranteed income, spending flexibility, and related ideas)."
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
            "<b>liability</b> tier, plus educational umbrella and quote links."
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
