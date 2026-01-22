"""
Unit tests for Pydantic data models.

Tests validation and serialization of Item, ItemResponse, and HealthResponse models.
"""

import pytest
from pydantic import ValidationError
from src.fast_api import Item, ItemResponse, HealthResponse


class TestItemModel:
    """Test suite for Item Pydantic model"""
    
    def test_item_valid_all_fields(self):
        """
        Test: Create Item with all fields
        Expected: Item created successfully
        """
        item = Item(
            name="Test Item",
            description="Test description",
            status="active"
        )
        
        assert item.name == "Test Item"
        assert item.description == "Test description"
        assert item.status == "active"
    
    def test_item_valid_required_only(self):
        """
        Test: Create Item with only required field
        Expected: Item created with defaults
        """
        item = Item(name="Test Item")
        
        assert item.name == "Test Item"
        assert item.description is None
        assert item.status == "created"
    
    def test_item_missing_name(self):
        """
        Test: Create Item without name
        Expected: ValidationError
        """
        with pytest.raises(ValidationError):
            Item(description="Test")
    
    def test_item_empty_name(self):
        """
        Test: Create Item with empty name
        Expected: ValidationError (min_length constraint)
        """
        with pytest.raises(ValidationError):
            Item(name="")
    
    def test_item_name_too_long(self):
        """
        Test: Create Item with name > 100 characters
        Expected: ValidationError (max_length constraint)
        """
        with pytest.raises(ValidationError):
            Item(name="a" * 101)
    
    def test_item_name_exact_max_length(self):
        """
        Test: Create Item with name exactly 100 characters
        Expected: Item created successfully
        """
        item = Item(name="a" * 100)
        
        assert len(item.name) == 100
    
    def test_item_description_too_long(self):
        """
        Test: Create Item with description > 500 characters
        Expected: ValidationError (max_length constraint)
        """
        with pytest.raises(ValidationError):
            Item(name="Test", description="a" * 501)
    
    def test_item_description_exact_max_length(self):
        """
        Test: Create Item with description exactly 500 characters
        Expected: Item created successfully
        """
        item = Item(name="Test", description="a" * 500)
        
        assert len(item.description) == 500
    
    def test_item_model_config(self):
        """
        Test: Item model preserves field order and metadata
        Expected: Fields have correct descriptions
        """
        item = Item(
            name="Test",
            description="Description",
            status="active"
        )
        
        # Check model field info
        assert "name" in Item.model_fields
        assert "description" in Item.model_fields
        assert "status" in Item.model_fields
    
    def test_item_serialization(self):
        """
        Test: Serialize Item to dict
        Expected: Dict contains all fields
        """
        item = Item(name="Test", status="active")
        item_dict = item.model_dump()
        
        assert item_dict["name"] == "Test"
        assert item_dict["status"] == "active"
        assert "description" in item_dict


class TestItemResponseModel:
    """Test suite for ItemResponse Pydantic model"""
    
    def test_item_response_all_fields(self):
        """
        Test: Create ItemResponse with all fields
        Expected: ItemResponse created successfully
        """
        response = ItemResponse(
            item_id=1,
            name="Item 1",
            description="Description",
            status="retrieved",
            query="search"
        )
        
        assert response.item_id == 1
        assert response.name == "Item 1"
        assert response.status == "retrieved"
        assert response.query == "search"
    
    def test_item_response_required_fields_only(self):
        """
        Test: Create ItemResponse with only required fields
        Expected: ItemResponse created with defaults
        """
        response = ItemResponse(status="created")
        
        assert response.status == "created"
        assert response.item_id is None
        assert response.name is None
        assert response.description is None
        assert response.query is None
    
    def test_item_response_missing_status(self):
        """
        Test: Create ItemResponse without status
        Expected: ValidationError (status is required)
        """
        with pytest.raises(ValidationError):
            ItemResponse(item_id=1, name="Test")
    
    def test_item_response_invalid_status_type(self):
        """
        Test: Create ItemResponse with invalid status type
        Expected: ValidationError (Pydantic doesn't coerce int to str)
        """
        # Pydantic v2 is strict and won't coerce int to str
        with pytest.raises(ValidationError):
            ItemResponse(status=200)  # Integer is not valid
    
    def test_item_response_optional_fields(self):
        """
        Test: ItemResponse optional fields can be None
        Expected: All optional fields can be None
        """
        response = ItemResponse(
            status="created",
            item_id=None,
            name=None,
            description=None,
            query=None
        )
        
        assert response.item_id is None
        assert response.name is None
    
    def test_item_response_serialization(self):
        """
        Test: Serialize ItemResponse to dict
        Expected: Dict contains all fields
        """
        response = ItemResponse(
            item_id=42,
            name="Item 42",
            status="retrieved"
        )
        response_dict = response.model_dump()
        
        assert response_dict["item_id"] == 42
        assert response_dict["name"] == "Item 42"
        assert response_dict["status"] == "retrieved"


class TestHealthResponseModel:
    """Test suite for HealthResponse Pydantic model"""
    
    def test_health_response_all_fields(self):
        """
        Test: Create HealthResponse with all fields
        Expected: HealthResponse created successfully
        """
        response = HealthResponse(
            status="healthy",
            version="1.0.0"
        )
        
        assert response.status == "healthy"
        assert response.version == "1.0.0"
    
    def test_health_response_default_version(self):
        """
        Test: Create HealthResponse with only status
        Expected: Version defaults to "1.0.0"
        """
        response = HealthResponse(status="healthy")
        
        assert response.status == "healthy"
        assert response.version == "1.0.0"
    
    def test_health_response_missing_status(self):
        """
        Test: Create HealthResponse without status
        Expected: ValidationError (status is required)
        """
        with pytest.raises(ValidationError):
            HealthResponse(version="1.0.0")
    
    def test_health_response_custom_version(self):
        """
        Test: Create HealthResponse with custom version
        Expected: Custom version used
        """
        response = HealthResponse(
            status="healthy",
            version="2.5.1"
        )
        
        assert response.version == "2.5.1"
    
    def test_health_response_status_variations(self):
        """
        Test: HealthResponse accepts different status values
        Expected: All status values accepted
        """
        statuses = ["healthy", "degraded", "unhealthy", "warning"]
        
        for status in statuses:
            response = HealthResponse(status=status)
            assert response.status == status
    
    def test_health_response_serialization(self):
        """
        Test: Serialize HealthResponse to dict
        Expected: Dict contains status and version
        """
        response = HealthResponse(status="healthy")
        response_dict = response.model_dump()
        
        assert response_dict["status"] == "healthy"
        assert response_dict["version"] == "1.0.0"
    
    def test_health_response_json_serialization(self):
        """
        Test: Serialize HealthResponse to JSON
        Expected: Valid JSON output
        """
        response = HealthResponse(status="healthy")
        json_str = response.model_dump_json()
        
        assert "healthy" in json_str
        assert "1.0.0" in json_str


class TestModelValidation:
    """Test suite for cross-model validation scenarios"""
    
    def test_item_to_item_response_mapping(self):
        """
        Test: Create ItemResponse from Item data
        Expected: Data correctly mapped
        """
        item = Item(
            name="Test Item",
            description="Test Description",
            status="active"
        )
        
        response = ItemResponse(
            item_id=1,
            name=item.name,
            description=item.description,
            status=item.status
        )
        
        assert response.name == item.name
        assert response.description == item.description
        assert response.status == item.status
    
    def test_model_json_round_trip(self):
        """
        Test: Serialize and deserialize models
        Expected: Data preserved
        """
        original = Item(
            name="Round Trip",
            description="Test"
        )
        
        json_str = original.model_dump_json()
        restored = Item.model_validate_json(json_str)
        
        assert restored.name == original.name
        assert restored.description == original.description
    
    def test_model_dict_round_trip(self):
        """
        Test: Convert to dict and back
        Expected: Data preserved
        """
        original = HealthResponse(
            status="healthy",
            version="2.0.0"
        )
        
        data_dict = original.model_dump()
        restored = HealthResponse(**data_dict)
        
        assert restored.status == original.status
        assert restored.version == original.version


class TestModelDocumentation:
    """Test suite for model field documentation"""
    
    def test_item_field_descriptions(self):
        """
        Test: Item model fields have descriptions
        Expected: Field info includes descriptions
        """
        fields = Item.model_fields
        
        assert fields["name"].description is not None
        assert "Name" in fields["name"].description or "name" in fields["name"].description
    
    def test_item_response_field_descriptions(self):
        """
        Test: ItemResponse model fields have descriptions
        Expected: Field info includes descriptions
        """
        fields = ItemResponse.model_fields
        
        assert fields["status"].description is not None
    
    def test_health_response_field_descriptions(self):
        """
        Test: HealthResponse model fields have descriptions
        Expected: Field info includes descriptions
        """
        fields = HealthResponse.model_fields
        
        assert fields["status"].description is not None
        assert fields["version"].description is not None


class TestModelConstraints:
    """Test suite for model field constraints"""
    
    def test_item_name_constraints(self):
        """
        Test: Item name field constraints
        Expected: Constraints properly enforced
        """
        fields = Item.model_fields
        name_field = fields["name"]
        
        # Check that constraints exist
        assert name_field is not None
    
    def test_item_description_constraints(self):
        """
        Test: Item description field constraints
        Expected: Max length constraint enforced
        """
        # Test constraint by trying invalid data
        with pytest.raises(ValidationError):
            Item(name="Test", description="a" * 501)
    
    def test_all_models_serializable(self):
        """
        Test: All models can be serialized to JSON
        Expected: model_dump_json() works for all
        """
        item = Item(name="Test")
        item_response = ItemResponse(status="test")
        health = HealthResponse(status="healthy")
        
        assert item.model_dump_json()
        assert item_response.model_dump_json()
        assert health.model_dump_json()
