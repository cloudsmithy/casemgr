"""
Property-based tests for data models.

Feature: aws-case-manager, Property 11: 缓存数据往返
Validates: Requirements 11.1
"""
from datetime import datetime, timezone
from hypothesis import given, strategies as st, settings

import sys
sys.path.insert(0, ".")

from src.models.case import Case, CaseDetail, CaseStatus
from src.models.communication import Communication, AttachmentInfo
from src.models.filters import Filters
from src.models.credentials import AWSCredentials
from src.models.service import Service, Category, SeverityLevel
from src.models.case_params import CreateCaseParams


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
    body=st.text(min_size=0, max_size=1000),
    submitted_by=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    time_created=datetime_strategy,
    attachments=st.lists(attachment_info_strategy, max_size=5),
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
    cc_email_addresses=st.lists(st.emails(), max_size=5),
    communications=st.lists(communication_strategy, max_size=10),
)


@settings(max_examples=100)
@given(case=case_strategy)
def test_case_round_trip(case: Case):
    """
    Feature: aws-case-manager, Property 11: 缓存数据往返
    Validates: Requirements 11.1
    
    For any Case data, serializing to dict then deserializing should produce
    an equivalent Case object.
    """
    serialized = case.to_dict()
    deserialized = Case.from_dict(serialized)
    
    assert deserialized.case_id == case.case_id
    assert deserialized.display_id == case.display_id
    assert deserialized.subject == case.subject
    assert deserialized.status == case.status
    assert deserialized.service_code == case.service_code
    assert deserialized.category_code == case.category_code
    assert deserialized.severity_code == case.severity_code
    assert deserialized.submitted_by == case.submitted_by
    assert deserialized.time_created == case.time_created
    assert deserialized.language == case.language


@settings(max_examples=100)
@given(case_detail=case_detail_strategy)
def test_case_detail_round_trip(case_detail: CaseDetail):
    """
    Feature: aws-case-manager, Property 11: 缓存数据往返
    Validates: Requirements 11.1
    
    For any CaseDetail data, serializing to dict then deserializing should
    produce an equivalent CaseDetail object.
    """
    serialized = case_detail.to_dict()
    deserialized = CaseDetail.from_dict(serialized)
    
    assert deserialized.case_id == case_detail.case_id
    assert deserialized.display_id == case_detail.display_id
    assert deserialized.subject == case_detail.subject
    assert deserialized.status == case_detail.status
    assert deserialized.cc_email_addresses == case_detail.cc_email_addresses
    assert len(deserialized.communications) == len(case_detail.communications)
    
    for orig, deser in zip(case_detail.communications, deserialized.communications):
        assert deser.case_id == orig.case_id
        assert deser.body == orig.body
        assert deser.submitted_by == orig.submitted_by
        assert deser.time_created == orig.time_created
        assert len(deser.attachments) == len(orig.attachments)


@settings(max_examples=100)
@given(comm=communication_strategy)
def test_communication_round_trip(comm: Communication):
    """
    Feature: aws-case-manager, Property 11: 缓存数据往返
    Validates: Requirements 11.1
    
    For any Communication data, serializing to dict then deserializing should
    produce an equivalent Communication object.
    """
    serialized = comm.to_dict()
    deserialized = Communication.from_dict(serialized)
    
    assert deserialized.case_id == comm.case_id
    assert deserialized.body == comm.body
    assert deserialized.submitted_by == comm.submitted_by
    assert deserialized.time_created == comm.time_created
    assert len(deserialized.attachments) == len(comm.attachments)
    
    for orig, deser in zip(comm.attachments, deserialized.attachments):
        assert deser.attachment_id == orig.attachment_id
        assert deser.file_name == orig.file_name
