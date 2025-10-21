"""
Formal DSL Grammar with Conflict Detection
Production-grade rule DSL with priorities, static analysis, and conflict detection
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class RuleType(str, Enum):
    """Types of rules in the DSL"""

    CONDITION = "condition"  # if-then rules
    THRESHOLD = "threshold"  # threshold comparisons
    RANGE = "range"  # range checks
    ENUM_MATCH = "enum_match"  # enum value matching
    REGEX = "regex"  # regex pattern matching
    CUSTOM = "custom"  # custom rule logic


class Operator(str, Enum):
    """Comparison operators"""

    EQ = "=="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX = "regex"
    NOT_REGEX = "not_regex"


class ConflictType(str, Enum):
    """Types of rule conflicts"""

    OVERLAPPING_CONDITIONS = "overlapping_conditions"
    AMBIGUOUS_PRIORITY = "ambiguous_priority"
    UNREACHABLE_RULE = "unreachable_rule"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    TYPE_MISMATCH = "type_mismatch"
    MISSING_FIELD = "missing_field"


@dataclass(frozen=True)
class RuleCondition:
    """A condition in a rule"""

    field_name: str
    operator: Operator
    value: Any
    negated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "field": self.field_name,
            "operator": self.operator.value,
            "value": self.value,
            "negated": self.negated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuleCondition":
        """Create from dictionary"""
        return cls(
            field_name=data["field"],
            operator=Operator(data["operator"]),
            value=data["value"],
            negated=data.get("negated", False),
        )


@dataclass(frozen=True)
class RuleAction:
    """An action to take when a rule matches"""

    action_type: str
    field_name: str
    value: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "action_type": self.action_type,
            "field": self.field_name,
            "value": self.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuleAction":
        """Create from dictionary"""
        return cls(
            action_type=data["action_type"],
            field_name=data["field"],
            value=data["value"],
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class DSLRule:
    """A rule in the DSL"""

    rule_id: str
    rule_type: RuleType
    priority: int
    conditions: List[RuleCondition]
    actions: List[RuleAction]
    description: str
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type.value,
            "priority": self.priority,
            "conditions": [c.to_dict() for c in self.conditions],
            "actions": [a.to_dict() for a in self.actions],
            "description": self.description,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DSLRule":
        """Create from dictionary"""
        return cls(
            rule_id=data["rule_id"],
            rule_type=RuleType(data["rule_type"]),
            priority=data["priority"],
            conditions=[RuleCondition.from_dict(c) for c in data["conditions"]],
            actions=[RuleAction.from_dict(a) for a in data["actions"]],
            description=data["description"],
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class RuleConflict:
    """A conflict between rules"""

    conflict_type: ConflictType
    rule_ids: List[str]
    message: str
    severity: str = "error"  # error, warning, info
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "conflict_type": self.conflict_type.value,
            "rule_ids": self.rule_ids,
            "message": self.message,
            "severity": self.severity,
            "details": self.details,
        }


@dataclass(frozen=True)
class DSLSchema:
    """Schema for the DSL"""

    name: str
    version: str
    rules: List[DSLRule]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "version": self.version,
            "rules": [rule.to_dict() for rule in self.rules],
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DSLSchema":
        """Create from dictionary"""
        return cls(
            name=data["name"],
            version=data["version"],
            rules=[DSLRule.from_dict(rule) for rule in data["rules"]],
            input_schema=data["input_schema"],
            output_schema=data["output_schema"],
            metadata=data.get("metadata", {}),
        )


class DSLGrammar:
    """Formal grammar for the DSL"""

    # Grammar rules (simplified EBNF)
    GRAMMAR = """
    DSL := Schema
    Schema := Name Version Rules InputSchema OutputSchema Metadata
    Name := String
    Version := String
    Rules := Rule+
    Rule := RuleId RuleType Priority Conditions Actions Description Enabled Metadata
    RuleId := String
    RuleType := "condition" | "threshold" | "range" | "enum_match" | "regex" | "custom"
    Priority := Integer
    Conditions := Condition+
    Condition := Field Operator Value Negated
    Field := String
    Operator := "==" | "!=" | "<" | "<=" | ">" | ">=" | "in" | "not_in" | "contains" | "not_contains" | "regex" | "not_regex"
    Value := String | Number | Boolean | Array | Object
    Negated := Boolean
    Actions := Action+
    Action := ActionType Field Value Metadata
    ActionType := "set" | "increment" | "decrement" | "append" | "remove"
    Description := String
    Enabled := Boolean
    Metadata := Object
    InputSchema := Object
    OutputSchema := Object
    """

    @staticmethod
    def validate_syntax(schema_data: Dict[str, Any]) -> List[str]:
        """Validate DSL syntax against grammar"""
        errors = []

        # Check required fields
        required_fields = ["name", "version", "rules", "input_schema", "output_schema"]
        for field in required_fields:
            if field not in schema_data:
                errors.append(f"Missing required field: {field}")

        # Validate rules
        if "rules" in schema_data:
            for i, rule in enumerate(schema_data["rules"]):
                rule_errors = DSLGrammar._validate_rule_syntax(rule, i)
                errors.extend(rule_errors)

        return errors

    @staticmethod
    def _validate_rule_syntax(rule: Dict[str, Any], index: int) -> List[str]:
        """Validate individual rule syntax"""
        errors = []

        # Check required rule fields
        required_rule_fields = [
            "rule_id",
            "rule_type",
            "priority",
            "conditions",
            "actions",
            "description",
        ]
        for field in required_rule_fields:
            if field not in rule:
                errors.append(f"Rule {index}: Missing required field: {field}")

        # Validate rule type
        if "rule_type" in rule:
            valid_types = [t.value for t in RuleType]
            if rule["rule_type"] not in valid_types:
                errors.append(f"Rule {index}: Invalid rule_type: {rule['rule_type']}")

        # Validate priority
        if "priority" in rule:
            if not isinstance(rule["priority"], int):
                errors.append(f"Rule {index}: Priority must be an integer")

        # Validate conditions
        if "conditions" in rule:
            for j, condition in enumerate(rule["conditions"]):
                condition_errors = DSLGrammar._validate_condition_syntax(
                    condition, index, j
                )
                errors.extend(condition_errors)

        # Validate actions
        if "actions" in rule:
            for j, action in enumerate(rule["actions"]):
                action_errors = DSLGrammar._validate_action_syntax(action, index, j)
                errors.extend(action_errors)

        return errors

    @staticmethod
    def _validate_condition_syntax(
        condition: Dict[str, Any], rule_index: int, condition_index: int
    ) -> List[str]:
        """Validate condition syntax"""
        errors = []

        required_fields = ["field", "operator", "value"]
        for field in required_fields:
            if field not in condition:
                errors.append(
                    f"Rule {rule_index}, Condition {condition_index}: Missing field: {field}"
                )

        # Validate operator
        if "operator" in condition:
            valid_operators = [op.value for op in Operator]
            if condition["operator"] not in valid_operators:
                errors.append(
                    f"Rule {rule_index}, Condition {condition_index}: Invalid operator: {condition['operator']}"
                )

        return errors

    @staticmethod
    def _validate_action_syntax(
        action: Dict[str, Any], rule_index: int, action_index: int
    ) -> List[str]:
        """Validate action syntax"""
        errors = []

        required_fields = ["action_type", "field", "value"]
        for field in required_fields:
            if field not in action:
                errors.append(
                    f"Rule {rule_index}, Action {action_index}: Missing field: {field}"
                )

        return errors


class RuleConflictDetector:
    """Detects conflicts between rules"""

    def __init__(self):
        self.conflicts: List[RuleConflict] = []

    def detect_conflicts(self, schema: DSLSchema) -> List[RuleConflict]:
        """Detect all conflicts in a schema"""
        self.conflicts = []

        # Sort rules by priority for analysis
        sorted_rules = sorted(schema.rules, key=lambda r: r.priority, reverse=True)

        # Detect different types of conflicts
        self._detect_overlapping_conditions(sorted_rules)
        self._detect_ambiguous_priorities(sorted_rules)
        self._detect_unreachable_rules(sorted_rules)
        self._detect_circular_dependencies(sorted_rules)
        self._detect_type_mismatches(sorted_rules, schema.input_schema)
        self._detect_missing_fields(sorted_rules, schema.input_schema)

        return self.conflicts.copy()

    def _detect_overlapping_conditions(self, rules: List[DSLRule]) -> None:
        """Detect rules with overlapping conditions"""
        for i, rule1 in enumerate(rules):
            for j, rule2 in enumerate(rules[i + 1 :], i + 1):
                if self._conditions_overlap(rule1.conditions, rule2.conditions):
                    conflict = RuleConflict(
                        conflict_type=ConflictType.OVERLAPPING_CONDITIONS,
                        rule_ids=[rule1.rule_id, rule2.rule_id],
                        message=f"Rules have overlapping conditions: {rule1.rule_id} and {rule2.rule_id}",
                        severity="warning",
                        details={
                            "rule1_conditions": [c.to_dict() for c in rule1.conditions],
                            "rule2_conditions": [c.to_dict() for c in rule2.conditions],
                        },
                    )
                    self.conflicts.append(conflict)

    def _detect_ambiguous_priorities(self, rules: List[DSLRule]) -> None:
        """Detect rules with ambiguous priorities"""
        priority_groups: Dict[int, List[DSLRule]] = {}
        for rule in rules:
            if rule.priority not in priority_groups:
                priority_groups[rule.priority] = []
            priority_groups[rule.priority].append(rule)

        for priority, group in priority_groups.items():
            if len(group) > 1:
                conflict = RuleConflict(
                    conflict_type=ConflictType.AMBIGUOUS_PRIORITY,
                    rule_ids=[rule.rule_id for rule in group],
                    message=f"Multiple rules have the same priority {priority}",
                    severity="error",
                    details={"priority": priority, "rule_count": len(group)},
                )
                self.conflicts.append(conflict)

    def _detect_unreachable_rules(self, rules: List[DSLRule]) -> None:
        """Detect unreachable rules"""
        # Rules with lower priority that are always shadowed by higher priority rules
        for i, rule in enumerate(rules):
            if i > 0:  # Skip first rule (highest priority)
                higher_priority_rules = rules[:i]
                if self._rule_is_shadowed(rule, higher_priority_rules):
                    conflict = RuleConflict(
                        conflict_type=ConflictType.UNREACHABLE_RULE,
                        rule_ids=[rule.rule_id],
                        message=f"Rule {rule.rule_id} is unreachable due to higher priority rules",
                        severity="warning",
                        details={
                            "shadowing_rules": [
                                r.rule_id for r in higher_priority_rules
                            ]
                        },
                    )
                    self.conflicts.append(conflict)

    def _detect_circular_dependencies(self, rules: List[DSLRule]) -> None:
        """Detect circular dependencies between rules"""
        # This is a simplified check - in practice, you'd need more sophisticated analysis
        for rule in rules:
            for action in rule.actions:
                if action.action_type == "set" and action.field_name in [
                    c.field_name for c in rule.conditions
                ]:
                    # Rule sets a field it also conditions on
                    conflict = RuleConflict(
                        conflict_type=ConflictType.CIRCULAR_DEPENDENCY,
                        rule_ids=[rule.rule_id],
                        message=f"Rule {rule.rule_id} has circular dependency on field {action.field_name}",
                        severity="error",
                        details={"field": action.field_name},
                    )
                    self.conflicts.append(conflict)

    def _detect_type_mismatches(
        self, rules: List[DSLRule], input_schema: Dict[str, Any]
    ) -> None:
        """Detect type mismatches between rules and schema"""
        for rule in rules:
            for condition in rule.conditions:
                field_type = self._get_field_type(condition.field_name, input_schema)
                if field_type and not self._is_type_compatible(
                    condition.value, field_type, condition.operator
                ):
                    conflict = RuleConflict(
                        conflict_type=ConflictType.TYPE_MISMATCH,
                        rule_ids=[rule.rule_id],
                        message=f"Type mismatch in rule {rule.rule_id}: field {condition.field_name} expects {field_type}",
                        severity="error",
                        details={
                            "field": condition.field_name,
                            "expected_type": field_type,
                            "actual_value": condition.value,
                        },
                    )
                    self.conflicts.append(conflict)

    def _detect_missing_fields(
        self, rules: List[DSLRule], input_schema: Dict[str, Any]
    ) -> None:
        """Detect references to missing fields"""
        schema_fields = set(input_schema.keys())

        for rule in rules:
            for condition in rule.conditions:
                if condition.field_name not in schema_fields:
                    conflict = RuleConflict(
                        conflict_type=ConflictType.MISSING_FIELD,
                        rule_ids=[rule.rule_id],
                        message=f"Rule {rule.rule_id} references missing field: {condition.field_name}",
                        severity="error",
                        details={"field": condition.field_name},
                    )
                    self.conflicts.append(conflict)

    def _conditions_overlap(
        self, conditions1: List[RuleCondition], conditions2: List[RuleCondition]
    ) -> bool:
        """Check if two sets of conditions overlap"""
        # Simplified overlap detection - in practice, this would be more sophisticated
        fields1 = {c.field_name for c in conditions1}
        fields2 = {c.field_name for c in conditions2}
        return bool(fields1.intersection(fields2))

    def _rule_is_shadowed(
        self, rule: DSLRule, higher_priority_rules: List[DSLRule]
    ) -> bool:
        """Check if a rule is shadowed by higher priority rules"""
        # Simplified shadowing detection
        rule_fields = {c.field_name for c in rule.conditions}
        for higher_rule in higher_priority_rules:
            higher_fields = {c.field_name for c in higher_rule.conditions}
            if rule_fields.issubset(higher_fields):
                return True
        return False

    def _get_field_type(self, field: str, schema: Dict[str, Any]) -> Optional[str]:
        """Get the type of a field from the schema"""
        return schema.get(field, {}).get("type")

    def _is_type_compatible(
        self, value: Any, expected_type: str, operator: Operator
    ) -> bool:
        """Check if a value is compatible with expected type for the operator"""
        if expected_type == "string":
            return isinstance(value, str) or operator in [Operator.IN, Operator.NOT_IN]
        elif expected_type == "number":
            return isinstance(value, (int, float))
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        return True


class DSLStaticAnalyzer:
    """Static analyzer for DSL schemas"""

    def __init__(self):
        self.conflict_detector = RuleConflictDetector()

    def analyze(self, schema_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive static analysis"""
        analysis_result: Dict[str, Any] = {
            "syntax_errors": [],
            "conflicts": [],
            "warnings": [],
            "metrics": {},
            "recommendations": [],
        }

        # Syntax validation
        syntax_errors = DSLGrammar.validate_syntax(schema_data)
        analysis_result["syntax_errors"] = syntax_errors

        if syntax_errors:
            return analysis_result  # Stop analysis if syntax errors exist

        # Parse schema
        try:
            schema = DSLSchema.from_dict(schema_data)
        except Exception as e:
            analysis_result["syntax_errors"].append(f"Schema parsing failed: {str(e)}")
            return analysis_result

        # Conflict detection
        conflicts = self.conflict_detector.detect_conflicts(schema)
        analysis_result["conflicts"] = [c.to_dict() for c in conflicts]

        # Generate warnings
        warnings = self._generate_warnings(schema)
        analysis_result["warnings"] = warnings

        # Calculate metrics
        metrics = self._calculate_metrics(schema)
        analysis_result["metrics"] = metrics

        # Generate recommendations
        recommendations = self._generate_recommendations(schema, conflicts)
        analysis_result["recommendations"] = recommendations

        return analysis_result

    def _generate_warnings(self, schema: DSLSchema) -> List[str]:
        """Generate warnings for the schema"""
        warnings = []

        # Check for rules without conditions
        for rule in schema.rules:
            if not rule.conditions:
                warnings.append(
                    f"Rule {rule.rule_id} has no conditions (always matches)"
                )

        # Check for rules without actions
        for rule in schema.rules:
            if not rule.actions:
                warnings.append(f"Rule {rule.rule_id} has no actions")

        # Check for disabled rules
        disabled_rules = [r for r in schema.rules if not r.enabled]
        if disabled_rules:
            warnings.append(f"{len(disabled_rules)} rules are disabled")

        return warnings

    def _calculate_metrics(self, schema: DSLSchema) -> Dict[str, Any]:
        """Calculate metrics for the schema"""
        return {
            "total_rules": len(schema.rules),
            "enabled_rules": len([r for r in schema.rules if r.enabled]),
            "disabled_rules": len([r for r in schema.rules if not r.enabled]),
            "rule_types": {
                t.value: len([r for r in schema.rules if r.rule_type == t])
                for t in RuleType
            },
            "priority_range": {
                "min": min(r.priority for r in schema.rules) if schema.rules else 0,
                "max": max(r.priority for r in schema.rules) if schema.rules else 0,
            },
            "average_conditions_per_rule": sum(len(r.conditions) for r in schema.rules)
            / max(len(schema.rules), 1),
            "average_actions_per_rule": sum(len(r.actions) for r in schema.rules)
            / max(len(schema.rules), 1),
        }

    def _generate_recommendations(
        self, schema: DSLSchema, conflicts: List[RuleConflict]
    ) -> List[str]:
        """Generate recommendations for improving the schema"""
        recommendations = []

        # Recommendations based on conflicts
        if any(c.conflict_type == ConflictType.AMBIGUOUS_PRIORITY for c in conflicts):
            recommendations.append("Consider using unique priorities for all rules")

        if any(c.conflict_type == ConflictType.UNREACHABLE_RULE for c in conflicts):
            recommendations.append(
                "Review rule priorities to ensure all rules are reachable"
            )

        # General recommendations
        if len(schema.rules) > 20:
            recommendations.append(
                "Consider splitting large rule sets into multiple schemas"
            )

        if any(len(r.conditions) > 5 for r in schema.rules):
            recommendations.append("Consider simplifying rules with many conditions")

        return recommendations


# Example DSL schema with conflicts
EXAMPLE_CONFLICTED_SCHEMA = {
    "name": "loan_approval",
    "version": "1.0",
    "rules": [
        {
            "rule_id": "high_amount_approval",
            "rule_type": "threshold",
            "priority": 100,
            "conditions": [
                {"field": "amount", "operator": ">=", "value": 100000},
                {"field": "credit_score", "operator": ">=", "value": 750},
            ],
            "actions": [{"action_type": "set", "field": "approved", "value": True}],
            "description": "Approve high amount loans with good credit",
        },
        {
            "rule_id": "high_amount_rejection",
            "rule_type": "threshold",
            "priority": 100,  # Same priority - conflict!
            "conditions": [
                {"field": "amount", "operator": ">=", "value": 100000},
                {"field": "credit_score", "operator": "<", "value": 600},
            ],
            "actions": [{"action_type": "set", "field": "approved", "value": False}],
            "description": "Reject high amount loans with poor credit",
        },
        {
            "rule_id": "unreachable_rule",
            "rule_type": "threshold",
            "priority": 50,  # Lower priority - will be unreachable
            "conditions": [{"field": "amount", "operator": ">=", "value": 100000}],
            "actions": [{"action_type": "set", "field": "approved", "value": True}],
            "description": "This rule will never be reached",
        },
    ],
    "input_schema": {
        "amount": {"type": "number"},
        "credit_score": {"type": "number"},
        "income": {"type": "number"},
    },
    "output_schema": {"approved": {"type": "boolean"}, "reason": {"type": "string"}},
}


def create_dsl_analyzer() -> DSLStaticAnalyzer:
    """Create a DSL static analyzer"""
    return DSLStaticAnalyzer()


def analyze_dsl_schema(schema_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a DSL schema for conflicts and issues"""
    analyzer = create_dsl_analyzer()
    return analyzer.analyze(schema_data)
