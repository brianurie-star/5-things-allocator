PORTFOLIO_PROFILES = {
    "aggressive": {"label": "Aggressive", "equity": 0.95, "mean": 10.67, "stdev": 14.79},
    "growth": {"label": "Growth", "equity": 0.80, "mean": 9.89, "stdev": 12.37},
    "growthIncome": {"label": "Growth With Income", "equity": 0.60, "mean": 8.88, "stdev": 9.34},
    "intermediate": {"label": "Intermediate Growth", "equity": 0.40, "mean": 7.77, "stdev": 6.16},
}


def num(data, key, default=0):
    value = data.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def calculate_results(data):
    risk_profile = data.get("risk_profile", "growth")
    profile = PORTFOLIO_PROFILES.get(risk_profile, PORTFOLIO_PROFILES["growth"])

    his_social_security = num(data, "his_social_security")
    her_social_security = num(data, "her_social_security")
    his_pension = num(data, "his_pension")
    her_pension = num(data, "her_pension")
    his_other_income = num(data, "his_other_income")
    her_other_income = num(data, "her_other_income")
    monthly_living_expenses = num(data, "monthly_living_expenses")
    retirement_assets = num(data, "retirement_assets")
    non_retirement_assets = num(data, "non_retirement_assets")
    guaranteed_income_allocation = num(data, "guaranteed_income_allocation")
    guaranteed_withdrawal_rate = num(data, "guaranteed_withdrawal_rate")
    unprotected_withdrawal_rate = num(data, "unprotected_withdrawal_rate")
    inflation = num(data, "inflation")
    his_age = num(data, "his_age")
    her_age = num(data, "her_age")
    his_life_expectancy = num(data, "his_life_expectancy")
    her_life_expectancy = num(data, "her_life_expectancy")
    tax_rate = num(data, "tax_rate")
    monthly_ltc_cost = num(data, "monthly_ltc_cost")
    ltc_years = num(data, "ltc_years")
    lawsuit_award = num(data, "lawsuit_award")
    life_insurance_premium = num(data, "life_insurance_premium")
    life_insurance_protection = num(data, "life_insurance_protection")
    ltc_insurance_premium = num(data, "ltc_insurance_premium")
    ltc_insurance_protection = num(data, "ltc_insurance_protection")
    auto_insurance_premium = num(data, "auto_insurance_premium")
    auto_insurance_protection = num(data, "auto_insurance_protection")
    home_insurance_premium = num(data, "home_insurance_premium")
    home_insurance_protection = num(data, "home_insurance_protection")
    umbrella_insurance_premium = num(data, "umbrella_insurance_premium")
    umbrella_insurance_protection = num(data, "umbrella_insurance_protection")

    total_ss_monthly = his_social_security + her_social_security
    total_pension_monthly = his_pension + her_pension
    total_other_monthly = his_other_income + her_other_income
    total_investable_assets = retirement_assets + non_retirement_assets

    protected_assets = total_investable_assets * guaranteed_income_allocation
    unprotected_assets = total_investable_assets - protected_assets
    stock_assets = unprotected_assets * profile["equity"]
    bond_assets = unprotected_assets * (1 - profile["equity"])

    annual_protected_income_from_assets = protected_assets * guaranteed_withdrawal_rate
    annual_unprotected_income_from_assets = unprotected_assets * unprotected_withdrawal_rate

    monthly_protected_income = (
        total_ss_monthly
        + total_pension_monthly
        + (annual_protected_income_from_assets / 12)
    )
    monthly_unprotected_income = total_other_monthly + (annual_unprotected_income_from_assets / 12)
    total_monthly_income = monthly_protected_income + monthly_unprotected_income

    estimated_taxes_monthly = total_monthly_income * tax_rate
    total_monthly_expenses = monthly_living_expenses + estimated_taxes_monthly
    extras_monthly = max(total_monthly_income - total_monthly_expenses, 0)

    his_retirement_years = max(his_life_expectancy - his_age, 0)
    her_retirement_years = max(her_life_expectancy - her_age, 0)

    if inflation > 0:
        loss_of_his_ss = ((his_social_security * 12) * (1 - (1 + inflation) ** (-his_retirement_years))) / inflation
        loss_of_her_ss = ((her_social_security * 12) * (1 - (1 + inflation) ** (-her_retirement_years))) / inflation
    else:
        loss_of_his_ss = 0
        loss_of_her_ss = 0

    assets_at_risk_early_death = max(min(loss_of_his_ss, loss_of_her_ss) - life_insurance_protection, 0)
    ltc_cost_total = monthly_ltc_cost * 12 * ltc_years * 2
    assets_at_risk_ltc = max(ltc_cost_total - ltc_insurance_protection, 0)

    liability_coverage = auto_insurance_protection + home_insurance_protection + umbrella_insurance_protection
    net_at_risk_lawsuit = max(
        lawsuit_award - liability_coverage - (annual_protected_income_from_assets + total_ss_monthly * 12 + total_pension_monthly * 12),
        0,
    )

    total_protection_spend = (
        5000
        + life_insurance_premium * 12
        + ltc_insurance_premium * 12
        + auto_insurance_premium * 12
        + home_insurance_premium * 12
        + umbrella_insurance_premium * 12
    )

    annual_surplus = max((total_monthly_income - total_monthly_expenses) * 12, 0)

    return {
        "profile_label": profile["label"],
        "monthly_income": round(total_monthly_income, 2),
        "monthly_expenses": round(total_monthly_expenses, 2),
        "protected_monthly_income": round(monthly_protected_income, 2),
        "unprotected_monthly_income": round(monthly_unprotected_income, 2),
        "estimated_taxes_monthly": round(estimated_taxes_monthly, 2),
        "extras_monthly": round(extras_monthly, 2),
        "investable_assets": round(total_investable_assets, 2),
        "protected_assets": round(protected_assets, 2),
        "unprotected_assets": round(unprotected_assets, 2),
        "stock_assets": round(stock_assets, 2),
        "bond_assets": round(bond_assets, 2),
        "assets_at_risk_early_death": round(assets_at_risk_early_death, 2),
        "assets_at_risk_ltc": round(assets_at_risk_ltc, 2),
        "net_at_risk_lawsuit": round(net_at_risk_lawsuit, 2),
        "ltc_cost_total": round(ltc_cost_total, 2),
        "total_protection_spend": round(total_protection_spend, 2),
        "annual_surplus": round(annual_surplus, 2),
        "market_mean": round(profile["mean"], 2),
        "market_range_68_low": round(profile["mean"] - profile["stdev"], 2),
        "market_range_68_high": round(profile["mean"] + profile["stdev"], 2),
        "market_range_98_low": round(profile["mean"] - 2 * profile["stdev"], 2),
        "market_range_98_high": round(profile["mean"] + 2 * profile["stdev"], 2),
    }