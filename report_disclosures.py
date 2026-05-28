"""
Methodology disclosures for fixed safe-withdrawal vs Monte Carlo reporting.
"""

DATA_PRIVACY_NOTICE_TAGLINE = (
    "Private by design—no cloud database of client plans and no saved user accounts."
)

DATA_PRIVACY_NOTICE_WEB = (
    "We do not store your financial inputs in a cloud database or tie them to a user account. "
    "What you enter is used to calculate results and build your PDF report. "
    "If you download the complimentary report, a short-lived copy (about two hours) may be held "
    "on our server only so you can open the premium report in the same browser session without "
    "re-entering everything—that temporary copy cannot be looked up later by you or by others. "
    "Download and save your PDF if you want a record; we do not keep your plan on file for retrieval."
)

DATA_PRIVACY_DISCLOSURE = (
    "<b>Data handling.</b> We do not store your financial inputs in a cloud database or associate "
    "them with a user account. Information you provide is processed to run the analysis and generate "
    "this PDF. If you requested the complimentary report with the option to upgrade, inputs and chart "
    "data may be held in short-lived server storage (about two hours) so a premium report can be "
    "generated in the same session without re-entry; that storage is not retrievable through the "
    "website after it expires and is not accessible to other users. Keep your downloaded PDF if you "
    "want a lasting copy of this run."
)

DISCLOSURE_COMPARISON = (
    "<b>Fixed withdrawal (safe withdrawal rate) analysis</b> applies a steady annual withdrawal "
    "percentage to your portfolio and compounds remaining assets at an assumed average return. "
    "It is useful for planning conversations and stress-testing paycut risks, but it does not "
    "model the full range of market paths.<br/><br/>"
    "<b>Monte Carlo analysis</b> runs many simulated market scenarios using expected return and "
    "volatility assumptions. It estimates the probability that your plan may succeed under "
    "variable returns and inflation—not a single average outcome.<br/><br/>"
    "These approaches answer different questions. A fixed rate shows what happens if assumptions "
    "hold; Monte Carlo shows how often similar plans have worked across many possible futures."
)

DISCLOSURE_BY_TIER = {
    "free": (
        "<b>This complimentary report uses fixed withdrawal-rate methodology.</b> Income from investable "
        "assets is estimated using the guaranteed and unprotected withdrawal rates you entered, "
        "combined with Social Security, pensions, and other stable income. Investment outcome "
        "ranges use the profile mean return plus or minus standard deviations—they are not a "
        "Monte Carlo probability study.<br/><br/>"
        + DISCLOSURE_COMPARISON
    ),
    "options": (
        "<b>The Premium 5 Things Report</b> presents educational strategies "
        "matched to your risk tier for each paycut category, plus fixed withdrawal-rate comparisons. "
        "Content cites commonly referenced retirement research (e.g., rational decumulation, "
        "guaranteed income) for context only—not as personalized advice. Withdrawal scenarios "
        "assume constant average returns and do not represent Monte Carlo probability of "
        "success. See Important Disclosures in the premium report section for full compliance "
        "language.<br/><br/>"
        + DISCLOSURE_COMPARISON
    ),
    "monte_carlo": (
        "<b>This Probability Study uses Monte Carlo simulation.</b> Portfolio paths are simulated "
        "using your investment profile’s expected return and standard deviation, annual withdrawals "
        "adjusted for inflation, and the planning horizon shown in the report. Outcomes include "
        "estimated success rates and ending-wealth percentiles.<br/><br/>"
        "Monte Carlo results are hypothetical, sensitive to inputs, and not a guarantee of future "
        "performance. They should be compared—not confused—with fixed safe-withdrawal illustrations "
        "that apply a single average return each year.<br/><br/>"
        + DISCLOSURE_COMPARISON
    ),
}

UPGRADE_OPTION_DISCLOSURES = {
    "free": (
        "Uses your entered safe withdrawal rates and profile return assumptions. "
        "Does not include multi-rate option tables or Monte Carlo probability outputs."
    ),
    "options": (
        "Same education, research, and observations as the complimentary report, plus tier-matched "
        "tier-matched options to consider for all five paycut risks and a withdrawal-rate "
        "comparison. Fixed-rate analysis—not Monte Carlo. Not personalized advice."
    ),
    "monte_carlo": (
        "Monte Carlo simulation only. Estimates probability of sustaining the plan across many "
        "random return sequences—not a single safe withdrawal rate illustration."
    ),
    "advisor": (
        "Advisor-led review—not an instant download. Your advisor prepares and interprets a "
        "Monte Carlo probability study using your household data in a planning conversation."
    ),
}
