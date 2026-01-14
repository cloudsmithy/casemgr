"""
Property-based tests for ArchiveService.

Feature: aws-case-manager
"""
import os
import tempfile
from hypothesis import given, strategies as st, settings

import sys
sys.path.insert(0, ".")

from src.services.archive_service import ArchiveService


# Strategy for generating valid case IDs (non-empty strings)
case_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P")),
    min_size=1,
    max_size=50,
).filter(lambda x: x.strip())


@settings(max_examples=100)
@given(case_id=case_id_strategy)
def test_archive_toggle(case_id: str):
    """
    Feature: aws-case-manager, Property 12: 归档状态切换
    Validates: Requirements 12.1, 12.2, 12.4
    
    For any case, archiving it should make it appear as archived,
    and unarchiving it should restore it to non-archived state.
    """
    # Use a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        service = ArchiveService(db_path=db_path)
        
        # Initial state: not archived
        assert not service.is_archived(case_id), (
            f"Case {case_id} should not be archived initially"
        )
        
        # Archive the case (Requirement 12.1)
        service.archive_case(case_id)
        assert service.is_archived(case_id), (
            f"Case {case_id} should be archived after archive_case()"
        )
        
        # Verify it appears in archived case IDs (Requirement 12.2)
        archived_ids = service.get_archived_case_ids()
        assert case_id in archived_ids, (
            f"Case {case_id} should be in archived_case_ids after archiving"
        )
        
        # Unarchive the case (Requirement 12.4)
        service.unarchive_case(case_id)
        assert not service.is_archived(case_id), (
            f"Case {case_id} should not be archived after unarchive_case()"
        )
        
        # Verify it no longer appears in archived case IDs
        archived_ids = service.get_archived_case_ids()
        assert case_id not in archived_ids, (
            f"Case {case_id} should not be in archived_case_ids after unarchiving"
        )
    finally:
        # Clean up temporary database
        if os.path.exists(db_path):
            os.unlink(db_path)


@settings(max_examples=100)
@given(case_id=case_id_strategy)
def test_archive_idempotent(case_id: str):
    """
    Feature: aws-case-manager, Property 12: 归档状态切换 (幂等性)
    Validates: Requirements 12.1
    
    Archiving an already archived case should have no effect.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        service = ArchiveService(db_path=db_path)
        
        # Archive twice
        service.archive_case(case_id)
        service.archive_case(case_id)
        
        # Should still be archived
        assert service.is_archived(case_id), (
            f"Case {case_id} should remain archived after double archive"
        )
        
        # Should appear exactly once in archived IDs
        archived_ids = service.get_archived_case_ids()
        assert case_id in archived_ids, (
            f"Case {case_id} should be in archived_case_ids"
        )
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@settings(max_examples=100)
@given(case_id=case_id_strategy)
def test_unarchive_non_archived_case(case_id: str):
    """
    Feature: aws-case-manager, Property 12: 归档状态切换 (边界情况)
    Validates: Requirements 12.4
    
    Unarchiving a non-archived case should have no effect and not raise errors.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        service = ArchiveService(db_path=db_path)
        
        # Unarchive a case that was never archived
        service.unarchive_case(case_id)
        
        # Should still not be archived
        assert not service.is_archived(case_id), (
            f"Case {case_id} should not be archived after unarchiving non-archived case"
        )
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)



# Import additional dependencies for archive filter tests
from datetime import datetime
from src.models.case import Case, CaseStatus
from src.models.filters import Filters
from src.services.filter_engine import FilterEngine


# Strategies for generating case data
case_status_strategy = st.sampled_from(list(CaseStatus))

severity_code_strategy = st.sampled_from(["low", "normal", "high", "urgent", "critical"])

datetime_strategy = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 12, 31),
)

case_strategy = st.builds(
    Case,
    case_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    display_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    subject=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
    status=case_status_strategy,
    service_code=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    category_code=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    severity_code=severity_code_strategy,
    submitted_by=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    time_created=datetime_strategy,
    language=st.sampled_from(["zh", "en", "ja"]),
)


@settings(max_examples=100)
@given(
    cases=st.lists(case_strategy, min_size=1, max_size=20),
    archive_ratio=st.floats(min_value=0.0, max_value=1.0),
)
def test_archive_filter_correctness(cases: list[Case], archive_ratio: float):
    """
    Feature: aws-case-manager, Property 13: 归档过滤正确性
    Validates: Requirements 12.3, 12.5
    
    For any case list, when filter is set to show only archived cases,
    every case in the result should be in archived state.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        archive_service = ArchiveService(db_path=db_path)
        
        # Archive some cases based on the ratio
        num_to_archive = int(len(cases) * archive_ratio)
        archived_case_ids = set()
        
        for i, case in enumerate(cases):
            if i < num_to_archive:
                archive_service.archive_case(case.case_id)
                archived_case_ids.add(case.case_id)
        
        # Create filter engine with archived case IDs
        filter_engine = FilterEngine(archived_case_ids=archived_case_ids)
        
        # Test archived_only filter (Requirement 12.3)
        archived_only_filter = Filters(archived_only=True)
        archived_result = filter_engine.filter_cases(cases, archived_only_filter)
        
        # Every case in result should be archived
        for case in archived_result:
            assert case.case_id in archived_case_ids, (
                f"Case {case.case_id} in archived_only result is not archived"
            )
        
        # Every archived case should be in result
        for case in cases:
            if case.case_id in archived_case_ids:
                assert case in archived_result, (
                    f"Archived case {case.case_id} not in archived_only result"
                )
        
        # Test default filter (exclude archived) (Requirement 12.5)
        default_filter = Filters(include_archived=False, archived_only=False)
        default_result = filter_engine.filter_cases(cases, default_filter)
        
        # No archived case should be in default result
        for case in default_result:
            assert case.case_id not in archived_case_ids, (
                f"Archived case {case.case_id} should not be in default result"
            )
        
        # Every non-archived case should be in default result
        for case in cases:
            if case.case_id not in archived_case_ids:
                assert case in default_result, (
                    f"Non-archived case {case.case_id} not in default result"
                )
        
        # Test include_archived filter
        include_all_filter = Filters(include_archived=True)
        include_all_result = filter_engine.filter_cases(cases, include_all_filter)
        
        # All cases should be in result when include_archived is True
        assert len(include_all_result) == len(cases), (
            f"include_archived=True should return all {len(cases)} cases, "
            f"got {len(include_all_result)}"
        )
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@settings(max_examples=100)
@given(
    cases=st.lists(case_strategy, min_size=0, max_size=20),
    archived_ids=st.lists(
        st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        min_size=0,
        max_size=10,
        unique=True,
    ),
)
def test_archive_filter_with_external_ids(cases: list[Case], archived_ids: list[str]):
    """
    Feature: aws-case-manager, Property 13: 归档过滤正确性 (外部归档ID)
    Validates: Requirements 12.3, 12.5
    
    For any case list and set of archived IDs, the filter engine should
    correctly filter based on archive status.
    """
    archived_case_ids = set(archived_ids)
    filter_engine = FilterEngine(archived_case_ids=archived_case_ids)
    
    # Test archived_only filter
    archived_only_filter = Filters(archived_only=True)
    archived_result = filter_engine.filter_cases(cases, archived_only_filter)
    
    # Every case in result should have its ID in archived_case_ids
    for case in archived_result:
        assert case.case_id in archived_case_ids, (
            f"Case {case.case_id} in archived_only result is not in archived_case_ids"
        )
    
    # Test default filter (exclude archived)
    default_filter = Filters(include_archived=False, archived_only=False)
    default_result = filter_engine.filter_cases(cases, default_filter)
    
    # No case in result should have its ID in archived_case_ids
    for case in default_result:
        assert case.case_id not in archived_case_ids, (
            f"Case {case.case_id} in default result should not be archived"
        )
