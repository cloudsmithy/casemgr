# AWS Case Manager

跨平台 AWS Support 案例管理应用，支持桌面、Web 和移动端。

## 功能

- 🔐 AWS 凭证管理（支持 Profile 和手动输入）
- 📋 查看和筛选 Support 案例
- 💬 查看案例通信记录
- ✉️ 回复案例
- 📁 案例归档管理
- 🌐 离线模式支持

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
# 桌面应用
flet run src/main.py

# Web 应用
flet run src/main.py --web
```

## 打包

```bash
# Android APK
flet build apk src/main.py --project aws-case-manager

# iOS
flet build ipa src/main.py --project aws-case-manager

# macOS
flet build macos src/main.py --project aws-case-manager

# Windows
flet build windows src/main.py --project aws-case-manager
```

或使用 GitHub Actions 自动打包（推送代码后在 Actions 页面下载）。

## 配置 AWS 凭证

应用支持两种方式：

1. **AWS Profile** - 从 `~/.aws/credentials` 读取
2. **手动输入** - 直接输入 Access Key 和 Secret Key

## 技术栈

- [Flet](https://flet.dev/) - 跨平台 UI 框架
- [Boto3](https://boto3.amazonaws.com/) - AWS SDK
- Python 3.11+

## 项目结构

```
src/
├── main.py              # 应用入口
├── models/              # 数据模型
├── pages/               # 页面组件
├── components/          # UI 组件
└── services/            # 业务服务
```

## License

MIT
