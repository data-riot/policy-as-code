"""
Decision Function Constraints and Determinism Guardrails
Formal DSL constraints and banned side-effects for auditable functions
"""

import ast
import inspect
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

from .errors import DecisionLayerError


class ConstraintViolationType(str, Enum):
    """Types of constraint violations"""

    NETWORK_ACCESS = "network_access"
    FILE_IO = "file_io"
    RANDOMNESS = "randomness"
    TIME_DEPENDENT = "time_dependent"
    SIDE_EFFECTS = "side_effects"
    BANNED_IMPORT = "banned_import"
    EXTERNAL_CALL = "external_call"


@dataclass
class ConstraintViolation:
    """Constraint violation details"""

    violation_type: ConstraintViolationType
    line_number: int
    code_snippet: str
    message: str
    severity: str = "error"  # error, warning

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "violation_type": self.violation_type.value,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "message": self.message,
            "severity": self.severity,
        }


class DeterminismError(DecisionLayerError):
    """Determinism constraint errors"""

    def __init__(
        self,
        error_type: str,
        message: str,
        violations: Optional[List[ConstraintViolation]] = None,
    ):
        super().__init__(f"Determinism error ({error_type}): {message}")
        self.error_type = error_type
        self.violations = violations or []


class DFConstraintChecker:
    """Static analysis checker for decision function constraints"""

    # Banned imports that could cause non-deterministic behavior
    BANNED_IMPORTS = {
        "random",
        "time",
        "datetime",
        "os",
        "sys",
        "subprocess",
        "urllib",
        "requests",
        "socket",
        "http",
        "ftplib",
        "smtplib",
        "sqlite3",
        "psycopg2",
        "pymongo",
        "redis",
        "boto3",
        "threading",
        "multiprocessing",
        "asyncio",
        "concurrent",
        "pickle",
        "marshal",
        "shelve",
        "dbm",
        "gdbm",
        "tempfile",
        "shutil",
        "glob",
        "pathlib",
        "zipfile",
        "tarfile",
    }

    # Banned function calls
    BANNED_FUNCTIONS = {
        "random.random",
        "random.randint",
        "random.choice",
        "random.shuffle",
        "time.time",
        "time.sleep",
        "datetime.now",
        "datetime.utcnow",
        "open",
        "file",
        "input",
        "print",
        "exit",
        "quit",
        "eval",
        "exec",
        "compile",
        "__import__",
        "getattr",
        "setattr",
        "delattr",
        "hasattr",
        "globals",
        "locals",
        "vars",
        "dir",
    }

    def __init__(self):
        self.violations: List[ConstraintViolation] = []

    def check_function(self, function_code: str) -> List[ConstraintViolation]:
        """Check a function for constraint violations"""
        self.violations = []

        try:
            # Parse the function code
            tree = ast.parse(function_code)

            # Check for violations
            self._check_imports(tree)
            self._check_function_calls(tree)
            self._check_side_effects(tree)
            self._check_time_dependencies(tree)

        except SyntaxError as e:
            self.violations.append(
                ConstraintViolation(
                    violation_type=ConstraintViolationType.SIDE_EFFECTS,
                    line_number=e.lineno or 0,
                    code_snippet="",
                    message=f"Syntax error: {str(e)}",
                    severity="error",
                )
            )

        return self.violations

    def _check_imports(self, tree: ast.AST) -> None:
        """Check for banned imports"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.BANNED_IMPORTS:
                        self.violations.append(
                            ConstraintViolation(
                                violation_type=ConstraintViolationType.BANNED_IMPORT,
                                line_number=node.lineno,
                                code_snippet=f"import {alias.name}",
                                message=f"Banned import: {alias.name}",
                                severity="error",
                            )
                        )

            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module in self.BANNED_IMPORTS:
                    self.violations.append(
                        ConstraintViolation(
                            violation_type=ConstraintViolationType.BANNED_IMPORT,
                            line_number=node.lineno,
                            code_snippet=f"from {node.module} import ...",
                            message=f"Banned import from: {node.module}",
                            severity="error",
                        )
                    )

    def _check_function_calls(self, tree: ast.AST) -> None:
        """Check for banned function calls"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                if func_name in self.BANNED_FUNCTIONS:
                    self.violations.append(
                        ConstraintViolation(
                            violation_type=ConstraintViolationType.EXTERNAL_CALL,
                            line_number=node.lineno,
                            code_snippet=ast.unparse(node),
                            message=f"Banned function call: {func_name}",
                            severity="error",
                        )
                    )

    def _check_side_effects(self, tree: ast.AST) -> None:
        """Check for side effects"""
        for node in ast.walk(tree):
            # Check for file operations
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                if func_name in {"open", "file"}:
                    self.violations.append(
                        ConstraintViolation(
                            violation_type=ConstraintViolationType.FILE_IO,
                            line_number=node.lineno,
                            code_snippet=ast.unparse(node),
                            message="File I/O operations not allowed",
                            severity="error",
                        )
                    )

            # Check for attribute assignment (potential side effects)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute):
                        self.violations.append(
                            ConstraintViolation(
                                violation_type=ConstraintViolationType.SIDE_EFFECTS,
                                line_number=node.lineno,
                                code_snippet=ast.unparse(node),
                                message="Attribute assignment may cause side effects",
                                severity="warning",
                            )
                        )

    def _check_time_dependencies(self, tree: ast.AST) -> None:
        """Check for time-dependent operations"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                if func_name in {"time.time", "datetime.now", "datetime.utcnow"}:
                    self.violations.append(
                        ConstraintViolation(
                            violation_type=ConstraintViolationType.TIME_DEPENDENT,
                            line_number=node.lineno,
                            code_snippet=ast.unparse(node),
                            message="Time-dependent operations not allowed",
                            severity="error",
                        )
                    )

    def _get_function_name(self, node: ast.AST) -> str:
        """Extract function name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_function_name(node.value)}.{node.attr}"
        else:
            return "unknown"


def df_pure(func: Callable) -> Callable:
    """Decorator to mark a function as pure (deterministic)"""

    def wrapper(*args, **kwargs):
        # Check function code for violations
        source = inspect.getsource(func)
        checker = DFConstraintChecker()
        violations = checker.check_function(source)

        if violations:
            error_violations = [v for v in violations if v.severity == "error"]
            if error_violations:
                raise DeterminismError(
                    "constraint_violation",
                    f"Function {func.__name__} violates determinism constraints",
                    error_violations,
                )

        # Execute the function
        return func(*args, **kwargs)

    return wrapper


class DeterministicFunction:
    """Wrapper for deterministic function execution"""

    def __init__(self, function_code: str, function_name: str = "decision_function"):
        self.function_code = function_code
        self.function_name = function_name
        self.checker = DFConstraintChecker()
        self.compiled_function: Optional[Callable] = None
        self.violations: List[ConstraintViolation] = []

    def validate(self) -> List[ConstraintViolation]:
        """Validate the function for determinism constraints"""
        self.violations = self.checker.check_function(self.function_code)
        return self.violations

    def compile(self) -> None:
        """Compile the function if valid"""
        violations = self.validate()
        error_violations = [v for v in violations if v.severity == "error"]

        if error_violations:
            raise DeterminismError(
                "compilation_failed",
                f"Cannot compile function {self.function_name} due to constraint violations",
                error_violations,
            )

        try:
            # Compile the function
            compiled_code = compile(
                self.function_code, f"<{self.function_name}>", "exec"
            )

            # Create a namespace for the function
            namespace = {
                "__builtins__": {
                    # Only allow safe built-ins
                    "len",
                    "str",
                    "int",
                    "float",
                    "bool",
                    "list",
                    "dict",
                    "tuple",
                    "set",
                    "min",
                    "max",
                    "sum",
                    "abs",
                    "round",
                    "sorted",
                    "reversed",
                    "enumerate",
                    "zip",
                    "map",
                    "filter",
                    "any",
                    "all",
                    "isinstance",
                    "issubclass",
                    "type",
                    "hasattr",
                    "getattr",
                    "ValueError",
                    "TypeError",
                    "KeyError",
                    "IndexError",
                }
            }

            exec(compiled_code, namespace)

            # Extract the function from namespace
            if self.function_name in namespace:
                func = namespace[self.function_name]
                if callable(func):
                    self.compiled_function = func
                else:
                    raise DeterminismError(
                        "invalid_function_type",
                        f"Expected callable function, got {type(func)}",
                    )
            else:
                raise DeterminismError(
                    "function_not_found",
                    f"Function {self.function_name} not found in compiled code",
                )

        except Exception as e:
            raise DeterminismError(
                "compilation_error", f"Failed to compile function: {str(e)}"
            )

    def execute(
        self, input_data: Dict[str, Any], context: Any = None
    ) -> Dict[str, Any]:
        """Execute the deterministic function"""
        if not self.compiled_function:
            raise DeterminismError(
                "not_compiled", "Function must be compiled before execution"
            )

        try:
            # Execute with deterministic environment
            result = self.compiled_function(input_data, context)
            return result
        except Exception as e:
            raise DeterminismError(
                "execution_error", f"Function execution failed: {str(e)}"
            )


class DSLTranspiler:
    """Simple DSL transpiler for rule-based decision functions"""

    def __init__(self):
        self.rule_templates = {
            "if_then": self._transpile_if_then,
            "threshold": self._transpile_threshold,
            "range_check": self._transpile_range_check,
            "enum_match": self._transpile_enum_match,
        }

    def transpile_yaml_rules(self, yaml_rules: Dict[str, Any]) -> str:
        """Transpile YAML rules to Python function"""
        function_name = yaml_rules.get("name", "decision_function")
        rules = yaml_rules.get("rules", [])

        python_code = f"def {function_name}(input_data, context):\n"
        python_code += '    """Generated decision function from DSL rules"""\n'
        python_code += "    result = {}\n"
        python_code += "    \n"

        for rule in rules:
            rule_type = rule.get("type")
            if rule_type in self.rule_templates:
                rule_code = self.rule_templates[rule_type](rule)
                python_code += f"    {rule_code}\n"

        python_code += "    return result\n"

        return python_code

    def _transpile_if_then(self, rule: Dict[str, Any]) -> str:
        """Transpile if-then rule"""
        condition = rule.get("condition", "")
        action = rule.get("action", "")

        return f"if {condition}:\n        {action}"

    def _transpile_threshold(self, rule: Dict[str, Any]) -> str:
        """Transpile threshold rule"""
        field = rule.get("field", "")
        threshold = rule.get("threshold", 0)
        operator = rule.get("operator", ">=")
        output_field = rule.get("output_field", "approved")

        return f"result['{output_field}'] = input_data.get('{field}', 0) {operator} {threshold}"

    def _transpile_range_check(self, rule: Dict[str, Any]) -> str:
        """Transpile range check rule"""
        field = rule.get("field", "")
        min_val = rule.get("min", 0)
        max_val = rule.get("max", 100)
        output_field = rule.get("output_field", "in_range")

        return f"result['{output_field}'] = {min_val} <= input_data.get('{field}', 0) <= {max_val}"

    def _transpile_enum_match(self, rule: Dict[str, Any]) -> str:
        """Transpile enum match rule"""
        field = rule.get("field", "")
        values = rule.get("values", [])
        output_field = rule.get("output_field", "matched")

        values_str = str(values)
        return f"result['{output_field}'] = input_data.get('{field}') in {values_str}"


def create_deterministic_function(
    function_code: str, function_name: str = "decision_function"
) -> DeterministicFunction:
    """Create a deterministic function with constraint checking"""
    return DeterministicFunction(function_code, function_name)


def create_dsl_transpiler() -> DSLTranspiler:
    """Create a DSL transpiler instance"""
    return DSLTranspiler()


# Example DSL rule definition
EXAMPLE_DSL_RULES = {
    "name": "approval_decision",
    "rules": [
        {
            "type": "threshold",
            "field": "amount",
            "threshold": 1000,
            "operator": "<=",
            "output_field": "amount_approved",
            "output_value": True,
        },
        {
            "type": "threshold",
            "field": "customer_score",
            "threshold": 700,
            "operator": ">=",
            "output_field": "score_approved",
            "output_value": True,
        },
        {
            "type": "if_then",
            "condition": "result.get('amount_approved', False) and result.get('score_approved', False)",
            "action": "result['approved'] = True",
        },
    ],
}
