from flask import Flask, render_template, request, jsonify, send_file, url_for, redirect
import io
import os
import tempfile

from export_cache import load_export_payload, save_export_payload
from report import generate_premium_client_report, save_base64_png
from brand_serve import brand_asset, register_brand_routes
from alpine_retirement_consulting import create_blueprint

REPORT_DOWNLOAD_NAMES = {
    "free": "retirement_report.pdf",
    "options": "retirement_options_report.pdf",
    "monte_carlo": "retirement_probability_study.pdf",
}

# Option 3 on /upgrade — advisor-led review (not a self-serve PDF export).
ADVISOR_APPOINTMENT_URL = os.environ.get(
    "ADVISOR_APPOINTMENT_URL",
    "https://www.macu.com/burie",
)

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(_APP_DIR, "templates"),
    static_folder=os.path.join(_APP_DIR, "static"),
)

register_brand_routes(app)
app.register_blueprint(create_blueprint(url_prefix="/"))
app.context_processor(lambda: {"brand_asset": brand_asset})

DEFAULT_INPUTS = {
    "client_name": "Sample Client",
    "report_date": "2024-03-01",
    "his_age": 65,
    "her_age": 65,
    "his_social_security": 3100,
    "her_social_security": 1600,
    "his_pension": 0,
    "her_pension": 0,
    "his_other_income": 0,
    "her_other_income": 0,
    "monthly_living_expenses": 5500,
    "retirement_assets": 750000,
    "non_retirement_assets": 110000,
    "home_value": 750000,
    "mortgage_balance": 100000,
    "guaranteed_income_allocation": 0.15,
    "risk_profile": "growth",
    "guaranteed_withdrawal_rate": 0.06,
    "unprotected_withdrawal_rate": 0.04,
    "inflation": 0.03,
    "his_life_expectancy": 90,
    "her_life_expectancy": 90,
    "tax_rate": 0.18,
    "monthly_ltc_cost": 4500,
    "ltc_years": 3,
    "lawsuit_award": 1000000,
    "life_insurance_protection": 0,
    "ltc_insurance_protection": 0,
    "auto_insurance_protection": 300000,
    "home_insurance_protection": 300000,
    "umbrella_insurance_protection": 0,
    "life_insurance_monthly_cost": 0,
    "ltc_insurance_monthly_cost": 0,
    "auto_insurance_monthly_cost": 0,
    "home_insurance_monthly_cost": 0,
    "umbrella_insurance_monthly_cost": 0,
    "aggressive_equity": 95,
    "aggressive_mean": 10.67,
    "aggressive_stdev": 14.79,
    "growth_equity": 80,
    "growth_mean": 9.89,
    "growth_stdev": 12.37,
    "growthIncome_equity": 60,
    "growthIncome_mean": 8.88,
    "growthIncome_stdev": 9.34,
    "intermediate_equity": 40,
    "intermediate_mean": 7.77,
    "intermediate_stdev": 6.16,
}


def to_float(value, default=0.0):
    try:
        if value in ("", None):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def get_home_equity_factor(age):
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


def _pv_of_monthly_benefit(monthly_amount, years, inflation_rate):
    """Present value of a monthly income stream over remaining retirement years."""
    annual = monthly_amount * 12
    if years <= 0 or annual <= 0:
        return 0.0
    if inflation_rate <= 0:
        return annual * years
    return annual * (1 - (1 + inflation_rate) ** (-years)) / inflation_rate


def early_death_social_security_exposure(data):
    """
    Estimate at-risk dollars as the present value of the smaller Social Security
    benefit stream (lost if that spouse dies first), minus life insurance protection.
    """
    his_ss = to_float(data.get("his_social_security"))
    her_ss = to_float(data.get("her_social_security"))
    his_age = to_float(data.get("his_age"))
    her_age = to_float(data.get("her_age"))
    his_years = max(to_float(data.get("his_life_expectancy")) - his_age, 0)
    her_years = max(to_float(data.get("her_life_expectancy")) - her_age, 0)
    inflation = to_float(data.get("inflation"))
    if inflation > 1:
        inflation /= 100.0

    pv_his = _pv_of_monthly_benefit(his_ss, his_years, inflation)
    pv_her = _pv_of_monthly_benefit(her_ss, her_years, inflation)
    gross_exposure = min(pv_his, pv_her)
    life_insurance_protection = to_float(data.get("life_insurance_protection"))
    return max(gross_exposure - life_insurance_protection, 0.0)


def get_portfolio_profiles(data):
    return {
        "aggressive": {
            "label": "Aggressive",
            "equity": to_float(data.get("aggressive_equity", 95)) / 100,
            "mean": to_float(data.get("aggressive_mean", 10.67)),
            "stdev": to_float(data.get("aggressive_stdev", 14.79)),
        },
        "growth": {
            "label": "Growth",
            "equity": to_float(data.get("growth_equity", 80)) / 100,
            "mean": to_float(data.get("growth_mean", 9.89)),
            "stdev": to_float(data.get("growth_stdev", 12.37)),
        },
        "growthIncome": {
            "label": "Growth With Income",
            "equity": to_float(data.get("growthIncome_equity", 60)) / 100,
            "mean": to_float(data.get("growthIncome_mean", 8.88)),
            "stdev": to_float(data.get("growthIncome_stdev", 9.34)),
        },
        "intermediate": {
            "label": "Intermediate Growth",
            "equity": to_float(data.get("intermediate_equity", 40)) / 100,
            "mean": to_float(data.get("intermediate_mean", 7.77)),
            "stdev": to_float(data.get("intermediate_stdev", 6.16)),
        },
    }


def calculate_results(data):
    portfolio_profiles = get_portfolio_profiles(data)

    balance_sheet_mode = data.get("balance_sheet_mode", "partial")

    his_ss = to_float(data.get("his_social_security"))
    her_ss = to_float(data.get("her_social_security"))
    his_pension = to_float(data.get("his_pension"))
    her_pension = to_float(data.get("her_pension"))
    his_other = to_float(data.get("his_other_income"))
    her_other = to_float(data.get("her_other_income"))

    base_income = his_ss + her_ss + his_pension + her_pension + his_other + her_other

    retirement_assets = to_float(data.get("retirement_assets"))
    non_retirement_assets = to_float(data.get("non_retirement_assets"))
    base_investable_assets = retirement_assets + non_retirement_assets

    his_age = to_float(data.get("his_age"))
    her_age = to_float(data.get("her_age"))
    planning_age = max(his_age, her_age)

    home_value = to_float(data.get("home_value"))
    mortgage_balance = to_float(data.get("mortgage_balance"))
    net_home_equity = max(home_value - mortgage_balance, 0)
    home_equity_factor = get_home_equity_factor(planning_age)
    accessible_home_equity = net_home_equity * home_equity_factor

    if balance_sheet_mode == "full":
        investable_assets = base_investable_assets + accessible_home_equity
    else:
        investable_assets = base_investable_assets

    guaranteed_income_allocation = to_float(data.get("guaranteed_income_allocation"))
    protected_assets = investable_assets * guaranteed_income_allocation
    unprotected_assets = max(investable_assets - protected_assets, 0)

    risk_profile_key = data.get("risk_profile") or "growth"
    profile = portfolio_profiles.get(risk_profile_key, portfolio_profiles["growth"])

    stock_assets = unprotected_assets * profile["equity"]
    bond_assets = unprotected_assets * (1 - profile["equity"])

    guaranteed_withdrawal_rate = to_float(data.get("guaranteed_withdrawal_rate"))
    unprotected_withdrawal_rate = to_float(data.get("unprotected_withdrawal_rate"))

    guaranteed_withdrawal_monthly = (protected_assets * guaranteed_withdrawal_rate) / 12
    unprotected_withdrawal_monthly = ((stock_assets + bond_assets) * unprotected_withdrawal_rate) / 12

    estimated_home_equity_income_monthly = (accessible_home_equity * 0.05) / 12

    monthly_income = (
        base_income
        + guaranteed_withdrawal_monthly
        + unprotected_withdrawal_monthly
    )

    full_balance_sheet_monthly_income = monthly_income + estimated_home_equity_income_monthly

    basic_expenses = to_float(data.get("monthly_living_expenses"))
    tax_rate = to_float(data.get("tax_rate"))

    life_insurance_monthly_cost = to_float(data.get("life_insurance_monthly_cost"))
    ltc_insurance_monthly_cost = to_float(data.get("ltc_insurance_monthly_cost"))
    auto_insurance_monthly_cost = to_float(data.get("auto_insurance_monthly_cost"))
    home_insurance_monthly_cost = to_float(data.get("home_insurance_monthly_cost"))
    umbrella_insurance_monthly_cost = to_float(data.get("umbrella_insurance_monthly_cost"))

    total_protection_monthly_cost = (
        life_insurance_monthly_cost
        + ltc_insurance_monthly_cost
        + auto_insurance_monthly_cost
        + home_insurance_monthly_cost
        + umbrella_insurance_monthly_cost
    )

    estimated_taxes = monthly_income * tax_rate
    monthly_expenses = basic_expenses + total_protection_monthly_cost + estimated_taxes
    extras = max(monthly_income - monthly_expenses, 0)

    monthly_ltc_cost = to_float(data.get("monthly_ltc_cost"))
    ltc_years = to_float(data.get("ltc_years"))
    ltc_insurance_protection = to_float(data.get("ltc_insurance_protection"))
    assets_at_risk_ltc = max((monthly_ltc_cost * 12 * ltc_years * 2) - ltc_insurance_protection, 0)

    assets_at_risk_early_death = early_death_social_security_exposure(data)

    lawsuit_award = to_float(data.get("lawsuit_award"))
    auto_insurance_protection = to_float(data.get("auto_insurance_protection"))
    home_insurance_protection = to_float(data.get("home_insurance_protection"))
    umbrella_insurance_protection = to_float(data.get("umbrella_insurance_protection"))

    base_liability_protection = max(auto_insurance_protection, home_insurance_protection)
    liability_coverage = base_liability_protection + umbrella_insurance_protection
    net_at_risk_lawsuit = max(lawsuit_award - liability_coverage, 0)

    protected_monthly_income = his_ss + her_ss + his_pension + her_pension + guaranteed_withdrawal_monthly

    self_insurance_total = (
        assets_at_risk_early_death
        + assets_at_risk_ltc
        + net_at_risk_lawsuit
    )

    return {
        "monthly_income": round(monthly_income, 2),
        "monthly_expenses": round(monthly_expenses, 2),
        "estimated_taxes_monthly": round(estimated_taxes, 2),
        "extras_monthly": round(extras, 2),
        "investable_assets": round(investable_assets, 2),
        "base_investable_assets": round(base_investable_assets, 2),
        "protected_assets": round(protected_assets, 2),
        "stock_assets": round(stock_assets, 2),
        "bond_assets": round(bond_assets, 2),
        "profile_label": profile["label"],
        "market_mean": round(profile["mean"], 2),
        "market_range_98_low": round(profile["mean"] - (2 * profile["stdev"]), 2),
        "market_range_98_high": round(profile["mean"] + (2 * profile["stdev"]), 2),
        "market_range_68_low": round(profile["mean"] - profile["stdev"], 2),
        "market_range_68_high": round(profile["mean"] + profile["stdev"], 2),
        "assets_at_risk_ltc": round(assets_at_risk_ltc, 2),
        "assets_at_risk_early_death": round(assets_at_risk_early_death, 2),
        "net_at_risk_lawsuit": round(net_at_risk_lawsuit, 2),
        "protected_monthly_income": round(protected_monthly_income, 2),
        "unprotected_monthly_income": round(his_other + her_other, 2),
        "guaranteed_withdrawal_monthly": round(guaranteed_withdrawal_monthly, 2),
        "unprotected_withdrawal_monthly": round(unprotected_withdrawal_monthly, 2),
        "home_value": round(home_value, 2),
        "mortgage_balance": round(mortgage_balance, 2),
        "net_home_equity": round(net_home_equity, 2),
        "accessible_home_equity": round(accessible_home_equity, 2),
        "available_home_equity": round(accessible_home_equity, 2),
        "estimated_home_equity_income_monthly": round(estimated_home_equity_income_monthly, 2),
        "full_balance_sheet_monthly_income": round(full_balance_sheet_monthly_income, 2),
        "self_insurance_total": round(self_insurance_total, 2),
        "total_protection_monthly_cost": round(total_protection_monthly_cost, 2),
        "life_insurance_monthly_cost": round(life_insurance_monthly_cost, 2),
        "ltc_insurance_monthly_cost": round(ltc_insurance_monthly_cost, 2),
        "auto_insurance_monthly_cost": round(auto_insurance_monthly_cost, 2),
        "home_insurance_monthly_cost": round(home_insurance_monthly_cost, 2),
        "umbrella_insurance_monthly_cost": round(umbrella_insurance_monthly_cost, 2),
    }


@app.route("/five-things")
def home():
    from report_disclosures import DATA_PRIVACY_NOTICE_TAGLINE, DATA_PRIVACY_NOTICE_WEB

    return render_template(
        "home.html",
        privacy_tagline=DATA_PRIVACY_NOTICE_TAGLINE,
        privacy_notice=DATA_PRIVACY_NOTICE_WEB,
    )


@app.route("/consulting")
@app.route("/consulting/")
def consulting_redirect():
    return redirect(url_for("alpine_consulting.home"))


@app.route("/allocator")
def allocator():
    from report_disclosures import DATA_PRIVACY_NOTICE_WEB

    return render_template(
        "index.html",
        defaults=DEFAULT_INPUTS,
        privacy_notice=DATA_PRIVACY_NOTICE_WEB,
    )


@app.route("/upgrade")
def upgrade():
    from report_disclosures import (
        DATA_PRIVACY_NOTICE_WEB,
        DISCLOSURE_COMPARISON,
        UPGRADE_OPTION_DISCLOSURES,
    )

    cache_id = request.args.get("cache", "").strip() or None
    return render_template(
        "upgrade.html",
        comparison_disclosure=DISCLOSURE_COMPARISON,
        option_disclosures=UPGRADE_OPTION_DISCLOSURES,
        privacy_notice=DATA_PRIVACY_NOTICE_WEB,
        cache_id=cache_id,
        appointment_url=ADVISOR_APPOINTMENT_URL,
    )


@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.get_json(force=True) or {}
    return jsonify(calculate_results(data))


@app.route("/export-pdf", methods=["POST"])
def export_pdf():
    try:
        payload = request.get_json(force=True) or {}
        tier = (payload.get("tier") or "free").lower()
        if tier in ("premium", "paid"):
            tier = "options"
        cache_id = payload.get("cache_id")

        if cache_id:
            cached_inputs, cached_charts = load_export_payload(cache_id)
            inputs = cached_inputs or payload.get("inputs", {}) or {}
            charts = cached_charts or payload.get("charts", {}) or {}
        else:
            inputs = payload.get("inputs", {}) or {}
            charts = payload.get("charts", {}) or {}

        if tier not in REPORT_DOWNLOAD_NAMES:
            tier = "free"

        if tier == "free" and payload.get("store_for_upgrade") and not cache_id:
            cache_id = save_export_payload(inputs, charts)

        upgrade_url = None
        if tier == "free":
            upgrade_url = url_for("upgrade", cache=cache_id, _external=True) if cache_id else url_for(
                "upgrade", _external=True
            )

        results = calculate_results(inputs)
        report_data = {**inputs, **results}

        with tempfile.TemporaryDirectory() as tmpdir:
            chart_paths = {}
            for key, val in charts.items():
                path = save_base64_png(val, tmpdir, f"{key}.png")
                if path:
                    chart_paths[key] = path

            pdf_path = os.path.join(tmpdir, "report.pdf")
            try:
                generate_premium_client_report(
                    report_data,
                    chart_paths,
                    pdf_path,
                    report_tier=tier,
                    upgrade_url=upgrade_url,
                )
            except Exception as chart_err:
                import traceback
                traceback.print_exc()
                generate_premium_client_report(
                    report_data,
                    {},
                    pdf_path,
                    report_tier=tier,
                    upgrade_url=upgrade_url,
                )
                if tier == "options":
                    app.logger.warning(
                        "Premium PDF generated without chart images after error: %s",
                        chart_err,
                    )

            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

        if tier == "free" and payload.get("store_for_upgrade") and cache_id:
            response = send_file(
                io.BytesIO(pdf_bytes),
                mimetype="application/pdf",
                as_attachment=True,
                download_name=REPORT_DOWNLOAD_NAMES["free"],
            )
            response.headers["X-Export-Cache-Id"] = cache_id
            return response

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=REPORT_DOWNLOAD_NAMES.get(tier, "retirement_report.pdf"),
        )
    except Exception as e:
        return f"PDF export failed on server: {str(e)}", 500


if __name__ == "__main__":
    app.run(debug=True)