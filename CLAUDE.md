# CLAUDE.md — Claude Code 项目指令文件

## 项目简介

你正在开发 QuantPilot，一个本地优先的个人量化交易平台。

## 核心参考文档

- **设计文档 (必读)**：`docs/DESIGN.md` — 包含完整的项目架构、功能模块、技术栈、编码规范、API 设计、任务分解。所有开发工作以此文档为准。
- **每次开始新任务前**，先阅读 `docs/DESIGN.md` 中对应的模块章节。

## 开发工作流

### 1. 任务执行流程

每次执行任务时，严格按以下步骤：

1. **读取** `docs/DESIGN.md` 中对应 Task 章节，理解需求和验收标准
2. **创建/修改**代码文件，严格遵循 `docs/DESIGN.md` Section 3 的目录结构
3. **编写测试**，覆盖验收标准中的所有条目
4. **运行测试**，确保全部通过
5. **运行 lint**，确保代码规范
6. **更新文档**：在 `docs/DESIGN.md` 中将完成的 Task 打 `[x]`，如有新的技术决策则追加到 Section 4.5

### 2. 编码规范

- Python: 严格遵循 `docs/DESIGN.md` Section 5.1（type hints、ruff、loguru、async-first、Pydantic v2）
- Rust: 遵循 Section 5.2（clippy、doc comments、PyO3）
- TypeScript: 遵循 Section 5.3（strict mode、函数组件、Zustand）
- Git: 遵循 Section 5.4 Conventional Commits 格式

### 3. 文件创建规则

- 新文件必须放在 `docs/DESIGN.md` Section 3 定义的位置
- 如需创建文档中未定义的新文件，先说明原因
- 所有 Python 文件必须包含模块级 docstring
- 所有 public 函数/类必须有 type hints 和 docstring

### 4. 依赖管理

- 只使用 `docs/DESIGN.md` Section 4 中列出的依赖
- 如需引入新依赖，必须先说明理由并更新 DESIGN.md Section 4

## 常用命令

```bash
# 安装依赖
cd backend && uv sync --extra dev

# 运行测试
cd backend && uv run pytest tests/ -v

# 代码检查
cd backend && uv run ruff check src/ tests/

# 类型检查
cd backend && uv run mypy src/

# 格式化
cd backend && uv run ruff format src/ tests/

# Rust 构建
cd rust_core && cargo build

# 前端开发
cd frontend && npm install && npm run dev
```

## 关键约束

- **不要** 跳过测试编写
- **不要** 忽略验收标准
- **不要** 引入文档外的依赖而不更新文档
- **不要** 修改目录结构而不更新 DESIGN.md Section 3
- 如果某个任务的验收标准不清晰，先问我再动手
