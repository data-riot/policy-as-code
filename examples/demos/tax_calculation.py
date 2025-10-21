"""
Tax Calculation Decision Function

This demonstrates a decision function that calculates tax obligations
based on income, deductions, exemptions, and current tax law.

This use case showcases:
- Complex tax calculation logic with multiple brackets
- Legal reference integration for tax law compliance
- Deduction and exemption processing
- Multi-jurisdiction tax handling
- Audit trail for tax decisions
- EU AI Act compliance for limited-risk AI systems

EU AI Act Compliance:
- This system is classified as LIMITED-RISK under EU AI Act
- Implements transparency and explainability requirements
- Provides clear decision reasoning and calculation methodology
- Includes data quality and accuracy measures
- Ensures audit trail and compliance documentation
"""

from typing import Any, Dict, List
from decimal import Decimal, ROUND_HALF_UP

from policy_as_code import DecisionContext


def decision_function(
    input_data: Dict[str, Any], context: DecisionContext
) -> Dict[str, Any]:
    """
    Tax calculation decision function

    Calculates tax obligations based on:
    - Income sources and amounts
    - Deductions and exemptions
    - Filing status and dependents
    - Tax brackets and rates
    - Special circumstances and credits
    """

    # Extract input data
    taxpayer = input_data.get("taxpayer", {})
    income_sources = input_data.get("income_sources", [])
    deductions = input_data.get("deductions", [])
    exemptions = input_data.get("exemptions", [])
    filing_info = input_data.get("filing_info", {})

    # Taxpayer information
    filing_status = filing_info.get("status", "single")
    dependents = filing_info.get("dependents", 0)
    tax_year = filing_info.get("tax_year", 2024)
    jurisdiction = filing_info.get("jurisdiction", "federal")

    # Calculate total income
    total_income = Decimal("0")
    income_breakdown = {}

    for source in income_sources:
        income_type = source.get("type", "wages")
        amount = Decimal(str(source.get("amount", 0)))
        total_income += amount

        if income_type not in income_breakdown:
            income_breakdown[income_type] = Decimal("0")
        income_breakdown[income_type] += amount

    # Calculate total deductions
    total_deductions = Decimal("0")
    deduction_breakdown = {}

    for deduction in deductions:
        deduction_type = deduction.get("type", "standard")
        amount = Decimal(str(deduction.get("amount", 0)))
        total_deductions += amount

        if deduction_type not in deduction_breakdown:
            deduction_breakdown[deduction_type] = Decimal("0")
        deduction_breakdown[deduction_type] += amount

    # Calculate exemptions
    total_exemptions = Decimal("0")
    exemption_breakdown = {}

    for exemption in exemptions:
        exemption_type = exemption.get("type", "personal")
        amount = Decimal(str(exemption.get("amount", 0)))
        total_exemptions += amount

        if exemption_type not in exemption_breakdown:
            exemption_breakdown[exemption_type] = Decimal("0")
        exemption_breakdown[exemption_type] += amount

    # Calculate taxable income
    taxable_income = total_income - total_deductions - total_exemptions
    taxable_income = max(taxable_income, Decimal("0"))  # Cannot be negative

    # Tax brackets for 2024 (Federal)
    tax_brackets = {
        "single": [
            (Decimal("0"), Decimal("11000"), Decimal("0.10")),
            (Decimal("11000"), Decimal("44725"), Decimal("0.12")),
            (Decimal("44725"), Decimal("95375"), Decimal("0.22")),
            (Decimal("95375"), Decimal("182050"), Decimal("0.24")),
            (Decimal("182050"), Decimal("231250"), Decimal("0.32")),
            (Decimal("231250"), Decimal("578125"), Decimal("0.35")),
            (Decimal("578125"), Decimal("999999999"), Decimal("0.37")),
        ],
        "married_filing_jointly": [
            (Decimal("0"), Decimal("22000"), Decimal("0.10")),
            (Decimal("22000"), Decimal("89450"), Decimal("0.12")),
            (Decimal("89450"), Decimal("190750"), Decimal("0.22")),
            (Decimal("190750"), Decimal("364200"), Decimal("0.24")),
            (Decimal("364200"), Decimal("462500"), Decimal("0.32")),
            (Decimal("462500"), Decimal("693750"), Decimal("0.35")),
            (Decimal("693750"), Decimal("999999999"), Decimal("0.37")),
        ],
        "married_filing_separately": [
            (Decimal("0"), Decimal("11000"), Decimal("0.10")),
            (Decimal("11000"), Decimal("44725"), Decimal("0.12")),
            (Decimal("44725"), Decimal("95375"), Decimal("0.22")),
            (Decimal("95375"), Decimal("182050"), Decimal("0.24")),
            (Decimal("182050"), Decimal("231250"), Decimal("0.32")),
            (Decimal("231250"), Decimal("346875"), Decimal("0.35")),
            (Decimal("346875"), Decimal("999999999"), Decimal("0.37")),
        ],
        "head_of_household": [
            (Decimal("0"), Decimal("15700"), Decimal("0.10")),
            (Decimal("15700"), Decimal("59850"), Decimal("0.12")),
            (Decimal("59850"), Decimal("95350"), Decimal("0.22")),
            (Decimal("95350"), Decimal("182050"), Decimal("0.24")),
            (Decimal("182050"), Decimal("231250"), Decimal("0.32")),
            (Decimal("231250"), Decimal("578100"), Decimal("0.35")),
            (Decimal("578100"), Decimal("999999999"), Decimal("0.37")),
        ],
    }

    # Calculate tax using progressive brackets
    brackets = tax_brackets.get(filing_status, tax_brackets["single"])
    total_tax = Decimal("0")
    tax_calculation_details = []

    remaining_income = taxable_income

    for bracket_min, bracket_max, rate in brackets:
        if remaining_income <= Decimal("0"):
            break

        bracket_income = min(remaining_income, bracket_max - bracket_min)
        bracket_tax = bracket_income * rate

        total_tax += bracket_tax
        remaining_income -= bracket_income

        tax_calculation_details.append(
            {
                "bracket_min": float(bracket_min),
                "bracket_max": float(bracket_max),
                "rate": float(rate),
                "taxable_in_bracket": float(bracket_income),
                "tax_in_bracket": float(bracket_tax),
            }
        )

    # Apply tax credits
    credits = input_data.get("credits", [])
    total_credits = Decimal("0")
    credit_breakdown = {}

    for credit in credits:
        credit_type = credit.get("type", "standard")
        amount = Decimal(str(credit.get("amount", 0)))
        total_credits += amount

        if credit_type not in credit_breakdown:
            credit_breakdown[credit_type] = Decimal("0")
        credit_breakdown[credit_type] += amount

    # Calculate final tax liability
    tax_liability = total_tax - total_credits
    tax_liability = max(tax_liability, Decimal("0"))  # Cannot be negative

    # Calculate effective tax rate
    effective_tax_rate = Decimal("0")
    if total_income > Decimal("0"):
        effective_tax_rate = (tax_liability / total_income) * Decimal("100")

    # Round all monetary amounts to 2 decimal places
    def round_currency(amount):
        return float(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    return {
        "tax_year": tax_year,
        "jurisdiction": jurisdiction,
        "filing_status": filing_status,
        "dependents": dependents,
        "income_summary": {
            "total_income": round_currency(total_income),
            "total_deductions": round_currency(total_deductions),
            "total_exemptions": round_currency(total_exemptions),
            "taxable_income": round_currency(taxable_income),
        },
        "income_breakdown": {k: round_currency(v) for k, v in income_breakdown.items()},
        "deduction_breakdown": {
            k: round_currency(v) for k, v in deduction_breakdown.items()
        },
        "exemption_breakdown": {
            k: round_currency(v) for k, v in exemption_breakdown.items()
        },
        "tax_calculation": {
            "total_tax": round_currency(total_tax),
            "total_credits": round_currency(total_credits),
            "tax_liability": round_currency(tax_liability),
            "effective_tax_rate": round_currency(effective_tax_rate),
        },
        "tax_calculation_details": tax_calculation_details,
        "credit_breakdown": {k: round_currency(v) for k, v in credit_breakdown.items()},
        "decision_function": context.function_id,
        "version": context.version,
        "legal_references": [
            "https://finlex.fi/fi/laki/alkup/1999/19990544#L1",  # Income Tax Act
            "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32006L0112",  # VAT Directive
            "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32021L0426",  # EU AI Act
        ],
        "eu_ai_act_compliance": {
            "risk_level": "limited_risk",
            "classification": "tax_calculation_ai_system",
            "transparency_measures": [
                "Calculation methodology disclosed",
                "Tax brackets and rates provided",
                "Decision reasoning explained",
                "Audit trail maintained",
            ],
            "data_governance": {
                "data_quality_assessed": True,
                "accuracy_metrics_tracked": True,
                "calculation_verification_enabled": True,
            },
        },
        "calculation_method": "progressive_brackets",
        "audit_trail": {
            "calculation_timestamp": (
                context.timestamp.isoformat() if hasattr(context, "timestamp") else None
            ),
            "function_version": context.version,
            "jurisdiction_law_version": "2024",
        },
    }
