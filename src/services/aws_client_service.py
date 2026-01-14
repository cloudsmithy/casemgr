"""AWS Support API client service."""
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from models.case import Case, CaseDetail, CaseStatus
from models.case_params import CreateCaseParams
from models.communication import Attachment, AttachmentInfo, Communication
from models.credentials import AWSCredentials
from models.service import Category, Service, SeverityLevel


class AWSClientService:
    """AWS Support API 客户端服务"""

    def __init__(self, credentials: AWSCredentials):
        """
        Initialize the AWS client service.
        
        Args:
            credentials: AWS credentials for authentication
        """
        self._credentials = credentials
        kwargs = {
            "aws_access_key_id": credentials.access_key_id,
            "aws_secret_access_key": credentials.secret_access_key,
            "region_name": "us-east-1",  # AWS Support API only available in us-east-1
        }
        if credentials.session_token:
            kwargs["aws_session_token"] = credentials.session_token
        
        self._client = boto3.client("support", **kwargs)

    def describe_cases(self, include_resolved: bool = False) -> list[Case]:
        """
        获取案例列表。
        
        Args:
            include_resolved: 是否包含已解决的案例
            
        Returns:
            list[Case]: 案例列表
        """
        cases: list[Case] = []
        next_token: str | None = None
        
        while True:
            kwargs = {
                "includeResolvedCases": include_resolved,
                "includeCommunications": False,
            }
            if next_token:
                kwargs["nextToken"] = next_token
            
            response = self._client.describe_cases(**kwargs)
            
            for case_data in response.get("cases", []):
                cases.append(self._parse_case(case_data))
            
            next_token = response.get("nextToken")
            if not next_token:
                break
        
        return cases

    def describe_case(self, case_id: str) -> CaseDetail:
        """
        获取案例详情。
        
        Args:
            case_id: 案例 ID
            
        Returns:
            CaseDetail: 案例详情
            
        Raises:
            ClientError: 当案例不存在或 API 调用失败时
        """
        response = self._client.describe_cases(
            caseIdList=[case_id],
            includeCommunications=True,
        )
        
        if not response.get("cases"):
            raise ClientError(
                {"Error": {"Code": "CaseIdNotFound", "Message": f"Case {case_id} not found"}},
                "DescribeCases"
            )
        
        case_data = response["cases"][0]
        return self._parse_case_detail(case_data)

    def describe_services(self) -> list[Service]:
        """
        获取服务列表。
        
        Returns:
            list[Service]: 可用的 AWS 服务列表
        """
        response = self._client.describe_services()
        
        services: list[Service] = []
        for service_data in response.get("services", []):
            categories = [
                Category(code=cat["code"], name=cat["name"])
                for cat in service_data.get("categories", [])
            ]
            services.append(Service(
                code=service_data["code"],
                name=service_data["name"],
                categories=categories,
            ))
        
        return services

    def describe_severity_levels(self) -> list[SeverityLevel]:
        """
        获取严重级别列表。
        
        Returns:
            list[SeverityLevel]: 可用的严重级别列表
        """
        response = self._client.describe_severity_levels()
        
        return [
            SeverityLevel(code=level["code"], name=level["name"])
            for level in response.get("severityLevels", [])
        ]


    def _parse_case(self, case_data: dict) -> Case:
        """Parse AWS API case response into Case model."""
        return Case(
            case_id=case_data["caseId"],
            display_id=case_data["displayId"],
            subject=case_data["subject"],
            status=CaseStatus(case_data["status"]),
            service_code=case_data["serviceCode"],
            category_code=case_data["categoryCode"],
            severity_code=case_data["severityCode"],
            submitted_by=case_data["submittedBy"],
            time_created=datetime.fromisoformat(
                case_data["timeCreated"].replace("Z", "+00:00")
            ),
            language=case_data.get("language", "zh"),
        )

    def _parse_case_detail(self, case_data: dict) -> CaseDetail:
        """Parse AWS API case response into CaseDetail model."""
        communications: list[Communication] = []
        
        for comm_data in case_data.get("recentCommunications", {}).get("communications", []):
            attachments = [
                AttachmentInfo(
                    attachment_id=att["attachmentId"],
                    file_name=att["fileName"],
                )
                for att in comm_data.get("attachmentSet", [])
            ]
            communications.append(Communication(
                case_id=case_data["caseId"],
                body=comm_data["body"],
                submitted_by=comm_data["submittedBy"],
                time_created=datetime.fromisoformat(
                    comm_data["timeCreated"].replace("Z", "+00:00")
                ),
                attachments=attachments,
            ))
        
        return CaseDetail(
            case_id=case_data["caseId"],
            display_id=case_data["displayId"],
            subject=case_data["subject"],
            status=CaseStatus(case_data["status"]),
            service_code=case_data["serviceCode"],
            category_code=case_data["categoryCode"],
            severity_code=case_data["severityCode"],
            submitted_by=case_data["submittedBy"],
            time_created=datetime.fromisoformat(
                case_data["timeCreated"].replace("Z", "+00:00")
            ),
            language=case_data.get("language", "zh"),
            cc_email_addresses=case_data.get("ccEmailAddresses", []),
            communications=communications,
        )


    def create_case(self, params: CreateCaseParams) -> str:
        """
        创建新案例。
        
        Args:
            params: 创建案例的参数
            
        Returns:
            str: 新创建案例的 ID
            
        Raises:
            ClientError: 当 API 调用失败时
        """
        kwargs = {
            "subject": params.subject,
            "serviceCode": params.service_code,
            "categoryCode": params.category_code,
            "severityCode": params.severity_code,
            "communicationBody": params.communication_body,
            "language": params.language,
        }
        
        if params.cc_email_addresses:
            kwargs["ccEmailAddresses"] = params.cc_email_addresses
        
        if params.attachment_set_id:
            kwargs["attachmentSetId"] = params.attachment_set_id
        
        response = self._client.create_case(**kwargs)
        return response["caseId"]

    def add_communication(
        self, case_id: str, body: str, attachments: list[str] | None = None
    ) -> None:
        """
        添加回复到案例。
        
        Args:
            case_id: 案例 ID
            body: 回复内容
            attachments: 附件集 ID 列表（可选）
            
        Raises:
            ClientError: 当 API 调用失败时
        """
        kwargs = {
            "caseId": case_id,
            "communicationBody": body,
        }
        
        if attachments:
            kwargs["attachmentSetId"] = attachments[0]  # AWS API accepts single attachment set
        
        self._client.add_communication_to_case(**kwargs)

    def resolve_case(self, case_id: str) -> None:
        """
        关闭案例。
        
        Args:
            case_id: 案例 ID
            
        Raises:
            ClientError: 当 API 调用失败时
        """
        self._client.resolve_case(caseId=case_id)


    def describe_attachment(self, attachment_id: str) -> Attachment:
        """
        获取附件内容。
        
        Args:
            attachment_id: 附件 ID
            
        Returns:
            Attachment: 附件对象，包含文件名和二进制数据
            
        Raises:
            ClientError: 当 API 调用失败时
        """
        response = self._client.describe_attachment(attachmentId=attachment_id)
        
        attachment_data = response["attachment"]
        return Attachment(
            attachment_id=attachment_id,
            file_name=attachment_data["fileName"],
            data=attachment_data["data"],
        )

    def add_attachment(self, file_name: str, data: bytes) -> str:
        """
        上传附件并返回附件集 ID。
        
        Args:
            file_name: 文件名
            data: 文件二进制数据
            
        Returns:
            str: 附件集 ID，用于关联到案例或回复
            
        Raises:
            ClientError: 当 API 调用失败时
        """
        response = self._client.add_attachments_to_set(
            attachments=[
                {
                    "fileName": file_name,
                    "data": data,
                }
            ]
        )
        return response["attachmentSetId"]

    def add_attachments(self, attachments: list[tuple[str, bytes]]) -> str:
        """
        上传多个附件并返回附件集 ID。
        
        Args:
            attachments: 附件列表，每个元素为 (文件名, 二进制数据) 元组
            
        Returns:
            str: 附件集 ID，用于关联到案例或回复
            
        Raises:
            ClientError: 当 API 调用失败时
        """
        attachment_list = [
            {"fileName": name, "data": data}
            for name, data in attachments
        ]
        
        response = self._client.add_attachments_to_set(attachments=attachment_list)
        return response["attachmentSetId"]
