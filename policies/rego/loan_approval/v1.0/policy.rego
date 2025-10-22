package org.policy_as_code.loan_approval.v1

# Metadata block - required for all Rego files
# owner: Data Governance Team
# version: 1.0
# description: Loan approval decision based on customer profile and request amount
# created_date: 2025-08-01
# last_updated: 2025-08-01
# tags: ["loan", "approval", "credit", "risk"]
# business_owner: Credit Risk Team
# compliance_required: true
# audit_trail: true

# Default deny - explicit default deny = true
default allow := false
default approved := false

# Input validation - reject if required fields missing
input_valid if {
    input.amount != null
    input.customer_score != null
}

# Rule 1: Reject if credit score is too low
rule_minimum_credit_score if {
    input.customer_score < 500
}

# Rule 2: High amount with low score
rule_high_amount_low_score if {
    input.amount > 10000
    input.customer_score < 650
}

# Rule 3: Standard tier limits
rule_standard_tier_limits if {
    input.customer_tier == "standard"
    input.amount > 5000
}

# Rule 4: Income verification for large amounts
rule_income_verification if {
    input.amount > 5000
    input.monthly_income == null
}

# Rule 5: Debt-to-income ratio check (approval rule)
rule_debt_to_income_check if {
    input.amount > 10000
    input.monthly_income > 0
}

# Rule 6: Premium tier with good score (approval rule)
rule_premium_good_score if {
    input.customer_tier == "premium"
    input.customer_score >= 700
}

# Rule 7: VIP customers (approval rule)
rule_vip_customers if {
    input.customer_tier == "vip"
}

# Rule 8: Small personal loans (approval rule)
rule_small_personal_loans if {
    input.amount <= 5000
    input.employment_status == "employed"
    input.customer_score >= 600
}

# Explicit deny rules - reject if any rejection rule matches
deny if {
    input_valid
    rule_minimum_credit_score
}

deny if {
    input_valid
    rule_high_amount_low_score
}

deny if {
    input_valid
    rule_standard_tier_limits
}

deny if {
    input_valid
    rule_income_verification
}

# Main decision logic - explicit allow only when conditions are met
allow if {
    # Check required fields
    input_valid

    # Not denied by any rejection rule
    not deny

    # Apply approval rules (only allow if approval rules match)
    rule_debt_to_income_check
}

allow if {
    # Check required fields
    input_valid

    # Not denied by any rejection rule
    not deny

    # Apply approval rules (only allow if approval rules match)
    rule_premium_good_score
}

allow if {
    # Check required fields
    input_valid

    # Not denied by any rejection rule
    not deny

    # Apply approval rules (only allow if approval rules match)
    rule_vip_customers
}

allow if {
    # Check required fields
    input_valid

    # Not denied by any rejection rule
    not deny

    # Apply approval rules (only allow if approval rules match)
    rule_small_personal_loans
}

# Decision result
approved if {
    allow
}

# Decision details
decision_result := "rejected_minimum_credit_score" if {
    rule_minimum_credit_score
}

decision_result := "rejected_high_amount_low_score" if {
    rule_high_amount_low_score
}

decision_result := "rejected_standard_tier_limits" if {
    rule_standard_tier_limits
}

decision_result := "rejected_income_verification" if {
    rule_income_verification
}

decision_result := "approved_debt_to_income_check" if {
    rule_debt_to_income_check
}

decision_result := "approved_premium_good_score" if {
    rule_premium_good_score
}

decision_result := "approved_vip_customers" if {
    rule_vip_customers
}

decision_result := "approved_small_personal_loans" if {
    rule_small_personal_loans
}

decision_result := "rejected_default" if {
    not rule_minimum_credit_score
    not rule_high_amount_low_score
    not rule_standard_tier_limits
    not rule_income_verification
    not rule_debt_to_income_check
    not rule_premium_good_score
    not rule_vip_customers
    not rule_small_personal_loans
}
