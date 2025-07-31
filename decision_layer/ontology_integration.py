"""
Ontology Integration for Decision Layer

Provides integration between ontologies and decision functions,
enabling ontology-driven schema generation, semantic validation,
and context enrichment.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .schemas import DecisionSchema, FieldType, SchemaField


class OntologyProvider(ABC):
    """Abstract interface for ontology providers"""

    @abstractmethod
    def get_classes(self) -> List[str]:
        """Get all available ontology classes"""
        pass

    @abstractmethod
    def get_class_properties(self, class_name: str) -> List[Dict[str, Any]]:
        """Get properties for a specific class"""
        pass

    @abstractmethod
    def get_class_relationships(self, class_name: str) -> List[Dict[str, Any]]:
        """Get relationships for a specific class"""
        pass

    @abstractmethod
    def validate_entity(self, entity_data: Dict[str, Any], class_name: str) -> bool:
        """Validate entity data against ontology class"""
        pass

    @abstractmethod
    def get_related_entities(self, entity_id: str, relationship_type: str) -> List[str]:
        """Get related entities through specific relationship"""
        pass


class MockOntologyProvider(OntologyProvider):
    """Mock ontology provider for testing and development"""

    def __init__(self):
        self.ontology = {
            "Patient": {
                "properties": [
                    {"name": "patient_id", "type": "string", "required": True},
                    {"name": "age", "type": "integer", "min": 0, "max": 150},
                    {
                        "name": "gender",
                        "type": "enum",
                        "values": ["male", "female", "other"],
                    },
                    {"name": "diagnosis", "type": "string"},
                    {"name": "medications", "type": "array", "item_type": "string"},
                ],
                "relationships": [
                    {"name": "has_doctor", "target": "Doctor", "type": "many_to_one"},
                    {
                        "name": "has_appointments",
                        "target": "Appointment",
                        "type": "one_to_many",
                    },
                ],
            },
            "Doctor": {
                "properties": [
                    {"name": "doctor_id", "type": "string", "required": True},
                    {"name": "name", "type": "string", "required": True},
                    {"name": "specialty", "type": "string"},
                    {"name": "license_number", "type": "string"},
                ],
                "relationships": [
                    {
                        "name": "has_patients",
                        "target": "Patient",
                        "type": "one_to_many",
                    },
                    {"name": "works_at", "target": "Hospital", "type": "many_to_one"},
                ],
            },
            "Medication": {
                "properties": [
                    {"name": "medication_id", "type": "string", "required": True},
                    {"name": "name", "type": "string", "required": True},
                    {"name": "dosage", "type": "string"},
                    {"name": "frequency", "type": "string"},
                    {
                        "name": "requires_prescription",
                        "type": "boolean",
                        "default": True,
                    },
                ],
                "relationships": [
                    {
                        "name": "prescribed_for",
                        "target": "Patient",
                        "type": "many_to_many",
                    }
                ],
            },
        }

    def get_classes(self) -> List[str]:
        """Get all available ontology classes"""
        return list(self.ontology.keys())

    def get_class_properties(self, class_name: str) -> List[Dict[str, Any]]:
        """Get properties for a specific class"""
        if class_name not in self.ontology:
            raise ValueError(f"Unknown ontology class: {class_name}")
        return self.ontology[class_name]["properties"]

    def get_class_relationships(self, class_name: str) -> List[Dict[str, Any]]:
        """Get relationships for a specific class"""
        if class_name not in self.ontology:
            raise ValueError(f"Unknown ontology class: {class_name}")
        return self.ontology[class_name]["relationships"]

    def validate_entity(self, entity_data: Dict[str, Any], class_name: str) -> bool:
        """Validate entity data against ontology class"""
        if class_name not in self.ontology:
            return False

        properties = self.ontology[class_name]["properties"]

        for prop in properties:
            prop_name = prop["name"]
            required = prop.get("required", False)

            # Check required fields
            if required and prop_name not in entity_data:
                return False

            # Check type if value exists
            if prop_name in entity_data:
                value = entity_data[prop_name]
                if not self._validate_property_type(value, prop):
                    return False

        return True

    def get_related_entities(self, entity_id: str, relationship_type: str) -> List[str]:
        """Get related entities through specific relationship"""
        # Mock implementation - would query actual ontology
        return [f"related_entity_{i}" for i in range(3)]

    def _validate_property_type(self, value: Any, prop: Dict[str, Any]) -> bool:
        """Validate property value against type definition"""
        prop_type = prop["type"]

        if prop_type == "string":
            return isinstance(value, str)
        elif prop_type == "integer":
            return isinstance(value, int)
        elif prop_type == "boolean":
            return isinstance(value, bool)
        elif prop_type == "array":
            return isinstance(value, list)
        elif prop_type == "enum":
            return value in prop.get("values", [])

        return True


@dataclass
class OntologySchemaMapping:
    """Mapping between ontology and schema definitions"""

    ontology_class: str
    schema_fields: Dict[str, SchemaField]
    relationships: List[Dict[str, Any]]
    validation_rules: List[Dict[str, Any]]


class OntologyIntegration:
    """
    Integration layer between ontologies and Decision Layer

    Provides capabilities for:
    - Generating schemas from ontology classes
    - Validating data against ontologies
    - Enriching decision context with ontological relationships
    """

    def __init__(self, ontology_provider: OntologyProvider):
        self.ontology = ontology_provider

    def create_schema_from_ontology(
        self, ontology_class: str, include_relationships: bool = True
    ) -> DecisionSchema:
        """
        Create a decision schema from an ontology class

        Args:
            ontology_class: Name of the ontology class
            include_relationships: Whether to include relationship fields

        Returns:
            DecisionSchema based on ontology definition
        """

        # Get ontology class properties
        properties = self.ontology.get_class_properties(ontology_class)

        # Convert properties to schema fields
        input_schema = {}
        for prop in properties:
            field = self._property_to_schema_field(prop)
            input_schema[prop["name"]] = field

        # Add relationship fields if requested
        if include_relationships:
            relationships = self.ontology.get_class_relationships(ontology_class)
            for rel in relationships:
                field = self._relationship_to_schema_field(rel)
                input_schema[rel["name"]] = field

        # Create output schema (basic structure)
        output_schema = {
            "valid": SchemaField(
                name="valid",
                type=FieldType.BOOLEAN,
                required=True,
                description="Whether the entity is valid according to ontology",
            ),
            "validation_errors": SchemaField(
                name="validation_errors",
                type=FieldType.ARRAY,
                required=False,
                description="List of validation errors if any",
            ),
            "related_entities": SchemaField(
                name="related_entities",
                type=FieldType.OBJECT,
                required=False,
                description="Related entities found through relationships",
            ),
        }

        return DecisionSchema(
            input_schema=input_schema,
            output_schema=output_schema,
            version="1.0",
            function_id=f"ontology_validation_{ontology_class.lower()}",
            description=f"Ontology validation for {ontology_class}",
            author="ontology-system",
            tags=["ontology", "validation", ontology_class.lower()],
            policy_references=[f"ONT-{ontology_class}"],
            compliance_requirements=["ontology-compliance"],
        )

    def create_ontology_validation_function(self, ontology_class: str) -> str:
        """
        Generate decision function code for ontology validation

        Args:
            ontology_class: Name of the ontology class to validate

        Returns:
            Python code for the validation function
        """

        return f'''
from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    """
    Ontology validation function for {ontology_class}

    Validates input data against {ontology_class} ontology definition
    and returns validation results with related entity information.
    """

    # Validate against ontology
    is_valid = True
    validation_errors = []
    related_entities = {{}}

    try:
        # Basic validation
        if not input_data:
            is_valid = False
            validation_errors.append("No input data provided")
            return {{
                "valid": is_valid,
                "validation_errors": validation_errors,
                "related_entities": related_entities,
                "ontology_class": "{ontology_class}",
                "function_id": context.function_id,
                "version": context.version
            }}

        # Check required fields based on ontology
        required_fields = {self._get_required_fields(ontology_class)}
        for field in required_fields:
            if field not in input_data:
                is_valid = False
                validation_errors.append(f"Required field '{{field}}' is missing")

        # Type validation
        type_errors = self._validate_types(input_data, "{ontology_class}")
        validation_errors.extend(type_errors)
        if type_errors:
            is_valid = False

        # Relationship validation and enrichment
        if is_valid:
            relationships = {self._get_relationships(ontology_class)}
            for rel_name, rel_info in relationships.items():
                if rel_name in input_data:
                    related_ids = input_data[rel_name]
                    if isinstance(related_ids, list):
                        related_entities[rel_name] = []
                        for rel_id in related_ids:
                            # Mock relationship lookup - would query actual ontology
                            related_entities[rel_name].append({{
                                "id": rel_id,
                                "type": rel_info["target"],
                                "relationship": rel_info["type"]
                            }})

    except Exception as e:
        is_valid = False
        validation_errors.append(f"Validation error: {{str(e)}}")

    return {{
        "valid": is_valid,
        "validation_errors": validation_errors,
        "related_entities": related_entities,
        "ontology_class": "{ontology_class}",
        "function_id": context.function_id,
        "version": context.version
    }}

def _validate_types(data: Dict[str, Any], ontology_class: str) -> List[str]:
    """Validate data types against ontology definition"""
    errors = []

    # Mock type validation - would use actual ontology
    type_definitions = {self._get_type_definitions(ontology_class)}

    for field_name, value in data.items():
        if field_name in type_definitions:
            expected_type = type_definitions[field_name]
            if not _check_type(value, expected_type):
                errors.append(f"Field '{{field_name}}' has wrong type. Expected {{expected_type}}")

    return errors

def _check_type(value: Any, expected_type: str) -> bool:
    """Check if value matches expected type"""
    if expected_type == "string":
        return isinstance(value, str)
    elif expected_type == "integer":
        return isinstance(value, int)
    elif expected_type == "boolean":
        return isinstance(value, bool)
    elif expected_type == "array":
        return isinstance(value, list)
    else:
        return True
'''

    def enrich_with_ontology(
        self,
        input_data: Dict[str, Any],
        ontology_class: str,
        include_relationships: bool = True,
    ) -> Dict[str, Any]:
        """
        Enrich input data with ontological context

        Args:
            input_data: Original input data
            ontology_class: Ontology class to use for enrichment
            include_relationships: Whether to include relationship data

        Returns:
            Enriched input data with ontological context
        """

        enriched_data = input_data.copy()

        # Add ontology metadata
        enriched_data["_ontology"] = {
            "class": ontology_class,
            "validation_timestamp": "2025-01-27T12:00:00Z",
            "enrichment_level": "full" if include_relationships else "basic",
        }

        # Add relationship data if requested
        if include_relationships:
            relationships = self.ontology.get_class_relationships(ontology_class)
            enriched_data["_relationships"] = {}

            for rel in relationships:
                rel_name = rel["name"]
                # Mock relationship lookup - would query actual ontology
                enriched_data["_relationships"][rel_name] = {
                    "target_class": rel["target"],
                    "relationship_type": rel["type"],
                    "related_entities": self.ontology.get_related_entities(
                        input_data.get("id", "unknown"), rel_name
                    ),
                }

        return enriched_data

    def validate_with_ontology(
        self, data: Dict[str, Any], ontology_class: str
    ) -> Dict[str, Any]:
        """
        Validate data against ontology definition

        Args:
            data: Data to validate
            ontology_class: Ontology class to validate against

        Returns:
            Validation results
        """

        is_valid = self.ontology.validate_entity(data, ontology_class)

        # Get class properties for detailed validation
        properties = self.ontology.get_class_properties(ontology_class)
        validation_details = []

        for prop in properties:
            prop_name = prop["name"]
            if prop_name in data:
                value = data[prop_name]
                if not self._validate_property_value(value, prop):
                    validation_details.append(
                        {
                            "field": prop_name,
                            "error": f"Value {value} does not match type {prop['type']}",
                        }
                    )

        return {
            "valid": is_valid,
            "ontology_class": ontology_class,
            "validation_details": validation_details,
            "timestamp": "2025-01-27T12:00:00Z",
        }

    def get_ontology_mapping(self, ontology_class: str) -> OntologySchemaMapping:
        """
        Get mapping between ontology and schema for a class

        Args:
            ontology_class: Name of the ontology class

        Returns:
            OntologySchemaMapping with schema fields and relationships
        """

        properties = self.ontology.get_class_properties(ontology_class)
        relationships = self.ontology.get_class_relationships(ontology_class)

        # Convert properties to schema fields
        schema_fields = {}
        for prop in properties:
            field = self._property_to_schema_field(prop)
            schema_fields[prop["name"]] = field

        # Create validation rules
        validation_rules = []
        for prop in properties:
            if prop.get("required", False):
                validation_rules.append(
                    {
                        "field": prop["name"],
                        "rule": "required",
                        "message": f"Field {prop['name']} is required",
                    }
                )

            if "min" in prop:
                validation_rules.append(
                    {
                        "field": prop["name"],
                        "rule": "min_value",
                        "value": prop["min"],
                        "message": f"Field {prop['name']} must be at least {prop['min']}",
                    }
                )

            if "max" in prop:
                validation_rules.append(
                    {
                        "field": prop["name"],
                        "rule": "max_value",
                        "value": prop["max"],
                        "message": f"Field {prop['name']} must be at most {prop['max']}",
                    }
                )

        return OntologySchemaMapping(
            ontology_class=ontology_class,
            schema_fields=schema_fields,
            relationships=relationships,
            validation_rules=validation_rules,
        )

    def _property_to_schema_field(self, prop: Dict[str, Any]) -> SchemaField:
        """Convert ontology property to schema field"""

        prop_type = prop["type"]
        field_type = self._map_ontology_type_to_schema_type(prop_type)

        return SchemaField(
            name=prop["name"],
            type=field_type,
            required=prop.get("required", False),
            description=prop.get("description", f"Property {prop['name']}"),
            default=prop.get("default"),
            enum_values=prop.get("values") if prop_type == "enum" else None,
            min_value=prop.get("min"),
            max_value=prop.get("max"),
        )

    def _relationship_to_schema_field(self, rel: Dict[str, Any]) -> SchemaField:
        """Convert ontology relationship to schema field"""

        return SchemaField(
            name=rel["name"],
            type=FieldType.ARRAY,
            required=False,
            description=f"Related {rel['target']} entities",
            default=[],
        )

    def _map_ontology_type_to_schema_type(self, ontology_type: str) -> FieldType:
        """Map ontology type to schema field type"""

        type_mapping = {
            "string": FieldType.STRING,
            "integer": FieldType.INTEGER,
            "float": FieldType.FLOAT,
            "boolean": FieldType.BOOLEAN,
            "array": FieldType.ARRAY,
            "object": FieldType.OBJECT,
            "enum": FieldType.ENUM,
        }

        return type_mapping.get(ontology_type, FieldType.STRING)

    def _validate_property_value(self, value: Any, prop: Dict[str, Any]) -> bool:
        """Validate property value against ontology definition"""

        prop_type = prop["type"]

        if prop_type == "string":
            return isinstance(value, str)
        elif prop_type == "integer":
            return isinstance(value, int)
        elif prop_type == "boolean":
            return isinstance(value, bool)
        elif prop_type == "array":
            return isinstance(value, list)
        elif prop_type == "enum":
            return value in prop.get("values", [])

        return True

    def _get_required_fields(self, ontology_class: str) -> List[str]:
        """Get required fields for ontology class"""
        properties = self.ontology.get_class_properties(ontology_class)
        return [prop["name"] for prop in properties if prop.get("required", False)]

    def _get_relationships(self, ontology_class: str) -> Dict[str, Any]:
        """Get relationships for ontology class"""
        relationships = self.ontology.get_class_relationships(ontology_class)
        return {rel["name"]: rel for rel in relationships}

    def _get_type_definitions(self, ontology_class: str) -> Dict[str, str]:
        """Get type definitions for ontology class"""
        properties = self.ontology.get_class_properties(ontology_class)
        return {prop["name"]: prop["type"] for prop in properties}


# Factory function for creating ontology providers
def create_ontology_provider(
    provider_type: str, config: Dict[str, Any]
) -> OntologyProvider:
    """Create ontology provider based on configuration"""

    if provider_type == "mock":
        return MockOntologyProvider()
    elif provider_type == "owl":
        # Would implement OWL/RDF integration
        raise NotImplementedError("OWL/RDF integration not yet implemented")
    elif provider_type == "neo4j":
        # Would implement Neo4j integration
        raise NotImplementedError("Neo4j integration not yet implemented")
    else:
        raise ValueError(f"Unknown ontology provider: {provider_type}")


def create_ontology_integration(
    provider_type: str = "mock", config: Optional[Dict[str, Any]] = None
) -> OntologyIntegration:
    """Create ontology integration with provider"""
    if config is None:
        config = {}

    provider = create_ontology_provider(provider_type, config)
    return OntologyIntegration(provider)
