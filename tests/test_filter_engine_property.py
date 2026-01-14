"""
Property-based tests for FilterEngine.

Feature: aws-case-manager
"""
from datetime import datetime
from hypothesis import given, strategies as st, settings

import sys
sys.path.insert(0, ".")

from src.models.case import Case, CaseStatus
from src.models.filters import Filters
from src.services.filter_engine import FilterEngine


# Strategies for generating test data
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

# Strategy for generating filter conditions
filters_strategy = st.builds(
    Filters,
    status=st.one_of(
        st.none(),
        st.lists(case_status_strategy, min_size=1, max_size=3, unique=True),
    ),
    severity=st.one_of(
        st.none(),
        st.lists(severity_code_strategy, min_size=1, max_size=3, unique=True),
    ),
    search_text=st.one_of(st.none(), st.text(min_size=0, max_size=50)),
    include_archived=st.booleans(),
    archived_only=st.booleans(),
)


def case_matches_filters(
    case: Case, filters: Filters, archived_case_ids: set[str]
) -> bool:
    """Helper function to check if a case matches all filter conditions."""
    # Check status filter
    if filters.status and case.status not in filters.status:
        return False

    # Check severity filter
    if filters.severity and case.severity_code not in filters.severity:
        return False

    # Check search text filter
    if filters.search_text and filters.search_text.strip():
        keyword_lower = filters.search_text.lower().strip()
        if keyword_lower not in case.subject.lower():
            return False

    # Check archive status filter
    is_archived = case.case_id in archived_case_ids
    if filters.archived_only and not is_archived:
        return False
    if not filters.include_archived and not filters.archived_only and is_archived:
        return False

    return True


@settings(max_examples=100)
@given(
    cases=st.lists(case_strategy, min_size=0, max_size=20),
    filters=filters_strategy,
    archived_ids=st.lists(
        st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        min_size=0,
        max_size=10,
    ),
)
def test_filter_correctness(
    cases: list[Case], filters: Filters, archived_ids: list[str]
):
    """
    Feature: aws-case-manager, Property 5: 过滤器正确性
    Validates: Requirements 4.1, 4.3, 4.5, 12.5
    
    For any case list and filter combination (status, severity, search keyword,
    archive status), every case in the filtered result should satisfy all
    specified filter conditions (AND logic).
    """
    archived_case_ids = set(archived_ids)
    engine = FilterEngine(archived_case_ids)
    
    result = engine.filter_cases(cases, filters)
    
    # Every case in result must match ALL filter conditions
    for case in result:
        assert case_matches_filters(case, filters, archived_case_ids), (
            f"Case {case.case_id} in result does not match filters: "
            f"status={filters.status}, severity={filters.severity}, "
            f"search_text={filters.search_text}, archived_only={filters.archived_only}, "
            f"include_archived={filters.include_archived}"
        )
    
    # Every case that matches filters should be in result
    for case in cases:
        if case_matches_filters(case, filters, archived_case_ids):
            assert case in result, (
                f"Case {case.case_id} matches filters but not in result"
            )



@settings(max_examples=100)
@given(
    cases=st.lists(case_strategy, min_size=0, max_size=20),
    keyword=st.text(min_size=1, max_size=30).filter(lambda x: x.strip()),
)
def test_search_result_correctness(cases: list[Case], keyword: str):
    """
    Feature: aws-case-manager, Property 6: 搜索结果正确性
    Validates: Requirements 4.2
    
    For any case list and search keyword, every case in the search result
    should have the keyword (case-insensitive) in its subject.
    """
    engine = FilterEngine()
    
    result = engine.search_cases(cases, keyword)
    keyword_lower = keyword.lower().strip()
    
    # Every case in result must contain the keyword in subject
    for case in result:
        assert keyword_lower in case.subject.lower(), (
            f"Case subject '{case.subject}' does not contain keyword '{keyword}'"
        )
    
    # Every case that contains the keyword should be in result
    for case in cases:
        if keyword_lower in case.subject.lower():
            assert case in result, (
                f"Case with subject '{case.subject}' contains keyword but not in result"
            )



@settings(max_examples=100)
@given(
    cases=st.lists(case_strategy, min_size=0, max_size=20),
    filters=filters_strategy,
)
def test_clear_filters_restores_full_list(cases: list[Case], filters: Filters):
    """
    Feature: aws-case-manager, Property 7: 清除过滤器恢复完整列表
    Validates: Requirements 4.4
    
    For any case list, applying filters then clearing all filter conditions
    should return the same result as the original list (excluding archived cases
    by default).
    """
    # Use empty archived set so archive filtering doesn't affect the test
    engine = FilterEngine(archived_case_ids=set())
    
    # Apply filters first
    filtered_result = engine.filter_cases(cases, filters)
    
    # Clear filters and apply again
    cleared_filters = engine.clear_filters()
    cleared_result = engine.filter_cases(cases, cleared_filters)
    
    # With no archived cases and cleared filters, result should equal original list
    assert len(cleared_result) == len(cases), (
        f"Cleared filter result has {len(cleared_result)} cases, "
        f"expected {len(cases)}"
    )
    
    # All original cases should be in the cleared result
    for case in cases:
        assert case in cleared_result, (
            f"Case {case.case_id} not in cleared filter result"
        )
