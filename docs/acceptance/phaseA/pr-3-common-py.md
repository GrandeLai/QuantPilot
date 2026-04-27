# Acceptance Report: phaseA.pr-3-common-py

**Run at**: 2026-04-27T15:25:00Z
**Implementation PR/commit**: `eb06d9a` — refactor(common): extract shared infra to common/python (Phase A PR 3)
**Diff range**: `965abdb..eb06d9a`
**Acceptance-agent invocation**: Bootstrap self-validation
**Verdict**: ✅ **PASS**

---

## 文件影响范围检查

PR 3 改动文件（99 文件）：
- 18 文件搬动 from `backend/src/quantpilot/{config.py, redis/, plugins/, data/, platform/{models.py, services.py}}` 到 `common/python/quantpilot_common/`（git rename detection 全部识别）✅
- 6 测试文件搬动 from `backend/tests/{test_data_*, test_plugins, test_redis_client, platform/test_models}` 到 `common/python/tests/`✅
- 47 文件 import 重写 in `backend/src/quantpilot/**/*.py` 和 `backend/tests/**/*.py`✅
- 7 共 7 文件内部 import 修正 in 移动后的 `common/python/quantpilot_common/**/*.py`✅
- 新增：`common/python/{pyproject.toml, README.md, quantpilot_common/__init__.py, quantpilot_common/platform/__init__.py}` ✅
- 修改：`backend/src/quantpilot/platform/__init__.py`（去除已迁出模块的 re-export）✅
- 修改：`pyproject.toml`（顶层；workspace members 追加 common/python）✅
- 修改：`uv.lock`（自动） ✅
- 修改：`docs/tasks/phaseA/pr-3-common-py.md`（实施过程中范围调整记录）✅

**结论**：所有改动在白名单内。范围调整（platform 拆分而非整搬）已在 task spec 中更新并标记原因。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: backend/src/quantpilot/ 不再含 config.py/redis//plugins//data/ | ✅ PASS | `! test -e` 4 个路径全部确认不存在 |
| AC-2: common/python/quantpilot_common/ 含上述模块 | ✅ PASS | `test -d` redis/、platform/、plugins/、data/；`test -e` config.py 全部确认 |
| AC-3: common/python/pyproject.toml 含 `name = "quantpilot-common"` | ✅ PASS | grep 命中 |
| AC-4: 根 `uv sync` 退出码 0 | ✅ PASS | `Resolved 73 packages` 完成；workspace member quantpilot-common 接入 |
| AC-5: 现有 backend pytest 全过 | ✅ PASS | **446 passed in 22.42s**（down from 505 因为 59 测试移到 common，总数 446+59=505 不变） |
| AC-6: common/python pytest 全过 | ✅ PASS | **59 passed in 12.63s** |
| AC-7: backend/src/ 不再使用已迁出旧路径（agent_models/advisor_service 例外） | ✅ PASS | grep 检查 `from quantpilot.{config,redis,plugins,data}` + `from quantpilot.platform.{models,services}` 全部 0 命中 |
| AC-8: common/python 不反向 import apps/ | ✅ PASS | `grep -rE "from apps\\.\|import apps\\."` 0 命中 |

---

## 测试执行日志摘要

```
=== AC-1 ===
  config.py: gone
  redis/: gone
  plugins/: gone
  data/: gone
=== AC-2 ===
  redis/: present
  platform/: present
  plugins/: present
  data/: present
  config.py: present
=== AC-3 === OK
=== AC-4 ===
  Resolved 73 packages in 3.14s
  ...installed
=== AC-5: backend pytest ===
  446 passed in 22.42s
=== AC-6: common/python pytest ===
  59 passed in 12.63s
  (covers test_data_fetchers, test_data_models, test_data_storage,
   test_plugins, test_redis_client, platform/test_models)
=== AC-7 === ✓ clean
=== AC-8 === ✓ clean
```

---

## 代码 Review 备注

非阻塞性观察：

1. **PR 3 范围中途调整**：原 task spec "platform/ 整体搬到 common"——实施时发现 `platform/__init__.py` 同时导出 `AdviceCard`/`AdviceEvidence`（来自 `agent_models.py`，并被 `advisor_service.py` 用），而 `advisor_service.py` 又依赖 `quantpilot.research.service` —— 后者属于 quant-py 模块。如果整搬 platform 到 common，会造成 common 反向依赖 quant-py，**违反 plan §2 不耦合约束**。

   解决方案：仅搬 `platform/{models.py, services.py}`（真正的共享 contract），保留 `agent_models.py` 和 `advisor_service.py` 在 backend，PR 4 再迁到 stock-assistant。task spec 已对应更新。

2. **Backend 的 .venv 用 editable install** 接入 `quantpilot-common`：`cd backend && uv pip install -e ../common/python`。Phase A PR 4 时 stock-assistant 自己的 pyproject.toml 会显式声明 `quantpilot-common` 为依赖。

3. **`common/python/pyproject.toml` 依赖闭包**：含 pydantic、redis、duckdb、polars、yfinance、akshare、pluggy、httpx、loguru、pyarrow（duckdb→polars 转换需要）。比 backend 的 dep 小很多——只取共享部分。

4. **Test count 数学**：原 backend 总 505；移走 59 → backend 446；新增 common 59；总和 505。**无丢失，无重复**。

5. **BSD sed `\b` 不工作**：第一次批量 import 重写时用 `\b` 字边界没生效（macOS BSD sed 不支持 GNU 风格的 `\b`），第二次改为 `[. ]` 显式跟随字符成功。Linux CI 环境下用 GNU sed 时 `\b` 也工作；这是 macOS 本地偏差。task spec 中 AC-7 grep 用了 GNU `grep -E` 的 `\b` 风格，但根本原因不依赖 `\b`，已用更明确的字符跟随版替代，跨平台兼容。

6. **fakeredis + pyarrow 加进 common dev deps**：`test_redis_client.py` 依赖 fakeredis，`test_data_storage.py` 因 polars+duckdb 的 `.pl()` 转换需要 pyarrow。已分别加入 `[dependency-groups] dev` 和 `[project] dependencies`。

7. **Phase A 后续 PR 的影响**
   - PR 4 (stock-assistant) 需要把 `backend/src/quantpilot/platform/{agent_models.py, advisor_service.py}` 迁过去
   - PR 4 对应也会处理 `backend/tests/test_advisor_api.py`、`test_platform_api.py`、`platform/test_agent_models.py`（API 端点测试）

---

## 后续动作

- ✅ 本 PR 可视为已合并（commit `eb06d9a` 落 main）
- 更新 `docs/acceptance/INDEX.md`
- 下一步：进入 PR 4（stock-assistant 抽出），见 `docs/tasks/phaseA/pr-4-stock-assistant.md`
- 注意 PR 4 范围会同时处理 PR 3 留下的 backend/.../platform/{agent_models, advisor_service}.py
