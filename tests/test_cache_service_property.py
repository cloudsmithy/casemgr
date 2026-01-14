"""
Property-based tests for CacheService.

Feature: aws-case-manager, Property 11: 缓存数据往返
Validates: Requirements 11.1, 11.2
"""
import os
import tempfile
from datetime import datetime
from hypothesis import given, strategies as st, settings

import sys
sys.path.insert(0, ".")

from src.models.case import Case, CaseDetail, CaseStatus
from src.models.communication import Communication, AttachmentInfo
from src.services.cache_service import CacheService


# Strategies for generating test data
case_status_strategy = st.sampled_from(list(CaseStatus))

datetime_strategy = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 12, 31),
)

attachment_info_strategy = st.builds(
    AttachmentInfo,
    attachment_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    file_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
)

communication_strategy = st.builds(
    Communication,
    case_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    body=st.text(min_size=0, max_size=500),
    submitted_by=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    time_created=datetime_strategy,
    attachments=st.lists(attachment_info_strategy, max_size=3),
)

case_strategy = st.builds(
    Case,
    case_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    display_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    subject=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
    status=case_status_strategy,
    service_code=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    category_code=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    severity_code=st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
    submitted_by=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    time_created=datetime_strategy,
    language=st.sampled_from(["zh", "en", "ja"]),
)

case_detail_strategy = st.builds(
    CaseDetail,
    case_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    display_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    subject=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
    status=case_status_strategy,
    service_code=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    category_code=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    severity_code=st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
    submitted_by=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    time_created=datetime_strategy,
    language=st.sampled_from(["zh", "en", "ja"]),
    cc_email_addresses=st.lists(st.emails(), max_size=3),
    communications=st.lists(communication_strategy, max_size=5),
)


@settings(max_examples=100)
@given(cases=st.lists(case_strategy, min_size=1, max_size=10))
def test_cache_cases_round_trip(cases: list[Case]):
    """
    Feature: aws-case-manager, Property 11: 缓存数据往返
    Validates: Requirements 11.1, 11.2
    
    For any list of Case data, saving to cache then retrieving should
    produce equivalent Case objects. Duplicate case_ids will be deduplicated
    (last one wins).
    """
    # Use a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        service = CacheService(db_path=db_path)
        
        # Save cases to cache
        service.save_cases(cases)
        
        # Retrieve cached cases
        cached = service.get_cached_cases()
        
        # Build expected map (last case with each ID wins due to INSERT OR REPLACE)
        expected_by_id = {}
        for c in cases:
            expected_by_id[c.case_id] = c
        
        # Verify count matches unique case_ids
        assert len(cached) == len(expected_by_id)
        
        for cached_case in cached:
            assert cached_case.case_id in expected_by_id
            orig = expected_by_id[cached_case.case_id]
            assert cached_case.display_id == orig.display_id
            assert cached_case.subject == orig.subject
            assert cached_case.status == orig.status
            assert cached_case.service_code == orig.service_code
            assert cached_case.severity_code == orig.severity_code
        
        # Verify last sync time is set
        sync_time = service.get_last_sync_time()
        assert sync_time is not None
    finally:
        os.unlink(db_path)


@settings(max_examples=100)
@given(case_detail=case_detail_strategy)
def test_cache_case_detail_round_trip(case_detail: CaseDetail):
    """
    Feature: aws-case-manager, Property 11: 缓存数据往返
    Validates: Requirements 11.1, 11.2
    
    For any CaseDetail data, saving to cache then retrieving should
    produce an equivalent CaseDetail object.
    """
    # Use a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        service = CacheService(db_path=db_path)
        
        # Save case detail to cache
        service.save_case_detail(case_detail.case_id, case_detail)
        
        # Retrieve cached case detail
        cached = service.get_cached_case_detail(case_detail.case_id)
        
        # Verify it was retrieved
        assert cached is not None
        
        # Verify fields match
        assert cached.case_id == case_detail.case_id
        assert cached.display_id == case_detail.display_id
        assert cached.subject == case_detail.subject
        assert cached.status == case_detail.status
        assert cached.service_code == case_detail.service_code
        assert cached.severity_code == case_detail.severity_code
        assert cached.cc_email_addresses == case_detail.cc_email_addresses
        assert len(cached.communications) == len(case_detail.communications)
        
        # Verify communications
        for orig, deser in zip(case_detail.communications, cached.communications):
            assert deser.case_id == orig.case_id
            assert deser.body == orig.body
            assert deser.submitted_by == orig.submitted_by
    finally:
        os.unlink(db_path)


def test_get_cached_case_detail_not_found():
    """
    Test that get_cached_case_detail returns None for non-existent case.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        service = CacheService(db_path=db_path)
        result = service.get_cached_case_detail("non-existent-id")
        assert result is None
    finally:
        os.unlink(db_path)


def test_get_last_sync_time_initially_none():
    """
    Test that get_last_sync_time returns None when no sync has occurred.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        service = CacheService(db_path=db_path)
        result = service.get_last_sync_time()
        assert result is None
    finally:
        os.unlink(db_path)


def test_clear_cache():
    """
    Test that clear_cache removes all cached data.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        service = CacheService(db_path=db_path)
        
        # Create a test case
        case = Case(
            case_id="test-123",
            display_id="DISP-123",
            subject="Test Subject",
            status=CaseStatus.OPENED,
            service_code="ec2",
            category_code="general",
            severity_code="low",
            submitted_by="user@example.com",
            time_created=datetime(2024, 1, 1),
            language="en",
        )
        
        # Save and verify
        service.save_cases([case])
        assert len(service.get_cached_cases()) == 1
        assert service.get_last_sync_time() is not None
        
        # Clear and verify
        service.clear_cache()
        assert len(service.get_cached_cases()) == 0
        assert service.get_last_sync_time() is None
    finally:
        os.unlink(db_path)
