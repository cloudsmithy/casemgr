"""Authentication service for AWS credentials management."""
import asyncio
import configparser
import json
from pathlib import Path

import boto3
import flet as ft
from botocore.exceptions import ClientError, NoCredentialsError

from models.credentials import AWSCredentials

# Storage key for credentials (with app prefix to avoid conflicts)
STORAGE_KEY = "aws_case_manager.credentials"


class AuthService:
    """认证服务 - 管理 AWS 凭证的存储和验证"""

    def __init__(self, page: ft.Page | None = None):
        """Initialize the auth service."""
        self._credentials: AWSCredentials | None = None
        self._page = page

    def set_page(self, page: ft.Page):
        """Set the page for storage access."""
        self._page = page

    def configure(self, credentials: AWSCredentials) -> bool:
        """配置 AWS 凭证并存储。"""
        try:
            if not self._validate_credentials_with_aws(credentials):
                return False
            
            self._store_credentials(credentials)
            self._credentials = credentials
            return True
        except Exception:
            return False

    def configure_from_profile(self, profile_name: str) -> bool:
        """从 AWS Profile 配置凭证。"""
        try:
            session = boto3.Session(profile_name=profile_name)
            creds = session.get_credentials()
            if creds is None:
                return False
            
            frozen_credentials = creds.get_frozen_credentials()
            
            credentials = AWSCredentials(
                access_key_id=frozen_credentials.access_key,
                secret_access_key=frozen_credentials.secret_key,
                region=session.region_name or "us-east-1",
                session_token=frozen_credentials.token,
            )
            
            if not self._validate_credentials_with_aws(credentials):
                return False
            
            self._store_credentials(credentials)
            self._credentials = credentials
            return True
        except Exception as e:
            print(f"configure_from_profile error: {e}")
            return False

    def validate_credentials(self) -> bool:
        """验证当前存储的凭证有效性。"""
        credentials = self.get_stored_credentials()
        if credentials is None:
            return False
        return self._validate_credentials_with_aws(credentials)

    def get_stored_credentials(self) -> AWSCredentials | None:
        """获取存储的凭证。"""
        if self._credentials is not None:
            return self._credentials
        
        # Try to load from shared_preferences (sync wrapper)
        if self._page:
            try:
                # Run async in sync context
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Already in async context, can't use run_until_complete
                    return None
                stored_data = loop.run_until_complete(
                    self._page.shared_preferences.get(STORAGE_KEY)
                )
                if stored_data:
                    data = json.loads(stored_data)
                    self._credentials = AWSCredentials.from_dict(data)
                    return self._credentials
            except Exception as e:
                print(f"Error loading credentials: {e}")
        
        return None

    def clear_credentials(self) -> None:
        """清除存储的凭证。"""
        if self._page:
            try:
                loop = asyncio.get_event_loop()
                if not loop.is_running():
                    loop.run_until_complete(
                        self._page.shared_preferences.remove(STORAGE_KEY)
                    )
            except Exception:
                pass
        self._credentials = None

    def list_profiles(self) -> list[str]:
        """列出可用的 AWS Profiles。"""
        profiles = []
        
        credentials_path = Path.home() / ".aws" / "credentials"
        if credentials_path.exists():
            config = configparser.ConfigParser()
            config.read(credentials_path)
            profiles.extend(config.sections())
        
        config_path = Path.home() / ".aws" / "config"
        if config_path.exists():
            config = configparser.ConfigParser()
            config.read(config_path)
            for section in config.sections():
                if section.startswith("profile "):
                    profile_name = section[8:]
                    if profile_name not in profiles:
                        profiles.append(profile_name)
                elif section == "default" and "default" not in profiles:
                    profiles.append("default")
        
        return sorted(profiles)

    def _store_credentials(self, credentials: AWSCredentials) -> None:
        """Store credentials using Flet shared_preferences."""
        if self._page:
            try:
                data = json.dumps(credentials.to_dict())
                loop = asyncio.get_event_loop()
                if not loop.is_running():
                    loop.run_until_complete(
                        self._page.shared_preferences.set(STORAGE_KEY, data)
                    )
            except Exception as e:
                print(f"Warning: Could not store credentials: {e}")

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
            client.get_caller_identity()
            return True
        except (ClientError, NoCredentialsError) as e:
            print(f"Validation error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
