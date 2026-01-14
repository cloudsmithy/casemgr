"""Authentication service for AWS credentials management."""
import configparser
import json
import os
from pathlib import Path

import boto3
import keyring
from botocore.exceptions import ClientError, NoCredentialsError

from models.credentials import AWSCredentials

# Keyring service name for storing credentials
KEYRING_SERVICE = "aws-case-manager"
KEYRING_USERNAME = "aws-credentials"


class AuthService:
    """认证服务 - 管理 AWS 凭证的存储和验证"""

    def __init__(self):
        """Initialize the auth service."""
        self._credentials: AWSCredentials | None = None

    def configure(self, credentials: AWSCredentials) -> bool:
        """
        配置 AWS 凭证并安全存储。
        
        Args:
            credentials: AWS 凭证对象
            
        Returns:
            bool: 配置是否成功
        """
        try:
            # Validate credentials before storing
            if not self._validate_credentials_with_aws(credentials):
                return False
            
            # Store credentials securely using keyring
            self._store_credentials(credentials)
            self._credentials = credentials
            return True
        except Exception:
            return False

    def configure_from_profile(self, profile_name: str) -> bool:
        """
        从 AWS Profile 配置凭证。
        
        Args:
            profile_name: AWS profile 名称
            
        Returns:
            bool: 配置是否成功
        """
        try:
            # Create a session with the specified profile
            session = boto3.Session(profile_name=profile_name)
            creds = session.get_credentials()
            if creds is None:
                return False
            
            frozen_credentials = creds.get_frozen_credentials()
            
            credentials = AWSCredentials(
                access_key_id=frozen_credentials.access_key,
                secret_access_key=frozen_credentials.secret_key,
                region=session.region_name or "us-east-1",
                session_token=frozen_credentials.token,  # 支持临时凭证
            )
            
            # Validate and store
            if not self._validate_credentials_with_aws(credentials):
                return False
            
            self._store_credentials(credentials)
            self._credentials = credentials
            return True
        except Exception as e:
            print(f"configure_from_profile error: {e}")  # 调试用
            return False

    def validate_credentials(self) -> bool:
        """
        验证当前存储的凭证有效性。
        
        Returns:
            bool: 凭证是否有效
        """
        credentials = self.get_stored_credentials()
        if credentials is None:
            return False
        return self._validate_credentials_with_aws(credentials)

    def get_stored_credentials(self) -> AWSCredentials | None:
        """
        获取存储的凭证。
        
        Returns:
            AWSCredentials | None: 存储的凭证，如果不存在则返回 None
        """
        if self._credentials is not None:
            return self._credentials
        
        try:
            stored_data = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
            if stored_data is None:
                return None
            
            data = json.loads(stored_data)
            self._credentials = AWSCredentials.from_dict(data)
            return self._credentials
        except Exception:
            return None

    def clear_credentials(self) -> None:
        """清除存储的凭证。"""
        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
        except keyring.errors.PasswordDeleteError:
            pass  # Password doesn't exist, ignore
        self._credentials = None

    def list_profiles(self) -> list[str]:
        """
        列出可用的 AWS Profiles。
        
        Returns:
            list[str]: 可用的 profile 名称列表
        """
        profiles = []
        
        # Check AWS credentials file
        credentials_path = Path.home() / ".aws" / "credentials"
        if credentials_path.exists():
            config = configparser.ConfigParser()
            config.read(credentials_path)
            profiles.extend(config.sections())
        
        # Check AWS config file for additional profiles
        config_path = Path.home() / ".aws" / "config"
        if config_path.exists():
            config = configparser.ConfigParser()
            config.read(config_path)
            for section in config.sections():
                # Config file uses "profile xxx" format
                if section.startswith("profile "):
                    profile_name = section[8:]  # Remove "profile " prefix
                    if profile_name not in profiles:
                        profiles.append(profile_name)
                elif section == "default" and "default" not in profiles:
                    profiles.append("default")
        
        return sorted(profiles)

    def _store_credentials(self, credentials: AWSCredentials) -> None:
        """Store credentials securely using keyring."""
        try:
            data = json.dumps(credentials.to_dict())
            keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, data)
        except Exception as e:
            # Keyring may fail in headless environments, just keep in memory
            print(f"Warning: Could not store credentials in keyring: {e}")
            pass

    def _validate_credentials_with_aws(self, credentials: AWSCredentials) -> bool:
        """Validate credentials by making an AWS API call."""
        try:
            kwargs = {
                "aws_access_key_id": credentials.access_key_id,
                "aws_secret_access_key": credentials.secret_access_key,
                "region_name": credentials.region,
            }
            if credentials.session_token:
                kwargs["aws_session_token"] = credentials.session_token
            
            client = boto3.client("sts", **kwargs)
            # Use get_caller_identity to validate credentials
            client.get_caller_identity()
            return True
        except (ClientError, NoCredentialsError) as e:
            print(f"Validation error: {e}")  # 调试用
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")  # 调试用
            return False
