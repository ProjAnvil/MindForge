# Skill 编写最佳实践

本文档提供编写高质量 Skill 的指导原则和最佳实践。

## Frontmatter 要求

### name（技能名称）

- **格式**: 只能使用小写字母、数字和连字符
- **长度**: 最多 64 个字符
- **示例**:
  - ✅ `pdf-processing`
  - ✅ `git-commit-helper`
  - ✅ `code-reviewer`
  - ❌ `PDF Processing`（包含空格和大写字母）
  - ❌ `技能名称`（使用中文字符）

### description（技能描述）

- **格式**: 简洁描述技能功能和使用时机
- **长度**: 最多 1024 个字符
- **必须包含**:
  1. 技能做什么（能力）
  2. 何时使用（触发场景）
- **示例**:

**❌ 太模糊**:
```yaml
description: 帮助处理文档
```

**✅ 具体明确**:
```yaml
description: 从 PDF 文件中提取文本和表格、填写表单、合并文档。当处理 PDF 文件、用户提到 PDF、表单或文档提取时使用。
```

### allowed-tools（可选）

- **格式**: 逗号分隔的工具列表
- **用途**: 限制 Claude 在使用此技能时可以访问的工具
- **何时使用**:
  - 只读技能（如文件阅读器）
  - 特定范围的技能（如数据分析，不需要文件写入）
  - 安全敏感的工作流
- **示例**:

```yaml
# 只读技能
allowed-tools: Read, Grep, Glob

# 完整访问权限
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
```

## 描述编写技巧

### 1. 具体化触发词

帮助 Claude 发现何时使用技能，在描述中包含具体的触发词：

**好的描述示例**:
```yaml
description: |
  分析 Excel 电子表格，创建数据透视表，生成图表。
  当处理 Excel 文件、电子表格、.xlsx 格式的表格数据分析时使用。
```

### 2. 包含关键场景

明确列出技能适用的具体场景：

```yaml
description: |
  Git 提交消息生成技能。
  用于编写提交信息、审查暂存的更改、格式化提交历史。
  当用户提到：commit、提交、git diff、暂存区时使用。
```

### 3. 避免歧义

确保描述不会与其他技能混淆：

**❌ 容易混淆**:
```yaml
# Skill 1
description: 数据分析技能

# Skill 2
description: 分析数据的技能
```

**✅ 明确区分**:
```yaml
# Skill 1
description: |
  分析 Excel 文件中的销售数据和 CRM 导出数据。
  用于销售报告、管道分析和收入跟踪。

# Skill 2
description: |
  分析日志文件和系统指标数据。
  用于性能监控、调试和系统诊断。
```

## 内容组织

### 推荐结构

```markdown
---
name: your-skill
description: 技能描述
---

# 技能名称

## 指令
清晰的步骤说明

## 此技能的功能
核心能力说明

## 何时使用此技能
具体场景和触发条件

## 示例
具体的示例

## 最佳实践
推荐做法

## 备注
重要注意事项
```

### 编写原则

1. **保持专注**: 一个技能应该专注于一件事
2. **提供示例**: 使用具体的示例来说明用法
3. **渐进式披露**: 主要内容放在 SKILL.md，详细信息放在辅助文件
4. **清晰简洁**: 避免冗余，直击要点

## 辅助文件

### 使用场景

当 SKILL.md 变得过长时，可以考虑创建辅助文件：

```
my-skill/
├── SKILL.md           # 主要内容（必需）
├── examples.md        # 示例集合
├── reference.md       # 详细参考
└── scripts/
    └── helper.py      # 工具脚本
```

### 引用方式

在 SKILL.md 中引用辅助文件：

```markdown
## 详细说明

请参阅 [reference.md](reference.md) 了解完整的 API 文档。

## 运行脚本

```bash
python scripts/helper.py input.txt
```
```

## 测试和调试

### 测试 Checklist

- [ ] 描述具体且明确（包含能力和触发场景）
- [ ] name 符合命名规范（小写、数字、连字符）
- [ ] YAML frontmatter 语法正确
- [ ] 文件路径正确
  - 个人技能: `~/.claude/skills/skill-name/SKILL.md`
  - 项目技能: `.claude/skills/skill-name/SKILL.md`
- [ ] 包含具体示例

### 调试技巧

如果 Claude 没有使用你的技能：

1. **检查描述是否具体**
   - 是否包含"做什么"？
   - 是否包含"何时使用"？
   - 是否有明确的触发词？

2. **验证 YAML 语法**
   ```bash
   cat SKILL.md | head -n 10
   ```
   - 确保有开头和结尾的 `---`
   - 不要使用 Tab，使用空格缩进
   - 特殊字符需要加引号

3. **查看错误日志**
   ```bash
   # 启动 Claude Code 时查看技能加载错误
   claude --debug
   ```

## 示例对比

### 简单技能

**提交消息生成器**:

```markdown
---
name: git-commit-helper
description: 从 git diff 生成清晰的提交消息。当编写提交消息或审查暂存的更改时使用。
---

# Git 提交消息助手

## 指令

1. 运行 `git diff --staged` 查看更改
2. 我会建议包含以下内容的提交消息：
   - 50 字符以内的摘要
   - 详细描述
   - 受影响的组件

## 最佳实践

- 使用现在时态
- 说明做什么和为什么，而不是怎么做
```

### 带工具限制的技能

```markdown
---
name: code-reviewer
description: 审查代码的最佳实践和潜在问题。用于代码审查、检查 PR 或分析代码质量。
allowed-tools: Read, Grep, Glob
---

# 代码审查器

## 审查清单

1. 代码组织和结构
2. 错误处理
3. 性能考虑
4. 安全问题
5. 测试覆盖率

## 指令

1. 使用 Read 工具读取目标文件
2. 使用 Grep 搜索特定模式
3. 使用 Glob 查找相关文件
4. 提供详细的代码质量反馈
```

### 多文件技能

```
pdf-processing/
├── SKILL.md
├── FORMS.md
├── REFERENCE.md
└── scripts/
    ├── fill_form.py
    └── validate.py
```

**SKILL.md**:
```markdown
---
name: pdf-processing
description: 提取文本、填写表单、合并 PDF。用于处理 PDF 文件、表单或文档提取。需要 pypdf 和 pdfplumber 包。
---

# PDF 处理

## 快速开始

提取文本：
```python
import pdfplumber
with pdfplumber.open("doc.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

表单填写请参阅 [FORMS.md](FORMS.md)。
详细 API 参考请参阅 [REFERENCE.md](REFERENCE.md)。

## 依赖

需要在环境中安装以下包：
```bash
pip install pypdf pdfplumber
```
```

## 常见错误

### 错误 1: 描述太模糊

**问题**:
```yaml
description: 帮助编写代码
```

**修复**:
```yaml
description: |
  编写 Python 代码，实现 RESTful API，使用 FastAPI。
  当用户提到 Python、API、后端开发、FastAPI 时使用。
```

### 错误 2: name 格式错误

**问题**:
```yaml
name: PDF Processing  # ❌ 包含空格和大写字母
```

**修复**:
```yaml
name: pdf-processing  # ✅ 只使用小写字母和连字符
```

### 错误 3: 缺少触发场景

**问题**:
```yaml
description: 分析 Excel 数据
```

**修复**:
```yaml
description: |
  分析 Excel 数据，创建数据透视表和图表。
  当处理 .xlsx 文件、电子表格、Excel 数据分析时使用。
```

## 版本控制

### 版本历史模板

可以在 SKILL.md 中添加版本历史部分：

```markdown
## 版本历史

- v2.0.0 (2025-10-01): 重大 API 变更
- v1.1.0 (2025-09-15): 添加新功能
- v1.0.0 (2025-09-01): 初始版本
```

## 分享技能

### 通过项目分享

```bash
# 1. 添加技能到项目
mkdir -p .claude/skills/team-skill
# 创建 SKILL.md

# 2. 提交到 git
git add .claude/skills/
git commit -m "添加团队 PDF 处理技能"
git push

# 3. 团队成员自动获得技能
git pull  # 技能立即可用
```

## 参考资源

- [Claude Code Skills 官方文档](https://code.claude.com/docs/en/skills)
- [MindForge 技能集合](https://github.com/ProjAnvil/MindForge)

---

**版本**: 1.0.0
**最后更新**: 2025-12
**维护者**: MindForge Team
