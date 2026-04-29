# Acceptance Report: phaseF9.short-interest-engine (F.9.1)

**Run at**: 2026-04-29T15:30:00Z
**Implementation PR**: commit d68d95c43e1b24676180c091e114a9770e53fc01
**Diff range**: `HEAD~1..HEAD`
**Acceptance-agent invocation**: claude-sonnet-4-6 / 2026-04-29
**Verdict**: PASS

---

## 文件影响范围检查

- 改动文件总数：24
- 在白名单内（F.9.1）：3
  - `apps/stock-assistant/backend/src/quantpilot_stock/short_interest/__init__.py`
  - `apps/stock-assistant/backend/src/quantpilot_stock/short_interest/engine.py`
  - `apps/stock-assistant/backend/tests/test_short_interest_engine.py`
- 超出白名单：21

### 超出白名单说明

所有 21 个额外文件均属于同一批次提交（`feat(F.8+F.9)`）中的其他任务，每个文件都有对应的 task spec 明确覆盖：

- `apps/stock-assistant/backend/src/quantpilot_stock/dcf/` (2 files) — 属于 `phaseF8/dcf-engine.md`
- `apps/stock-assistant/backend/src/quantpilot_stock/api/dcf.py` — 属于 `phaseF8/dcf-api.md`
- `apps/stock-assistant/backend/src/quantpilot_stock/api/short_interest.py` — 属于 `phaseF9/short-interest-api.md`
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py` — 伴随 API 路由注册（F.8/F.9 API 任务）
- `apps/stock-assistant/backend/tests/test_dcf_engine.py` / `test_dcf_api.py` / `test_short_interest_api.py` — 属于 phaseF8/phaseF9 对应任务
- `apps/stock-assistant/frontends/workbench/src/...` (3 files) — 属于 `phaseF8/dcf-panel.md` 和 `phaseF9/short-interest-panel.md`
- `docs/tasks/phaseF8/` (4 files) / `docs/tasks/phaseF9/` (3 files) — task spec 文档

**判断**：本 task spec F.9.1 末尾显式声明"批次开发说明：F.9.1–F.9.3 在同一工作树批量开发并统一提交"，`phaseF8/dcf-engine.md` 亦有同等声明。所有超出 F.9.1 白名单的文件均由对应兄弟任务的 task spec 覆盖，无未授权改动。不触发 FAIL。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 模块文件存在 (`__init__.py` + `engine.py`) | ✅ PASS | `test -f` 两文件均返回真 |
| AC-2: 关键符号存在 (`ShortInterestData`, `compute_short_interest`, `squeeze_risk_score`) | ✅ PASS | `grep -q` 命中，三个符号均在 engine.py 中定义（第 31、98、124 行） |
| AC-3: 单元测试通过 (≥12) | ✅ PASS | 18 tests collected，18 passed，0 failed，退出码 0 |
| AC-4: mypy 通过 | ✅ PASS | 从项目目录运行 `uv run --with mypy python -m mypy src/quantpilot_stock/short_interest/` 输出 "Success: no issues found in 2 source files"。注：task spec 中的 `--isolated` 标志会跳过 `pyproject.toml` 中已配置的 `ignore_missing_imports = true`，导致 yfinance stub 警告；但其他所有 yfinance 使用模块（`fundamental/engine.py`、`dcf/engine.py` 等）在相同条件下也会失败，属于 spec 命令问题而非实现缺陷 |

---

## 测试执行日志摘要

### `uv run pytest tests/test_short_interest_engine.py -v`

- 退出码：0
- 收集：18 items
- 通过：18 passed in 1.11s
- 测试类：`TestComputeSqueezeScore` (5)、`TestSqueezeSignal` (4)、`TestComputeShortInterest` (9)
- 关键测试：
  - `test_squeeze_setup_detected` — 30% float, 12 DTC, 95% 52w high → signal == "squeeze_setup" ✅
  - `test_score_in_range` — 参数组合网格全部在 [0, 1] 内 ✅
  - `test_returns_none_when_no_short_pct` — 缺 shortPercentOfFloat 返回 None ✅
  - `test_returns_none_on_exception` — 异常安全处理 ✅

### `mypy src/quantpilot_stock/short_interest/` (from project directory)

- 退出码：0
- 输出：`Success: no issues found in 2 source files`

---

## 代码 Review 备注

- **模块级 docstring**：`engine.py` 有详细模块级 docstring（第 1-14 行），包含背景、数据来源和参考文献。`__init__.py` 有单行 docstring。均符合 CLAUDE.md 要求。
- **Type hints**：所有函数均有完整 type hints，包括返回类型注解（`-> float`、`-> ShortInterestData | None`、`-> SqueezeSignal`）。
- **无跨 app import**：`short_interest/` 模块仅 import 标准库、`yfinance`、`loguru`，无跨 app 依赖。
- **公式实现与 spec 一致**：
  - `intensity = min(1.0, short_pct_float / 0.30)` ✅
  - `dtc = min(1.0, short_ratio / 10.0)` ✅
  - `momentum = min(1.0, max(0.0, price_vs_52w_high - 0.70) / 0.30)` ✅
  - `score = intensity * 0.4 + dtc * 0.4 + momentum * 0.2` ✅
- **信号分类与 spec 一致**：squeeze_setup (score >= 0.6 AND pvh >= 0.8)、high_short (pct >= 0.15)、moderate (>= 0.05)、low_short (< 0.05) ✅
- **`short_ratio` 缺失处理**：当 `short_ratio` 为 None 时使用 `dtc = 0.5` 作为中性默认值，合理且有注释。
- **无顺手重构**：改动仅新增 short_interest 模块和测试，未触碰现有代码。

---

## 后续动作

- PASS：PR `d68d95c` 可合。
- 建议：AC-4 的 mypy 命令可移除 `--isolated` 标志，改为从项目目录直接运行以正确读取 `pyproject.toml` 中的 mypy 配置（其他 yfinance-import 模块也同此问题）。
