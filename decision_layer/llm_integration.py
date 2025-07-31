"""
LLM Integration for Decision Layer

Provides integration between Large Language Models and decision functions,
enabling natural language generation, consumption, and explanation of
decision logic.
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .registry import FunctionArtifact, FunctionRegistry
from .schemas import create_schema_from_dict


class LLMProvider(ABC):
    """Abstract interface for LLM providers"""

    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using the LLM"""
        pass

    @abstractmethod
    async def generate_structured(
        self, prompt: str, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured output using the LLM"""
        pass


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing and development"""

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Mock text generation"""
        if "generate decision function" in prompt.lower():
            return self._mock_decision_function()
        elif "explain" in prompt.lower():
            return self._mock_explanation()
        else:
            return "Mock LLM response"

    async def generate_structured(
        self, prompt: str, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock structured generation"""
        if "schema" in prompt.lower():
            return {
                "input_schema": {
                    "user_id": {"type": "integer", "required": True},
                    "amount": {"type": "float", "required": True},
                },
                "output_schema": {
                    "approved": {"type": "boolean", "required": True},
                    "reason": {"type": "string", "required": True},
                },
            }
        return {"result": "mock_structured_response"}

    def _mock_decision_function(self) -> str:
        return '''
def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    """LLM-generated decision function"""

    user_id = input_data.get('user_id', 0)
    amount = input_data.get('amount', 0.0)

    # Decision logic
    if amount > 1000:
        return {"approved": False, "reason": "Amount exceeds limit"}
    else:
        return {"approved": True, "reason": "Amount within acceptable range"}
'''

    def _mock_explanation(self) -> str:
        return "This decision function checks if the requested amount is within acceptable limits."


@dataclass
class LLMGenerationRequest:
    """Request for LLM-based generation"""

    prompt: str
    context: Optional[Dict[str, Any]] = None
    examples: Optional[List[Dict[str, Any]]] = None
    constraints: Optional[List[str]] = None
    output_format: str = "text"  # "text", "json", "python"


@dataclass
class LLMExplanationRequest:
    """Request for LLM-based explanation"""

    function_id: str
    version: Optional[str] = None
    audience: str = "technical"  # "technical", "business", "user"
    format: str = "natural"  # "natural", "structured", "code"
    include_examples: bool = True


class LLMIntegration:
    """
    Integration layer between LLMs and Decision Layer

    Provides capabilities for:
    - Generating decision functions from natural language
    - Explaining decision functions in natural language
    - Answering natural language queries about decisions
    """

    def __init__(self, registry: FunctionRegistry, llm_provider: LLMProvider):
        self.registry = registry
        self.llm = llm_provider

    async def generate_decision_function(
        self,
        policy_description: str,
        function_id: str,
        version: str = "1.0",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FunctionArtifact:
        """
        Generate a decision function from natural language policy description

        Args:
            policy_description: Natural language description of the policy
            function_id: Unique identifier for the function
            version: Version string
            metadata: Additional metadata

        Returns:
            FunctionArtifact with generated code and schema
        """

        # Step 1: Generate schema from policy description
        schema_prompt = self._create_schema_generation_prompt(policy_description)
        schema_dict = await self.llm.generate_structured(
            schema_prompt,
            {
                "type": "object",
                "properties": {
                    "input_schema": {"type": "object"},
                    "output_schema": {"type": "object"},
                },
            },
        )

        schema = create_schema_from_dict(schema_dict)
        schema.function_id = function_id
        schema.version = version

        # Step 2: Generate decision function code
        code_prompt = self._create_code_generation_prompt(
            policy_description, schema_dict
        )
        function_code = await self.llm.generate_text(code_prompt)

        # Step 3: Clean and validate generated code
        cleaned_code = self._clean_generated_code(function_code)

        # Step 4: Register the function
        artifact = self.registry.register_function(
            function_id=function_id,
            version=version,
            logic_code=cleaned_code,
            schema=schema,
            metadata=metadata or {},
            status="draft",
        )

        return artifact

    async def explain_decision_function(
        self,
        function_id: str,
        version: Optional[str] = None,
        audience: str = "technical",
        format: str = "natural",
    ) -> str:
        """
        Generate natural language explanation of a decision function

        Args:
            function_id: Function to explain
            version: Specific version (defaults to latest)
            audience: Target audience ("technical", "business", "user")
            format: Output format ("natural", "structured", "code")

        Returns:
            Natural language explanation
        """

        # Get function artifact
        if version is None:
            version = self.registry.get_latest_version(function_id)

        artifact = self.registry.get_function(function_id, version)

        # Create explanation prompt
        prompt = self._create_explanation_prompt(artifact, audience, format)

        return await self.llm.generate_text(prompt)

    async def answer_natural_language_query(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Answer natural language queries about decisions

        Args:
            query: Natural language query
            context: Additional context (user_id, time_range, etc.)

        Returns:
            Structured answer with relevant information
        """

        # Parse query intent
        intent = await self._parse_query_intent(query)

        if intent["type"] == "function_search":
            return await self._handle_function_search(query, context)
        elif intent["type"] == "decision_explanation":
            return await self._handle_decision_explanation(query, context)
        elif intent["type"] == "trace_query":
            return await self._handle_trace_query(query, context)
        else:
            return {"answer": "I don't understand that query", "type": "unknown"}

    async def generate_policy_documentation(
        self, function_id: str, version: Optional[str] = None
    ) -> str:
        """
        Generate policy documentation from decision function

        Args:
            function_id: Function to document
            version: Specific version (defaults to latest)

        Returns:
            Policy documentation in markdown format
        """

        if version is None:
            version = self.registry.get_latest_version(function_id)

        artifact = self.registry.get_function(function_id, version)

        prompt = f"""
        Generate comprehensive policy documentation for the following decision function:

        Function ID: {artifact.function_id}
        Version: {artifact.version}
        Description: {artifact.metadata.description or 'No description provided'}

        Code:
        {artifact.logic_code}

        Input Schema:
        {json.dumps(artifact.schema.input_schema, indent=2)}

        Output Schema:
        {json.dumps(artifact.schema.output_schema, indent=2)}

        Generate markdown documentation that includes:
        1. Policy overview and purpose
        2. Input requirements and validation
        3. Decision logic explanation
        4. Output interpretation
        5. Examples and use cases
        6. Compliance considerations
        """

        return await self.llm.generate_text(prompt)

    def _create_schema_generation_prompt(self, policy_description: str) -> str:
        """Create prompt for schema generation"""
        return f"""
        Based on the following policy description, generate a JSON schema for input and output:

        Policy: {policy_description}

        Generate a JSON object with:
        - input_schema: Object defining required input fields with types and constraints
        - output_schema: Object defining output fields with types

        Use appropriate types: string, integer, float, boolean, array, object
        Include validation constraints like min/max values, enums, required fields
        """

    def _create_code_generation_prompt(
        self, policy_description: str, schema_dict: Dict[str, Any]
    ) -> str:
        """Create prompt for code generation"""
        return f"""
        Generate a Python decision function based on this policy and schema:

        Policy: {policy_description}

        Schema:
        {json.dumps(schema_dict, indent=2)}

        Requirements:
        1. Function must be named 'decision_function'
        2. Take input_data (Dict[str, Any]) and context (DecisionContext) parameters
        3. Return Dict[str, Any] with structured output
        4. Include proper error handling
        5. Add docstring explaining the logic
        6. Use the exact field names from the schema
        7. Include decision reasoning in the output
        """

    def _create_explanation_prompt(
        self, artifact: FunctionArtifact, audience: str, format: str
    ) -> str:
        """Create prompt for function explanation"""

        audience_instructions = {
            "technical": "Explain the technical implementation, code structure, and logic flow",
            "business": "Explain the business rules, decision criteria, and business impact",
            "user": "Explain in simple terms what the function does and how it affects users",
        }

        format_instructions = {
            "natural": "Provide a natural language explanation",
            "structured": "Provide a structured explanation with sections",
            "code": "Explain the code line by line",
        }

        return f"""
        Explain this decision function for a {audience} audience in {format} format:

        Function: {artifact.function_id} v{artifact.version}
        Description: {artifact.metadata.description or 'No description'}

        Code:
        {artifact.logic_code}

        Input Schema:
        {json.dumps(artifact.schema.input_schema, indent=2)}

        Output Schema:
        {json.dumps(artifact.schema.output_schema, indent=2)}

        Instructions:
        {audience_instructions.get(audience, '')}
        {format_instructions.get(format, '')}
        """

    async def _parse_query_intent(self, query: str) -> Dict[str, Any]:
        """Parse the intent of a natural language query"""

        prompt = f"""
        Analyze this query and determine its intent:
        Query: "{query}"

        Classify as one of:
        - function_search: Looking for decision functions
        - decision_explanation: Wanting to understand a decision
        - trace_query: Looking for decision history/traces
        - unknown: Not sure what they're asking for

        Return JSON with:
        - type: The intent classification
        - entities: Any entities mentioned (function names, user IDs, etc.)
        - time_range: Any time references
        """

        result = await self.llm.generate_structured(
            prompt,
            {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "entities": {"type": "array"},
                    "time_range": {"type": "string"},
                },
            },
        )

        return result

    async def _handle_function_search(
        self, query: str, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle function search queries"""

        # Extract search terms
        search_terms = await self._extract_search_terms(query)

        # Search registry
        functions = self.registry.search_functions(
            text_search=search_terms.get("text"),
            tags=search_terms.get("tags"),
            author=search_terms.get("author"),
        )

        return {
            "type": "function_search",
            "query": query,
            "results": [
                {
                    "function_id": f.function_id,
                    "version": f.version,
                    "title": f.metadata.title,
                    "description": f.metadata.description,
                    "tags": f.metadata.tags,
                }
                for f in functions
            ],
        }

    async def _handle_decision_explanation(
        self, query: str, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle decision explanation queries"""

        # Extract function reference
        function_ref = await self._extract_function_reference(query)

        if function_ref:
            explanation = await self.explain_decision_function(
                function_ref["function_id"],
                function_ref.get("version"),
                audience="user",
            )

            return {
                "type": "decision_explanation",
                "function_id": function_ref["function_id"],
                "explanation": explanation,
            }

        return {
            "type": "error",
            "message": "Could not identify which decision to explain",
        }

    async def _handle_trace_query(
        self, query: str, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle trace/history queries"""

        # This would integrate with the tracing system
        # For now, return a placeholder
        return {
            "type": "trace_query",
            "message": "Trace query functionality would be implemented here",
            "query": query,
        }

    async def _extract_search_terms(self, query: str) -> Dict[str, Any]:
        """Extract search terms from query"""

        prompt = f"""
        Extract search terms from this query:
        Query: "{query}"

        Return JSON with:
        - text: General text search terms
        - tags: Any tags or categories mentioned
        - author: Any author names mentioned
        """

        return await self.llm.generate_structured(
            prompt,
            {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "tags": {"type": "array"},
                    "author": {"type": "string"},
                },
            },
        )

    async def _extract_function_reference(self, query: str) -> Optional[Dict[str, str]]:
        """Extract function reference from query"""

        prompt = f"""
        Extract function reference from this query:
        Query: "{query}"

        Return JSON with:
        - function_id: The function ID mentioned
        - version: The version mentioned (if any)

        If no function is mentioned, return null.
        """

        result = await self.llm.generate_structured(
            prompt,
            {
                "type": ["object", "null"],
                "properties": {
                    "function_id": {"type": "string"},
                    "version": {"type": "string"},
                },
            },
        )

        return result if result else None

    def _clean_generated_code(self, code: str) -> str:
        """Clean and validate generated code"""

        # Extract code block if wrapped in markdown
        if "```python" in code:
            code = re.search(r"```python\s*(.*?)\s*```", code, re.DOTALL)
            if code:
                code = code.group(1)

        # Ensure it has the required function signature
        if "def decision_function" not in code:
            code = f"""
from typing import Dict, Any
from decision_layer import DecisionContext

{code}
"""

        return code.strip()


# Factory function for creating LLM providers
def create_llm_provider(provider_type: str, config: Dict[str, Any]) -> LLMProvider:
    """Create LLM provider based on configuration"""

    if provider_type == "mock":
        return MockLLMProvider()
    elif provider_type == "openai":
        # Would implement OpenAI integration
        raise NotImplementedError("OpenAI integration not yet implemented")
    elif provider_type == "anthropic":
        # Would implement Anthropic integration
        raise NotImplementedError("Anthropic integration not yet implemented")
    else:
        raise ValueError(f"Unknown LLM provider: {provider_type}")


# Factory function for creating LLM integration
def create_llm_integration(
    registry: FunctionRegistry,
    provider_type: str = "mock",
    config: Optional[Dict[str, Any]] = None,
) -> LLMIntegration:
    """Create LLM integration with registry and provider"""
    if config is None:
        config = {}

    provider = create_llm_provider(provider_type, config)
    return LLMIntegration(registry, provider)
