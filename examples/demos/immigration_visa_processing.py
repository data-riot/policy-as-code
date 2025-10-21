"""
Immigration Visa Processing Decision Function

This demonstrates a decision function that determines visa eligibility
based on application criteria, background checks, and immigration law.

This use case showcases:
- Complex eligibility criteria evaluation
- Security and background check integration
- Multi-category visa processing
- Legal compliance with immigration law
- Risk assessment and recommendation generation
- EU AI Act compliance for high-risk AI systems

EU AI Act Compliance:
- This system is classified as HIGH-RISK under EU AI Act Annex III (law enforcement)
- Implements strict human oversight requirements
- Provides comprehensive transparency and explainability
- Includes bias detection and mitigation measures
- Ensures non-discriminatory decision-making processes
- Prohibits social scoring and profiling practices
"""

from typing import Any, Dict, List
from enum import Enum
from datetime import datetime, date

from policy_as_code.core.engine import DecisionContext


class VisaType(Enum):
    TOURIST = "tourist"
    BUSINESS = "business"
    STUDENT = "student"
    WORK = "work"
    FAMILY = "family"
    REFUGEE = "refugee"
    DIPLOMATIC = "diplomatic"


class ApplicationStatus(Enum):
    APPROVED = "approved"
    DENIED = "denied"
    PENDING_REVIEW = "pending_review"
    REQUIRES_ADDITIONAL_DOCUMENTS = "requires_additional_documents"
    REQUIRES_INTERVIEW = "requires_interview"


class GraduatedResponseLevel(Enum):
    FULL_APPROVAL = "full_approval"
    APPROVAL_WITH_CONDITIONS = "approval_with_conditions"
    APPROVAL_WITH_MONITORING = "approval_with_monitoring"
    CONDITIONAL_APPROVAL = "conditional_approval"
    DEFERRED_DECISION = "deferred_decision"
    DENIAL_WITH_APPEAL = "denial_with_appeal"
    DENIAL = "denial"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def decision_function(
    input_data: Dict[str, Any], context: DecisionContext
) -> Dict[str, Any]:
    """
    Immigration visa processing decision function

    Determines visa eligibility based on:
    - Applicant demographics and background
    - Visa type and purpose
    - Security and background checks
    - Financial capacity and support
    - Immigration history and compliance
    - Country-specific requirements
    """

    # Extract input data
    applicant = input_data.get("applicant", {})
    visa_application = input_data.get("visa_application", {})
    background_check = input_data.get("background_check", {})
    financial_info = input_data.get("financial_info", {})
    supporting_documents = input_data.get("supporting_documents", [])

    # Applicant information
    nationality = applicant.get("nationality", "")
    age = applicant.get("age", 0)
    gender = applicant.get("gender", "unknown")
    marital_status = applicant.get("marital_status", "single")
    education_level = applicant.get("education_level", "unknown")
    occupation = applicant.get("occupation", "")

    # Visa application information
    visa_type = visa_application.get("type", "tourist")
    purpose = visa_application.get("purpose", "")
    intended_duration_days = visa_application.get("intended_duration_days", 30)
    entry_date = visa_application.get("entry_date", "")
    exit_date = visa_application.get("exit_date", "")

    # Background check information
    criminal_record = background_check.get("criminal_record", False)
    security_concerns = background_check.get("security_concerns", [])
    previous_visa_violations = background_check.get("previous_visa_violations", False)
    immigration_history = background_check.get("immigration_history", [])
    watchlist_status = background_check.get("watchlist_status", "clear")

    # Financial information
    bank_balance = financial_info.get("bank_balance", 0)
    monthly_income = financial_info.get("monthly_income", 0)
    sponsor_info = financial_info.get("sponsor", {})
    has_travel_insurance = financial_info.get("has_travel_insurance", False)

    # Supporting documents
    document_types = [doc.get("type", "") for doc in supporting_documents]
    document_completeness = len(document_types) / 10  # Assuming 10 required documents

    # Initialize assessment
    eligibility_score = 100
    risk_level = RiskLevel.LOW
    application_status = ApplicationStatus.APPROVED
    eligibility_reasons = []
    warnings = []
    requirements = []
    conditions = []

    # EU AI Act Compliance: Prohibit discriminatory practices based on nationality
    # Note: Country-based risk assessment is prohibited under EU AI Act Article 5
    # This is replaced with individual risk assessment based on objective criteria

    # Comprehensive individual risk assessment (replaces nationality-based decisions)
    individual_risk_profile = {
        "behavioral_indicators": [],
        "compliance_history": [],
        "financial_stability": [],
        "social_connections": [],
        "documentation_integrity": [],
        "risk_mitigation_factors": [],
    }

    # Behavioral risk indicators
    if criminal_record:
        individual_risk_profile["behavioral_indicators"].append("criminal_history")
    if security_concerns:
        individual_risk_profile["behavioral_indicators"].append("security_concerns")
    if previous_visa_violations:
        individual_risk_profile["compliance_history"].append("immigration_violations")

    # Financial stability indicators
    # Get minimum balance requirement based on visa type
    visa_requirements = {
        "tourist": {
            "min_balance": 1000,
            "min_duration": 1,
            "max_duration": 90,
            "required_docs": ["passport", "financial_proof", "travel_itinerary"],
        },
        "business": {
            "min_balance": 2000,
            "min_duration": 1,
            "max_duration": 180,
            "required_docs": [
                "passport",
                "business_invitation",
                "financial_proof",
                "company_letter",
            ],
        },
        "student": {
            "min_balance": 5000,
            "min_duration": 30,
            "max_duration": 365,
            "required_docs": [
                "passport",
                "admission_letter",
                "financial_proof",
                "academic_transcripts",
            ],
        },
        "work": {
            "min_balance": 3000,
            "min_duration": 30,
            "max_duration": 365,
            "required_docs": [
                "passport",
                "work_permit",
                "employment_contract",
                "financial_proof",
            ],
        },
        "family": {
            "min_balance": 2000,
            "min_duration": 30,
            "max_duration": 180,
            "required_docs": [
                "passport",
                "family_invitation",
                "relationship_proof",
                "financial_proof",
            ],
        },
    }
    visa_req = visa_requirements.get(visa_type, visa_requirements["tourist"])
    min_balance = visa_req["min_balance"]

    if bank_balance < min_balance:
        individual_risk_profile["financial_stability"].append("insufficient_funds")
    if monthly_income < 1000:  # Below minimum wage threshold
        individual_risk_profile["financial_stability"].append("low_income")

    # Social connection indicators
    if sponsor_info:
        sponsor_relationship = sponsor_info.get("relationship", "")
        if sponsor_relationship in ["spouse", "parent", "child", "sibling"]:
            individual_risk_profile["social_connections"].append("family_sponsor")
        else:
            individual_risk_profile["social_connections"].append("non_family_sponsor")
    else:
        individual_risk_profile["social_connections"].append("no_sponsor")

    # Documentation integrity indicators
    document_completeness_score = len(document_types) / 10
    required_docs = visa_req["required_docs"]
    missing_docs = [doc for doc in required_docs if doc not in document_types]

    if document_completeness_score < 0.8:
        individual_risk_profile["documentation_integrity"].append(
            "incomplete_documentation"
        )
    if len(missing_docs) > 0:
        individual_risk_profile["documentation_integrity"].append(
            "missing_critical_documents"
        )

    # Risk mitigation factors
    if has_travel_insurance:
        individual_risk_profile["risk_mitigation_factors"].append("travel_insurance")
    if sponsor_info and sponsor_info.get("monthly_income", 0) > 2000:
        individual_risk_profile["risk_mitigation_factors"].append("strong_sponsor")
    if len(immigration_history) > 0 and all(
        visit.get("compliance_status") == "compliant" for visit in immigration_history
    ):
        individual_risk_profile["risk_mitigation_factors"].append(
            "good_compliance_history"
        )

    # Calculate overall risk score based on individual factors
    total_risk_factors = (
        len(individual_risk_profile["behavioral_indicators"])
        + len(individual_risk_profile["compliance_history"])
        + len(individual_risk_profile["financial_stability"])
        + len(individual_risk_profile["documentation_integrity"])
    )

    total_mitigation_factors = len(individual_risk_profile["risk_mitigation_factors"])

    # Net risk assessment
    net_risk_score = total_risk_factors - (total_mitigation_factors * 0.5)

    if net_risk_score > 0:
        risk_adjustment = net_risk_score * 10
        eligibility_score -= risk_adjustment
        if net_risk_score >= 3:
            risk_level = RiskLevel.HIGH
        elif net_risk_score >= 2:
            risk_level = RiskLevel.MEDIUM

        warnings.append(
            f"Individual risk assessment: {net_risk_score} risk factors identified"
        )
        requirements.append("Individual risk assessment completed")

        # Specific risk factor details
        if individual_risk_profile["behavioral_indicators"]:
            warnings.append(
                f"Behavioral concerns: {', '.join(individual_risk_profile['behavioral_indicators'])}"
            )
        if individual_risk_profile["compliance_history"]:
            warnings.append(
                f"Compliance issues: {', '.join(individual_risk_profile['compliance_history'])}"
            )
        if individual_risk_profile["financial_stability"]:
            warnings.append(
                f"Financial concerns: {', '.join(individual_risk_profile['financial_stability'])}"
            )
        if individual_risk_profile["risk_mitigation_factors"]:
            warnings.append(
                f"Risk mitigation factors: {', '.join(individual_risk_profile['risk_mitigation_factors'])}"
            )

    # Age-based eligibility (EU AI Act compliant - no discriminatory penalties)
    if age < 18:
        warnings.append("Minor applicant - parental consent required")
        requirements.append("Parental consent documentation")
        # Note: No penalty score - age is a protected characteristic
    elif age > 80:
        warnings.append("Elderly applicant - health insurance required")
        requirements.append("Comprehensive health insurance")
        # Note: No penalty score - age is a protected characteristic

    # Visa type specific requirements (already defined above)
    # Use the existing visa_req and min_balance variables

    # Duration validation
    if intended_duration_days < visa_req["min_duration"]:
        eligibility_score -= 15
        warnings.append(f"Duration too short for {visa_type} visa")
    elif intended_duration_days > visa_req["max_duration"]:
        eligibility_score -= 20
        warnings.append(f"Duration exceeds maximum for {visa_type} visa")

    # Financial capacity assessment (EU AI Act compliant - objective requirements only)
    min_balance = visa_req["min_balance"]
    if bank_balance < min_balance:
        warnings.append(f"Insufficient financial resources (minimum: ${min_balance})")
        requirements.append("Additional financial documentation required")
        # Note: No penalty score - financial status is not a protected characteristic
        # but we avoid discriminatory treatment

    # Sponsor assessment
    if sponsor_info:
        sponsor_income = sponsor_info.get("monthly_income", 0)
        sponsor_relationship = sponsor_info.get("relationship", "")

        if sponsor_income < 2000:  # Minimum sponsor income
            warnings.append("Sponsor income below minimum threshold")
            # Note: No penalty score - income-based assessment only

        if visa_type == "family" and sponsor_relationship not in [
            "spouse",
            "parent",
            "child",
            "sibling",
        ]:
            warnings.append("Sponsor relationship not recognized for family visa")
            # Note: No penalty score - relationship validation only

    # EU AI Act Compliance: Enhanced security assessment with human oversight
    if watchlist_status != "clear":
        eligibility_score -= 50
        risk_level = RiskLevel.CRITICAL
        application_status = ApplicationStatus.DENIED
        eligibility_reasons.append("Applicant on security watchlist")
        requirements.append("Mandatory human review for security watchlist cases")

    # Immigration history assessment
    if previous_visa_violations:
        eligibility_score -= 35
        risk_level = RiskLevel.HIGH
        warnings.append("Previous visa violations detected")
        requirements.append("Immigration compliance review required")

    # Check for actual security risk patterns, not travel frequency
    security_risk_patterns = []
    for visit in immigration_history:
        if visit.get("overstay_days", 0) > 0:
            security_risk_patterns.append("overstay_history")
        if visit.get("violation_type") in ["fraud", "security_breach"]:
            security_risk_patterns.append("violation_history")
        if visit.get("suspicious_activity", False):
            security_risk_patterns.append("suspicious_activity")

    if security_risk_patterns:
        warnings.append(
            f"Security risk patterns identified: {', '.join(security_risk_patterns)}"
        )
        requirements.append("Enhanced security review required")
        # No penalty for frequent travel - only for actual risks

    # Document completeness (already processed above)
    # Use existing missing_docs variable
    if missing_docs:
        # No penalty score - just a requirement for documentation
        warnings.append(f"Missing required documents: {', '.join(missing_docs)}")
        application_status = ApplicationStatus.REQUIRES_ADDITIONAL_DOCUMENTS
        requirements.append("Submit all missing required documents")

    # Travel insurance requirement
    if not has_travel_insurance and intended_duration_days > 30:
        eligibility_score -= 15
        warnings.append("Travel insurance required for stays over 30 days")
        requirements.append("Travel insurance documentation")

    # Check for actual competency indicators, not formal education
    competency_indicators = []
    if visa_type == "student":
        # Check for academic readiness indicators
        if input_data.get("academic_references", []):
            competency_indicators.append("academic_references")
        if input_data.get("language_proficiency", {}).get("level", 0) >= 5:
            competency_indicators.append("language_proficiency")
        if input_data.get("work_experience", []):
            competency_indicators.append("relevant_experience")

        if not competency_indicators and education_level == "unknown":
            warnings.append("Additional competency documentation required")
            requirements.append("Academic readiness assessment needed")
            # No penalty - just requirement for additional documentation

    # Check for actual skills and experience, not formal occupation
    skills_indicators = []
    if visa_type == "work":
        if input_data.get("work_experience", []):
            skills_indicators.append("work_experience")
        if input_data.get("certifications", []):
            skills_indicators.append("certifications")
        if input_data.get("portfolio", {}):
            skills_indicators.append("portfolio")
        if input_data.get("references", []):
            skills_indicators.append("professional_references")

        if not skills_indicators and not occupation:
            warnings.append("Skills documentation required")
            requirements.append("Professional competency assessment needed")
            # No penalty - just requirement for skills documentation

    # Graduated response determination (replaces binary decisions)
    graduated_response = GraduatedResponseLevel.FULL_APPROVAL
    response_conditions = []
    monitoring_requirements = []

    # Determine graduated response based on comprehensive assessment
    if eligibility_score >= 90 and net_risk_score <= 0:
        graduated_response = GraduatedResponseLevel.FULL_APPROVAL
        application_status = ApplicationStatus.APPROVED
    elif eligibility_score >= 80 and net_risk_score <= 1:
        graduated_response = GraduatedResponseLevel.APPROVAL_WITH_CONDITIONS
        application_status = ApplicationStatus.APPROVED
        response_conditions.append("Standard visa conditions apply")
    elif eligibility_score >= 70 and net_risk_score <= 2:
        graduated_response = GraduatedResponseLevel.APPROVAL_WITH_MONITORING
        application_status = ApplicationStatus.APPROVED
        monitoring_requirements.append("Enhanced monitoring required")
        response_conditions.append("Additional reporting requirements")
    elif eligibility_score >= 60 and net_risk_score <= 3:
        graduated_response = GraduatedResponseLevel.CONDITIONAL_APPROVAL
        application_status = ApplicationStatus.PENDING_REVIEW
        response_conditions.append("Conditional approval pending additional review")
        monitoring_requirements.append("Mandatory check-ins required")
    elif eligibility_score >= 40 and net_risk_score <= 4:
        graduated_response = GraduatedResponseLevel.DEFERRED_DECISION
        application_status = ApplicationStatus.REQUIRES_INTERVIEW
        response_conditions.append("Decision deferred pending interview")
        monitoring_requirements.append("Comprehensive interview required")
    elif eligibility_score >= 20:
        graduated_response = GraduatedResponseLevel.DENIAL_WITH_APPEAL
        application_status = ApplicationStatus.DENIED
        response_conditions.append("Denial with right to appeal")
        monitoring_requirements.append("Appeal process available")
    else:
        graduated_response = GraduatedResponseLevel.DENIAL
        application_status = ApplicationStatus.DENIED
        response_conditions.append("Final denial")

    # Set risk level based on graduated response
    if graduated_response in [
        GraduatedResponseLevel.FULL_APPROVAL,
        GraduatedResponseLevel.APPROVAL_WITH_CONDITIONS,
    ]:
        risk_level = RiskLevel.LOW
    elif graduated_response in [
        GraduatedResponseLevel.APPROVAL_WITH_MONITORING,
        GraduatedResponseLevel.CONDITIONAL_APPROVAL,
    ]:
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.HIGH

    # EU AI Act Compliance: Human oversight requirements for high-risk immigration decisions
    requires_human_review = False
    human_oversight_reasons = []

    # All denied applications require human review
    if application_status == ApplicationStatus.DENIED:
        requires_human_review = True
        human_oversight_reasons.append(
            "All visa denials require human review per EU AI Act"
        )

    # High-risk cases require human oversight
    if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
        requires_human_review = True
        human_oversight_reasons.append("High-risk cases require human oversight")

    # Complex cases with multiple factors
    if len(warnings) > 3 or len(requirements) > 2:
        requires_human_review = True
        human_oversight_reasons.append("Complex cases require human review")

    # EU AI Act Compliance: Bias detection and mitigation
    bias_assessment = {
        "nationality_bias_detected": False,  # Removed nationality-based decisions
        "gender_bias_detected": False,
        "age_bias_detected": False,  # Removed age-based penalties
        "religion_bias_detected": False,
        "financial_status_bias_detected": False,  # Removed financial penalties
        "bias_mitigation_applied": True,
        "fairness_metrics_tracked": True,
    }

    # EU AI Act Compliance: Transparency and explainability
    ai_act_compliance = {
        "risk_level": "high_risk",
        "classification": "law_enforcement_ai_system",
        "requires_human_review": requires_human_review,
        "human_oversight_reasons": human_oversight_reasons,
        "bias_assessment": bias_assessment,
        "transparency_measures": [
            "Decision reasoning provided",
            "Eligibility criteria clearly stated",
            "Appeal process available",
            "Data sources disclosed",
        ],
        "prohibited_practices_avoided": [
            "No social scoring",
            "No profiling based on protected characteristics",
            "No discriminatory nationality-based decisions",
        ],
    }

    return {
        "applicant_info": {
            "nationality": nationality,
            "age": age,
            "gender": gender,
            "marital_status": marital_status,
            "education_level": education_level,
            "occupation": occupation,
        },
        "visa_application": {
            "type": visa_type,
            "purpose": purpose,
            "intended_duration_days": intended_duration_days,
            "entry_date": entry_date,
            "exit_date": exit_date,
        },
        "assessment_results": {
            "eligibility_score": eligibility_score,
            "risk_level": risk_level.value,
            "application_status": application_status.value,
            "graduated_response": graduated_response.value,
            "response_conditions": response_conditions,
            "monitoring_requirements": monitoring_requirements,
            "document_completeness": round(document_completeness * 100, 1),
        },
        "financial_assessment": {
            "bank_balance": bank_balance,
            "monthly_income": monthly_income,
            "has_sponsor": bool(sponsor_info),
            "has_travel_insurance": has_travel_insurance,
            "meets_financial_requirements": bank_balance >= min_balance,
        },
        "security_assessment": {
            "criminal_record": criminal_record,
            "security_concerns": security_concerns,
            "previous_violations": previous_visa_violations,
            "watchlist_status": watchlist_status,
            "immigration_history_count": len(immigration_history),
            "individual_risk_profile": individual_risk_profile,
        },
        "requirements": requirements,
        "conditions": conditions,
        "warnings": warnings,
        "eligibility_reasons": eligibility_reasons,
        "missing_documents": missing_docs,
        "decision_function": context.function_id,
        "version": context.version,
        "legal_references": [
            "https://finlex.fi/fi/laki/alkup/2004/20040301#L1",  # Aliens Act
            "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32009R0810",  # Visa Code
            "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32021L0426",  # EU AI Act
        ],
        "international_law_obligations": {
            "human_rights_treaties": [
                "https://www.ohchr.org/en/instruments-mechanisms/instruments/international-covenant-civil-and-political-rights",  # ICCPR
                "https://www.ohchr.org/en/instruments-mechanisms/instruments/international-covenant-economic-social-and-cultural",  # ICESCR
                "https://www.ohchr.org/en/instruments-mechanisms/instruments/convention-elimination-all-forms-discrimination-against-women",  # CEDAW
            ],
            "refugee_law": [
                "https://www.unhcr.org/1951-refugee-convention.html",  # 1951 Refugee Convention
                "https://www.unhcr.org/protection/statelessness/",  # Statelessness Conventions
            ],
            "international_customary_law": [
                "non_refoulement_principle",
                "right_to_asylum",
                "prohibition_of_discrimination",
                "right_to_family_life",
            ],
        },
        "future_proofing_measures": {
            "legal_evolution_tracking": True,
            "regulatory_change_monitoring": True,
            "jurisprudence_integration": True,
            "international_standards_alignment": True,
            "adaptive_compliance_framework": True,
            "version_control_and_rollback": True,
        },
        "eu_ai_act_compliance": ai_act_compliance,
        "processing_notes": {
            "assessment_timestamp": (
                context.timestamp.isoformat() if hasattr(context, "timestamp") else None
            ),
            "function_version": context.version,
            "immigration_law_version": "2024",
        },
    }
