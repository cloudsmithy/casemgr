"""Property-based tests for validation service."""
import pytest
from hypothesis import given, strategies as st, settings

from src.services.validation_service import (
    ValidationError,
    validate_create_case_form,
    validate_reply,
)
from src.models.case_params import CreateCaseParams


# Strategy for whitespace-only strings
whitespace_strategy = st.text(
    alphabet=" \t\n\r\v\f",
    min_size=0,
    max_size=20
)

# Strategy for non-empty, non-whitespace strings
non_empty_string_strategy = st.text(min_size=1).filter(lambda s: s.strip())


class TestValidateReplyProperty:
    """Property tests for validate_reply function."""

    @settings(max_examples=100)
    @given(body=whitespace_strategy)
    def test_whitespace_only_rejected(self, body: str):
        """
        Feature: aws-case-manager, Property 4: 空回复验证
        Validates: Requirements 3.3
        
        For any string composed entirely of whitespace characters,
        validate_reply should return False.
        """
        assert validate_reply(body) is False

    @settings(max_examples=100)
    @given(body=non_empty_string_strategy)
    def test_non_empty_accepted(self, body: str):
        """
        Feature: aws-case-manager, Property 4: 空回复验证 (inverse)
        Validates: Requirements 3.3
        
        For any string with non-whitespace content,
        validate_reply should return True.
        """
        assert validate_reply(body) is True

    def test_none_rejected(self):
        """None should be rejected."""
        assert validate_reply(None) is False


class TestValidateCreateCaseFormProperty:
    """Property tests for validate_create_case_form function."""

    @settings(max_examples=100)
    @given(
        subject=whitespace_strategy,
        service_code=non_empty_string_strategy,
        category_code=non_empty_string_strategy,
        severity_code=non_empty_string_strategy,
        communication_body=non_empty_string_strategy,
    )
    def test_empty_subject_rejected(
        self,
        subject: str,
        service_code: str,
        category_code: str,
        severity_code: str,
        communication_body: str,
    ):
        """
        Feature: aws-case-manager, Property 8: 案例创建表单验证
        Validates: Requirements 8.2
        
        Forms with empty/whitespace subject should be rejected.
        """
        params = CreateCaseParams(
            subject=subject,
            service_code=service_code,
            category_code=category_code,
            severity_code=severity_code,
            communication_body=communication_body,
        )
        errors = validate_create_case_form(params)
        assert any(e.field == "subject" for e in errors)

    @settings(max_examples=100)
    @given(
        subject=non_empty_string_strategy,
        service_code=whitespace_strategy,
        category_code=non_empty_string_strategy,
        severity_code=non_empty_string_strategy,
        communication_body=non_empty_string_strategy,
    )
    def test_empty_service_code_rejected(
        self,
        subject: str,
        service_code: str,
        category_code: str,
        severity_code: str,
        communication_body: str,
    ):
        """
        Feature: aws-case-manager, Property 8: 案例创建表单验证
        Validates: Requirements 8.2
        
        Forms with empty/whitespace service_code should be rejected.
        """
        params = CreateCaseParams(
            subject=subject,
            service_code=service_code,
            category_code=category_code,
            severity_code=severity_code,
            communication_body=communication_body,
        )
        errors = validate_create_case_form(params)
        assert any(e.field == "service_code" for e in errors)

    @settings(max_examples=100)
    @given(
        subject=non_empty_string_strategy,
        service_code=non_empty_string_strategy,
        category_code=non_empty_string_strategy,
        severity_code=whitespace_strategy,
        communication_body=non_empty_string_strategy,
    )
    def test_empty_severity_code_rejected(
        self,
        subject: str,
        service_code: str,
        category_code: str,
        severity_code: str,
        communication_body: str,
    ):
        """
        Feature: aws-case-manager, Property 8: 案例创建表单验证
        Validates: Requirements 8.2
        
        Forms with empty/whitespace severity_code should be rejected.
        """
        params = CreateCaseParams(
            subject=subject,
            service_code=service_code,
            category_code=category_code,
            severity_code=severity_code,
            communication_body=communication_body,
        )
        errors = validate_create_case_form(params)
        assert any(e.field == "severity_code" for e in errors)

    @settings(max_examples=100)
    @given(
        subject=non_empty_string_strategy,
        service_code=non_empty_string_strategy,
        category_code=non_empty_string_strategy,
        severity_code=non_empty_string_strategy,
        communication_body=whitespace_strategy,
    )
    def test_empty_communication_body_rejected(
        self,
        subject: str,
        service_code: str,
        category_code: str,
        severity_code: str,
        communication_body: str,
    ):
        """
        Feature: aws-case-manager, Property 8: 案例创建表单验证
        Validates: Requirements 8.2
        
        Forms with empty/whitespace communication_body should be rejected.
        """
        params = CreateCaseParams(
            subject=subject,
            service_code=service_code,
            category_code=category_code,
            severity_code=severity_code,
            communication_body=communication_body,
        )
        errors = validate_create_case_form(params)
        assert any(e.field == "communication_body" for e in errors)

    @settings(max_examples=100)
    @given(
        subject=non_empty_string_strategy,
        service_code=non_empty_string_strategy,
        category_code=non_empty_string_strategy,
        severity_code=non_empty_string_strategy,
        communication_body=non_empty_string_strategy,
    )
    def test_valid_form_accepted(
        self,
        subject: str,
        service_code: str,
        category_code: str,
        severity_code: str,
        communication_body: str,
    ):
        """
        Feature: aws-case-manager, Property 8: 案例创建表单验证 (inverse)
        Validates: Requirements 8.2
        
        Forms with all required fields filled should pass validation.
        """
        params = CreateCaseParams(
            subject=subject,
            service_code=service_code,
            category_code=category_code,
            severity_code=severity_code,
            communication_body=communication_body,
        )
        errors = validate_create_case_form(params)
        assert len(errors) == 0
