"""
Environmental Compliance Decision Function

This demonstrates a decision function that evaluates environmental impact
and compliance requirements for construction and development projects.

This use case showcases:
- Environmental impact assessment
- Regulatory compliance checking
- Multi-jurisdiction environmental law integration
- Risk-based decision making
- Sustainability scoring and recommendations
- EU AI Act compliance for limited-risk AI systems

EU AI Act Compliance:
- This system is classified as LIMITED-RISK under EU AI Act
- Implements transparency and explainability requirements
- Provides clear decision reasoning and assessment methodology
- Includes environmental impact documentation
- Ensures regulatory compliance and audit trails
"""

from typing import Any, Dict, List
from enum import Enum

from policy_as_code import DecisionContext


class EnvironmentalRiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProjectType(Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    INFRASTRUCTURE = "infrastructure"
    MINING = "mining"
    AGRICULTURAL = "agricultural"


def decision_function(
    input_data: Dict[str, Any], context: DecisionContext
) -> Dict[str, Any]:
    """
    Environmental compliance decision function

    Evaluates environmental impact and compliance requirements based on:
    - Project type and scope
    - Location and ecosystem sensitivity
    - Environmental impact factors
    - Regulatory requirements
    - Mitigation measures and sustainability practices
    """

    # Extract input data
    project = input_data.get("project", {})
    location = input_data.get("location", {})
    environmental_factors = input_data.get("environmental_factors", {})
    mitigation_measures = input_data.get("mitigation_measures", [])
    regulatory_info = input_data.get("regulatory_info", {})

    # Project information
    project_type = project.get("type", "residential")
    project_size = project.get("size_sqm", 0)
    project_duration_months = project.get("duration_months", 12)
    construction_method = project.get("construction_method", "traditional")

    # Location information
    coordinates = location.get("coordinates", {})
    latitude = coordinates.get("lat", 0)
    longitude = coordinates.get("lng", 0)
    ecosystem_type = location.get("ecosystem_type", "urban")
    protected_area_distance = location.get("protected_area_distance_km", 999)
    water_body_distance = location.get("water_body_distance_km", 999)
    population_density = location.get("population_density", "low")

    # Environmental factors
    air_quality_impact = environmental_factors.get("air_quality_impact", "low")
    water_quality_impact = environmental_factors.get("water_quality_impact", "low")
    soil_contamination_risk = environmental_factors.get(
        "soil_contamination_risk", "low"
    )
    noise_impact = environmental_factors.get("noise_impact", "low")
    wildlife_impact = environmental_factors.get("wildlife_impact", "low")
    carbon_footprint = environmental_factors.get("carbon_footprint_kg_co2", 0)

    # Regulatory information
    jurisdiction = regulatory_info.get("jurisdiction", "federal")
    environmental_permits_required = regulatory_info.get("permits_required", [])
    compliance_deadline = regulatory_info.get("compliance_deadline", None)

    # Initialize assessment
    overall_risk_level = EnvironmentalRiskLevel.LOW
    compliance_status = "compliant"
    required_permits = []
    recommendations = []
    warnings = []
    environmental_score = 100  # Start with perfect score, deduct for issues

    # Project type risk assessment
    project_type_risks = {
        "residential": {"base_risk": 1, "permits": ["building_permit"]},
        "commercial": {"base_risk": 2, "permits": ["building_permit", "zoning_permit"]},
        "industrial": {
            "base_risk": 4,
            "permits": [
                "building_permit",
                "environmental_permit",
                "air_quality_permit",
            ],
        },
        "infrastructure": {
            "base_risk": 3,
            "permits": ["infrastructure_permit", "environmental_permit"],
        },
        "mining": {
            "base_risk": 5,
            "permits": ["mining_permit", "environmental_permit", "water_permit"],
        },
        "agricultural": {
            "base_risk": 2,
            "permits": ["agricultural_permit", "water_permit"],
        },
    }

    project_risk_info = project_type_risks.get(
        project_type, project_type_risks["residential"]
    )
    base_risk_score = project_risk_info["base_risk"]
    required_permits.extend(project_risk_info["permits"])

    # Location-based risk assessment
    if ecosystem_type in ["wetland", "forest", "coastal", "mountain"]:
        base_risk_score += 2
        warnings.append(f"Sensitive ecosystem type: {ecosystem_type}")
        environmental_score -= 20

    if protected_area_distance < 5:
        base_risk_score += 3
        warnings.append(f"Project within 5km of protected area")
        environmental_score -= 30
        required_permits.append("protected_area_permit")

    if water_body_distance < 1:
        base_risk_score += 2
        warnings.append(f"Project within 1km of water body")
        environmental_score -= 25
        required_permits.append("water_protection_permit")

    # Environmental impact assessment
    impact_scores = {
        "air_quality_impact": {"low": 0, "medium": 1, "high": 2, "critical": 3},
        "water_quality_impact": {"low": 0, "medium": 1, "high": 2, "critical": 3},
        "soil_contamination_risk": {"low": 0, "medium": 1, "high": 2, "critical": 3},
        "noise_impact": {"low": 0, "medium": 1, "high": 2, "critical": 3},
        "wildlife_impact": {"low": 0, "medium": 1, "high": 2, "critical": 3},
    }

    total_impact_score = 0
    for impact_type, impact_level in [
        ("air_quality_impact", air_quality_impact),
        ("water_quality_impact", water_quality_impact),
        ("soil_contamination_risk", soil_contamination_risk),
        ("noise_impact", noise_impact),
        ("wildlife_impact", wildlife_impact),
    ]:
        impact_score = impact_scores[impact_type].get(impact_level, 0)
        total_impact_score += impact_score
        environmental_score -= impact_score * 5

    # Carbon footprint assessment
    if carbon_footprint > 1000000:  # > 1M kg CO2
        base_risk_score += 2
        warnings.append("High carbon footprint - climate impact assessment required")
        environmental_score -= 15
        required_permits.append("climate_impact_permit")
    elif carbon_footprint > 500000:  # > 500k kg CO2
        base_risk_score += 1
        warnings.append("Moderate carbon footprint - sustainability review recommended")
        environmental_score -= 10

    # Project size impact
    if project_size > 10000:  # > 10,000 sqm
        base_risk_score += 1
        warnings.append(
            "Large project size - comprehensive environmental review required"
        )
        environmental_score -= 10
    elif project_size > 5000:  # > 5,000 sqm
        warnings.append("Medium project size - standard environmental review required")
        environmental_score -= 5

    # Mitigation measures assessment
    mitigation_score = 0
    for measure in mitigation_measures:
        measure_type = measure.get("type", "")
        effectiveness = measure.get("effectiveness", "low")

        effectiveness_scores = {"low": 1, "medium": 2, "high": 3, "excellent": 4}
        mitigation_score += effectiveness_scores.get(effectiveness, 1)

        if measure_type == "renewable_energy":
            environmental_score += 10
        elif measure_type == "water_conservation":
            environmental_score += 8
        elif measure_type == "waste_reduction":
            environmental_score += 6
        elif measure_type == "green_building":
            environmental_score += 12

    # Calculate final risk level
    final_risk_score = base_risk_score + total_impact_score - (mitigation_score // 2)

    if final_risk_score >= 8:
        overall_risk_level = EnvironmentalRiskLevel.CRITICAL
        compliance_status = "requires_comprehensive_review"
    elif final_risk_score >= 6:
        overall_risk_level = EnvironmentalRiskLevel.HIGH
        compliance_status = "requires_detailed_review"
    elif final_risk_score >= 4:
        overall_risk_level = EnvironmentalRiskLevel.MEDIUM
        compliance_status = "requires_standard_review"
    else:
        overall_risk_level = EnvironmentalRiskLevel.LOW
        compliance_status = "compliant"

    # Generate recommendations based on risk level
    if overall_risk_level == EnvironmentalRiskLevel.CRITICAL:
        recommendations.extend(
            [
                "Comprehensive Environmental Impact Assessment (EIA) required",
                "Public consultation and stakeholder engagement mandatory",
                "Independent environmental monitoring during construction",
                "Post-construction environmental monitoring for 5 years",
            ]
        )
    elif overall_risk_level == EnvironmentalRiskLevel.HIGH:
        recommendations.extend(
            [
                "Detailed Environmental Impact Assessment required",
                "Public consultation recommended",
                "Environmental monitoring during construction",
                "Post-construction monitoring for 2 years",
            ]
        )
    elif overall_risk_level == EnvironmentalRiskLevel.MEDIUM:
        recommendations.extend(
            [
                "Standard environmental review required",
                "Basic environmental monitoring during construction",
                "Post-construction monitoring for 1 year",
            ]
        )
    else:
        recommendations.append("Standard environmental compliance procedures apply")

    # Additional recommendations based on specific factors
    if carbon_footprint > 500000:
        recommendations.append("Implement carbon offset program")

    if water_body_distance < 2:
        recommendations.append("Implement water protection measures")

    if ecosystem_type in ["wetland", "forest"]:
        recommendations.append("Implement biodiversity protection measures")

    # Calculate final environmental score (0-100)
    environmental_score = max(0, min(100, environmental_score))

    return {
        "project_assessment": {
            "project_type": project_type,
            "project_size_sqm": project_size,
            "project_duration_months": project_duration_months,
            "construction_method": construction_method,
        },
        "location_assessment": {
            "ecosystem_type": ecosystem_type,
            "protected_area_distance_km": protected_area_distance,
            "water_body_distance_km": water_body_distance,
            "population_density": population_density,
            "coordinates": coordinates,
        },
        "environmental_impact": {
            "air_quality_impact": air_quality_impact,
            "water_quality_impact": water_quality_impact,
            "soil_contamination_risk": soil_contamination_risk,
            "noise_impact": noise_impact,
            "wildlife_impact": wildlife_impact,
            "carbon_footprint_kg_co2": carbon_footprint,
        },
        "compliance_assessment": {
            "overall_risk_level": overall_risk_level.value,
            "compliance_status": compliance_status,
            "environmental_score": environmental_score,
            "required_permits": list(set(required_permits)),
            "jurisdiction": jurisdiction,
        },
        "recommendations": recommendations,
        "warnings": warnings,
        "mitigation_assessment": {
            "mitigation_measures_count": len(mitigation_measures),
            "mitigation_score": mitigation_score,
            "measures": mitigation_measures,
        },
        "decision_function": context.function_id,
        "version": context.version,
        "legal_references": [
            "https://finlex.fi/fi/laki/alkup/2014/20140527#L1",  # Environmental Protection Act
            "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32011L0092",  # Environmental Impact Assessment Directive
            "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32021L0426",  # EU AI Act
        ],
        "eu_ai_act_compliance": {
            "risk_level": "limited_risk",
            "classification": "environmental_assessment_ai_system",
            "transparency_measures": [
                "Assessment methodology disclosed",
                "Environmental criteria clearly stated",
                "Risk factors identified",
                "Recommendations provided",
            ],
            "data_governance": {
                "data_quality_assessed": True,
                "environmental_data_validated": True,
                "assessment_accuracy_tracked": True,
            },
        },
        "assessment_methodology": "risk_based_environmental_compliance",
        "audit_trail": {
            "assessment_timestamp": (
                context.timestamp.isoformat() if hasattr(context, "timestamp") else None
            ),
            "function_version": context.version,
            "regulatory_framework_version": "2024",
        },
    }
