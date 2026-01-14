"""Filter engine for case filtering and searching."""
from models.case import Case, CaseStatus
from models.filters import Filters


class FilterEngine:
    """过滤引擎 - 用于筛选和搜索案例"""

    def __init__(self, archived_case_ids: set[str] | None = None):
        """
        Initialize FilterEngine.
        
        Args:
            archived_case_ids: Set of case IDs that are archived.
                              If None, archive filtering is disabled.
        """
        self._archived_case_ids = archived_case_ids or set()

    def set_archived_case_ids(self, archived_case_ids: set[str]) -> None:
        """Update the set of archived case IDs."""
        self._archived_case_ids = archived_case_ids

    def is_archived(self, case_id: str) -> bool:
        """Check if a case is archived."""
        return case_id in self._archived_case_ids

    def filter_cases(self, cases: list[Case], filters: Filters) -> list[Case]:
        """
        根据过滤条件筛选案例。
        
        使用 AND 逻辑组合所有过滤条件。
        
        Args:
            cases: 案例列表
            filters: 过滤条件
            
        Returns:
            满足所有过滤条件的案例列表
        """
        result = cases

        # 状态过滤 (Requirement 4.1)
        if filters.status:
            result = [c for c in result if c.status in filters.status]

        # 严重级别过滤 (Requirement 4.3)
        if filters.severity:
            result = [c for c in result if c.severity_code in filters.severity]

        # 搜索关键词过滤 (Requirement 4.2)
        if filters.search_text:
            result = self.search_cases(result, filters.search_text)

        # 归档状态过滤 (Requirement 12.5)
        result = self._filter_by_archive_status(result, filters)

        return result

    def search_cases(self, cases: list[Case], keyword: str) -> list[Case]:
        """
        在案例标题和描述中搜索关键词。
        
        搜索不区分大小写。
        
        Args:
            cases: 案例列表
            keyword: 搜索关键词
            
        Returns:
            标题或描述包含关键词的案例列表
        """
        if not keyword or not keyword.strip():
            return cases

        keyword_lower = keyword.lower().strip()
        result = []

        for case in cases:
            # 在标题中搜索
            if keyword_lower in case.subject.lower():
                result.append(case)
            # Note: Case model doesn't have description field directly,
            # but subject serves as the main searchable text field
            # For CaseDetail, communications would contain the description

        return result

    def _filter_by_archive_status(
        self, cases: list[Case], filters: Filters
    ) -> list[Case]:
        """
        根据归档状态过滤案例。
        
        Args:
            cases: 案例列表
            filters: 过滤条件
            
        Returns:
            满足归档状态条件的案例列表
        """
        # 仅显示已归档案例 (Requirement 12.3)
        if filters.archived_only:
            return [c for c in cases if self.is_archived(c.case_id)]

        # 包含已归档案例
        if filters.include_archived:
            return cases

        # 默认：不显示已归档案例 (Requirement 12.2)
        return [c for c in cases if not self.is_archived(c.case_id)]

    def clear_filters(self) -> Filters:
        """
        返回清除所有过滤条件后的默认过滤器。
        
        Returns:
            默认过滤条件（无任何过滤）
        """
        return Filters(
            status=None,
            severity=None,
            search_text=None,
            include_archived=False,
            archived_only=False,
        )
