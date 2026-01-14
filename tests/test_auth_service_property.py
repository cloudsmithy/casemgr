"""
Property-based tests for AuthService credentials persistence.

Feature: aws-case-manager, Property 10: 凭证持久化往返
Validates: Requirements 6.2, 6.5
"""
import json
from unittest.mock import patch, MagicMock

from hypothesis import given, strategies as st, settings

import sys
sys.path.insert(0, ".")

from src.models.credentials import AWSCredentials
from src.services.auth_service import AuthService, KEYRING_SERVICE, KEYRING_USERNAME


# Strategy for generating valid AWS credentials
# AWS access keys are typically 20 characters, secret keys are 40 characters
aws_credentials_strategy = st.builds(
    AWSCredentials,
    access_key_id=st.text(
        alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
        min_size=16,
        max_size=128,
    ).filter(lambda x: len(x) >= 16),
    secret_access_key=st.text(
        alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/"),
        min_size=32,
        max_size=128,
    ).filter(lambda x: len(x) >= 32),
    region=st.sampled_from([
        "us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1",
        "ap-southeast-1", "eu-central-1", "sa-east-1"
    ]),
)


@settings(max_examples=100)
@given(credentials=aws_credentials_strategy)
def test_credentials_persistence_round_trip(credentials: AWSCredentials):
    """
    Feature: aws-case-manager, Property 10: 凭证持久化往返
    Validates: Requirements 6.2, 6.5
    
    For any valid AWS credentials, storing then retrieving should produce
    equivalent credentials.
    """
    stored_data = {}
    
    def mock_set_password(service, username, password):
        stored_data[(service, username)] = password
    
    def mock_get_password(service, username):
        return stored_data.get((service, username))
    
    def mock_delete_password(service, username):
        if (service, username) in stored_data:
            del stored_data[(service, username)]
    
    with patch('src.services.auth_service.keyring.set_password', side_effect=mock_set_password), \
         patch('src.services.auth_service.keyring.get_password', side_effect=mock_get_password), \
         patch('src.services.auth_service.keyring.delete_password', side_effect=mock_delete_password):
        
        auth_service = AuthService()
        
        # Store credentials directly (bypassing AWS validation for this test)
        auth_service._store_credentials(credentials)
        auth_service._credentials = None  # Clear in-memory cache to force read from storage
        
        # Retrieve credentials
        retrieved = auth_service.get_stored_credentials()
        
        # Verify round-trip
        assert retrieved is not None
        assert retrieved.access_key_id == credentials.access_key_id
        assert retrieved.secret_access_key == credentials.secret_access_key
        assert retrieved.region == credentials.region


@settings(max_examples=100)
@given(credentials=aws_credentials_strategy)
def test_credentials_clear_removes_stored_data(credentials: AWSCredentials):
    """
    Feature: aws-case-manager, Property 10: 凭证持久化往返
    Validates: Requirements 6.2, 6.5
    
    For any stored credentials, clearing should remove them completely.
    """
    stored_data = {}
    
    def mock_set_password(service, username, password):
        stored_data[(service, username)] = password
    
    def mock_get_password(service, username):
        return stored_data.get((service, username))
    
    def mock_delete_password(service, username):
        if (service, username) in stored_data:
            del stored_data[(service, username)]
        else:
            raise Exception("Password not found")
    
    with patch('src.services.auth_service.keyring.set_password', side_effect=mock_set_password), \
         patch('src.services.auth_service.keyring.get_password', side_effect=mock_get_password), \
         patch('src.services.auth_service.keyring.delete_password', side_effect=mock_delete_password):
        
        auth_service = AuthService()
        
        # Store credentials
        auth_service._store_credentials(credentials)
        auth_service._credentials = credentials
        
        # Clear credentials
        auth_service.clear_credentials()
        
        # Verify credentials are cleared
        assert auth_service._credentials is None
        retrieved = auth_service.get_stored_credentials()
        assert retrieved is None


@settings(max_examples=100)
@given(credentials=aws_credentials_strategy)
def test_credentials_serialization_preserves_all_fields(credentials: AWSCredentials):
    """
    Feature: aws-case-manager, Property 10: 凭证持久化往返
    Validates: Requirements 6.2, 6.5
    
    For any credentials, JSON serialization should preserve all fields.
    """
    # Serialize to dict then to JSON (as done in keyring storage)
    serialized = json.dumps(credentials.to_dict())
    
    # Deserialize
    deserialized_dict = json.loads(serialized)
    restored = AWSCredentials.from_dict(deserialized_dict)
    
    # Verify all fields match
    assert restored.access_key_id == credentials.access_key_id
    assert restored.secret_access_key == credentials.secret_access_key
    assert restored.region == credentials.region
