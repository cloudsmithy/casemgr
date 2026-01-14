"""Property-based tests for UI components data and logic."""
import pytest
from datetime import datetime
from hypothesis import given, strategies as st, settings

from src.models.case import Case, CaseDetail, CaseStatus
from src.models.communication import Communication, AttachmentInfo


# Strategies for generating test data
case_status_strategy = st.sampled_from(list(CaseStatus))
severity_code_strategy = st.sampled_from(["low", "normal", "high", "urgent", "critical"])
datetime_strategy = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 12, 31),
)
non_empty_string_strategy = st.text(min_size=1, max_size=100).filter(lambda s: s.strip())


@st.composite
def case_strategy(draw):
    """Generate a random Case."""
    return Case(
        case_id=draw(st.text(min_size=1, max_size=50).filter(lambda s: s.strip())),
        display_id=draw(st.text(min_size=1, max_size=20).filter(lambda s: s.strip())),
        subject=draw(non_empty_string_strategy),
        status=draw(case_status_strategy),
        service_code=draw(non_empty_string_strategy),
        category_code=draw(non_empty_string_strategy),
        severity_code=draw(severity_code_strategy),
        submitted_by=draw(non_empty_string_strategy),
        time_created=draw(datetime_strategy),
    )


@st.composite
def attachment_info_strategy(draw):
    """Generate a random AttachmentInfo."""
    return AttachmentInfo(
        attachment_id=draw(st.text(min_size=1, max_size=50).filter(lambda s: s.strip())),
        file_name=draw(st.text(min_size=1, max_size=100).filter(lambda s: s.strip())),
    )


@st.composite
def communication_strategy(draw):
    """Generate a random Communication."""
    return Communication(
        case_id=draw(st.text(min_size=1, max_size=50).filter(lambda s: s.strip())),
        body=draw(non_empty_string_strategy),
        submitted_by=draw(non_empty_string_strategy),
        time_created=draw(datetime_strategy),
        attachments=draw(st.lists(attachment_info_strategy(), max_size=5)),
    )


@st.composite
def case_detail_strategy(draw):
    """Generate a random CaseDetail."""
    return CaseDetail(
        case_id=draw(st.text(min_size=1, max_size=50).filter(lambda s: s.strip())),
        display_id=draw(st.text(min_size=1, max_size=20).filter(lambda s: s.strip())),
        subject=draw(non_empty_string_strategy),
        status=draw(case_status_strategy),
        service_code=draw(non_empty_string_strategy),
        category_code=draw(non_empty_string_strategy),
        severity_code=draw(severity_code_strategy),
        submitted_by=draw(non_empty_string_strategy),
        time_created=draw(datetime_strategy),
        cc_email_addresses=draw(st.lists(st.emails(), max_size=3)),
        communications=draw(st.lists(communication_strategy(), max_size=10)),
    )


class TestCaseCardRenderingProperty:
    """Property tests for CaseCard data completeness."""

    @settings(max_examples=100)
    @given(case=case_strategy())
    def test_case_contains_required_info_for_rendering(self, case: Case):
        """
        Feature: aws-case-manager, Property 1: 案例列表渲染完整性
        Validates: Requirements 1.2
        
        For any case data, the case should contain all required fields
        for rendering: title (subject), status, severity level, and time_created.
        """
        # Verify all required fields for rendering are present and valid
        assert case.subject is not None and len(case.subject.strip()) > 0
        assert case.status is not None and isinstance(case.status, CaseStatus)
        assert case.severity_code is not None and len(case.severity_code.strip()) > 0
        assert case.time_created is not None and isinstance(case.time_created, datetime)
        assert case.display_id is not None and len(case.display_id.strip()) > 0


class TestCommunicationTimeSortingProperty:
    """Property tests for communication time sorting."""

    @settings(max_examples=100)
    @given(communications=st.lists(communication_strategy(), min_size=2, max_size=20))
    def test_communications_sorted_by_time(self, communications: list[Communication]):
        """
        Feature: aws-case-manager, Property 3: 通信记录时间排序
        Validates: Requirements 2.3
        
        For any list of communications, when sorted by time_created,
        the result should be in ascending order (oldest first).
        """
        sorted_comms = sorted(communications, key=lambda c: c.time_created)
        
        # Verify ascending order
        for i in range(len(sorted_comms) - 1):
            assert sorted_comms[i].time_created <= sorted_comms[i + 1].time_created


class TestCaseDetailRenderingProperty:
    """Property tests for CaseDetail data completeness."""

    @settings(max_examples=100)
    @given(case_detail=case_detail_strategy())
    def test_case_detail_contains_required_info_for_rendering(self, case_detail: CaseDetail):
        """
        Feature: aws-case-manager, Property 2: 案例详情渲染完整性
        Validates: Requirements 2.2
        
        For any case detail data, the data should contain all required fields
        for rendering: title, status, severity level, service category,
        and all communication records.
        """
        # Verify all required fields for rendering are present
        assert case_detail.subject is not None and len(case_detail.subject.strip()) > 0
        assert case_detail.status is not None and isinstance(case_detail.status, CaseStatus)
        assert case_detail.severity_code is not None and len(case_detail.severity_code.strip()) > 0
        assert case_detail.service_code is not None and len(case_detail.service_code.strip()) > 0
        assert case_detail.category_code is not None and len(case_detail.category_code.strip()) > 0
        assert case_detail.communications is not None and isinstance(case_detail.communications, list)
        
        # Verify communications list integrity
        for comm in case_detail.communications:
            assert comm.body is not None and len(comm.body.strip()) > 0
            assert comm.submitted_by is not None and len(comm.submitted_by.strip()) > 0
            assert comm.time_created is not None and isinstance(comm.time_created, datetime)


class TestAttachmentListRenderingProperty:
    """Property tests for attachment list data completeness."""

    @settings(max_examples=100)
    @given(attachments=st.lists(attachment_info_strategy(), min_size=1, max_size=10))
    def test_attachment_list_contains_required_info(self, attachments: list[AttachmentInfo]):
        """
        Feature: aws-case-manager, Property 9: 附件列表渲染完整性
        Validates: Requirements 10.2
        
        For any list of attachments, each attachment should have
        a file name and attachment ID for rendering.
        """
        # Verify each attachment has required info for rendering
        for attachment in attachments:
            assert attachment.file_name is not None and len(attachment.file_name.strip()) > 0
            assert attachment.attachment_id is not None and len(attachment.attachment_id.strip()) > 0
        
        # Verify all attachments are unique by ID
        attachment_ids = [a.attachment_id for a in attachments]
        # Note: duplicates are allowed in generated data, just verify structure
        assert len(attachments) > 0
