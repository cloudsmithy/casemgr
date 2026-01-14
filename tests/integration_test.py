"""集成测试 - 测试 AWS 凭证和 Support API"""
import sys
sys.path.insert(0, 'src')

from services.auth_service import AuthService
from services.aws_client_service import AWSClientService


def test_auth_service():
    """测试认证服务"""
    print("=" * 50)
    print("测试 AuthService")
    print("=" * 50)
    
    auth = AuthService()
    
    # 列出可用的 profiles
    profiles = auth.list_profiles()
    print(f"可用的 AWS Profiles: {profiles}")
    
    if not profiles:
        print("❌ 没有找到任何 AWS Profile")
        return None
    
    # 尝试使用 default profile
    profile = "default" if "default" in profiles else profiles[0]
    print(f"\n尝试使用 Profile: {profile}")
    
    success = auth.configure_from_profile(profile)
    if success:
        print(f"✅ Profile '{profile}' 配置成功")
        creds = auth.get_stored_credentials()
        print(f"   Region: {creds.region}")
        print(f"   Access Key: {creds.access_key_id[:8]}...")
        print(f"   Has Session Token: {bool(creds.session_token)}")
        return creds
    else:
        print(f"❌ Profile '{profile}' 配置失败")
        return None


def test_aws_client(credentials):
    """测试 AWS Support API 客户端"""
    print("\n" + "=" * 50)
    print("测试 AWSClientService")
    print("=" * 50)
    
    if not credentials:
        print("❌ 没有有效凭证，跳过测试")
        return
    
    try:
        client = AWSClientService(credentials)
        
        # 测试获取案例列表
        print("\n获取案例列表...")
        cases = client.describe_cases(include_resolved=False)
        print(f"✅ 获取到 {len(cases)} 个活跃案例")
        
        for case in cases[:3]:  # 只显示前3个
            print(f"   - [{case.status.value}] {case.subject[:40]}...")
        
        # 测试获取服务列表
        print("\n获取服务列表...")
        services = client.describe_services()
        print(f"✅ 获取到 {len(services)} 个服务")
        
        # 测试获取严重级别
        print("\n获取严重级别...")
        levels = client.describe_severity_levels()
        print(f"✅ 获取到 {len(levels)} 个严重级别")
        for level in levels:
            print(f"   - {level.code}: {level.name}")
            
    except Exception as e:
        print(f"❌ AWS API 调用失败: {e}")


def main():
    print("AWS Case Manager 集成测试")
    print("=" * 50)
    
    # 测试认证
    credentials = test_auth_service()
    
    # 测试 AWS 客户端
    test_aws_client(credentials)
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
