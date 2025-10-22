package org.policy_as_code.loan_approval.v1

# Metadata block - required for all Rego files
# owner: Data Governance Team
# version: 1.0
# description: Test cases for loan approval policy
# created_date: 2025-08-01
# last_updated: 2025-08-01
# tags: ["test", "loan", "approval"]
# business_owner: Credit Risk Team
# compliance_required: true
# audit_trail: true

# Test cases for loan approval policy

# Test 1: Minimum credit score - negative case
test_minimum_credit_score_negative if {
    test_input := {
        "amount": 1000,
        "customer_score": 400,
        "customer_tier": "standard",
        "employment_status": "employed",
        "monthly_income": 3000,
        "loan_purpose": "personal"
    }

    # Should trigger minimum credit score rule
    rule_minimum_credit_score with input as test_input
    not allow with input as test_input
    not approved with input as test_input
}

# Test 2: High amount low score - negative case
test_high_amount_low_score_negative if {
    test_input := {
        "amount": 15000,
        "customer_score": 600,
        "customer_tier": "standard",
        "employment_status": "employed",
        "monthly_income": 5000,
        "loan_purpose": "personal"
    }

    # Should trigger high amount low score rule
    rule_high_amount_low_score with input as test_input
    not allow with input as test_input
}

# Test 3: VIP customers - positive case
test_vip_customers_positive if {
    test_input := {
        "amount": 50000,
        "customer_score": 700,
        "customer_tier": "vip",
        "employment_status": "employed",
        "monthly_income": 10000,
        "loan_purpose": "personal"
    }

    # Should trigger VIP customers rule and approve
    rule_vip_customers with input as test_input
    allow with input as test_input
    approved with input as test_input
}

# Test 4: Small personal loans - positive case
test_small_personal_loans_positive if {
    test_input := {
        "amount": 3000,
        "customer_score": 650,
        "customer_tier": "standard",
        "employment_status": "employed",
        "monthly_income": 4000,
        "loan_purpose": "personal"
    }

    # Should trigger small personal loans rule and approve
    rule_small_personal_loans with input as test_input
    allow with input as test_input
    approved with input as test_input
}

# Test 5: Default deny - missing required fields
test_default_deny_missing_fields if {
    test_input := {
        "amount": null,
        "customer_score": 650,
        "customer_tier": "standard",
        "employment_status": "employed",
        "monthly_income": 4000,
        "loan_purpose": "personal"
    }

    # Should not allow due to missing required fields
    not input_valid with input as test_input
    not allow with input as test_input
    not approved with input as test_input
}

# Test 6: Input validation
test_input_validation if {
    test_input := {
        "amount": 1000,
        "customer_score": 650,
        "customer_tier": "standard",
        "employment_status": "employed",
        "monthly_income": 4000,
        "loan_purpose": "personal"
    }

    # Check input validation
    input_valid with input as test_input
}

# Test 7: Standard tier limits - negative case
test_standard_tier_limits_negative if {
    test_input := {
        "amount": 8000,
        "customer_score": 650,
        "customer_tier": "standard",
        "employment_status": "employed",
        "monthly_income": 4000,
        "loan_purpose": "personal"
    }

    # Should trigger standard tier limits rule
    rule_standard_tier_limits with input as test_input
    deny with input as test_input
    not allow with input as test_input
}

# Test 8: Income verification - negative case
test_income_verification_negative if {
    test_input := {
        "amount": 8000,
        "customer_score": 650,
        "customer_tier": "standard",
        "employment_status": "employed",
        "monthly_income": null,
        "loan_purpose": "personal"
    }

    # Should trigger income verification rule
    rule_income_verification with input as test_input
    deny with input as test_input
    not allow with input as test_input
}

# Test 9: Debt-to-income check - positive case
test_debt_to_income_check_positive if {
    test_input := {
        "amount": 15000,
        "customer_score": 700,
        "customer_tier": "premium",
        "employment_status": "employed",
        "monthly_income": 6000,
        "loan_purpose": "personal"
    }

    # Should trigger debt-to-income check rule and approve
    rule_debt_to_income_check with input as test_input
    allow with input as test_input
    approved with input as test_input
}

# Test 10: Premium good score - positive case
test_premium_good_score_positive if {
    test_input := {
        "amount": 30000,
        "customer_score": 750,
        "customer_tier": "premium",
        "employment_status": "employed",
        "monthly_income": 8000,
        "loan_purpose": "personal"
    }

    # Should trigger premium good score rule and approve
    rule_premium_good_score with input as test_input
    allow with input as test_input
    approved with input as test_input
}

# Test 11: Decision result structure
test_decision_result_structure if {
    test_input := {
        "amount": 1000,
        "customer_score": 400,
        "customer_tier": "standard",
        "employment_status": "employed",
        "monthly_income": 3000,
        "loan_purpose": "personal"
    }

    result := decision_result with input as test_input

    # Check result structure
    result == "rejected_minimum_credit_score"
}

# Test 12: Boundary conditions
test_boundary_conditions if {
    test_input := {
        "amount": 5000,
        "customer_score": 499,
        "customer_tier": "standard",
        "employment_status": "employed",
        "monthly_income": 4000,
        "loan_purpose": "personal"
    }

    # Test boundary conditions - minimum credit score rule should trigger
    rule_minimum_credit_score with input as test_input
    deny with input as test_input
    not allow with input as test_input
}
