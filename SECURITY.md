# Security Policy

## Supported Versions

| Version | Supported          |
|:--|:--|
| 0.1.x   | ✅                 |
| < 0.1   | ❌                 |

## Reporting a Vulnerability

**请勿在公开 issue 中报告安全漏洞。**

通过以下方式私下报告：

📧 邮件：[yhn0535@gmail.com](mailto:yhn0535@gmail.com)

请在邮件中包含：

1. 漏洞描述与影响范围
2. 复现步骤（PoC）
3. 建议的修复方案（可选）
4. 您的联系方式

## Response Timeline

- **48 小时内**：确认收到报告
- **7 天内**：评估严重程度并给出初步反馈
- **30 天内**：发布修复（视严重程度）

## Sensitive Data Policy

**本项目严禁提交以下内容**：

- ❌ API 密钥（任何供应商）
- ❌ 用户凭据
- ❌ 个人身份信息（PII）
- ❌ 大于 50MB 的本地数据集

请使用环境变量注入凭据（详见 [README.md](README.md) 配置章节）。

`.env` 文件已在 `.gitignore` 中，但仍请在每次提交前自查：

```bash
git diff --cached | grep -iE "api[_-]?key|secret|token|password"
```
