"""Validation service for form inputs."""
from dataclasses import dataclass

from models.case_params import CreateCaseParams


@dataclass
class ValidationError:
    """验证错误"""
    field: str
    message: str


def validate_create_case_form(data: CreateCaseParams) -> list[ValidationError]:
    """
    验证创建案例表单。
    
    检查必填字段：服务类别、严重级别、主题和描述。
    
    Args:
        data: 创建案例的参数
        
    Returns:
        验证错误列表，如果为空则表示验证通过
    """
    errors: list[ValidationError] = []
    
    if not data.subject or not data.subject.strip():
        errors.append(ValidationError("subject", "主题不能为空"))
    
    if not data.communication_body or not data.communication_body.strip():
        errors.append(ValidationError("communication_body", "描述不能为空"))
    
    if not data.service_code or not data.service_code.strip():
        errors.append(ValidationError("service_code", "请选择服务类别"))
    
    if not data.severity_code or not data.severity_code.strip():
        errors.append(ValidationError("severity_code", "请选择严重级别"))
    
    return errors


def validate_reply(body: str) -> bool:
    """
    验证回复内容。
    
    回复内容不能为空或仅包含空白字符。
    
    Args:
        body: 回复内容
        
    Returns:
        True 如果验证通过，False 如果验证失败
    """
    if body is None:
        return False
    return bool(body.strip())
