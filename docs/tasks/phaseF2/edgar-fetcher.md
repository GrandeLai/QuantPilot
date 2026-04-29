# Task phaseF2.edgar-fetcher: EDGAR 数据抓取客户端

**Phase**: Phase F.2
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/edgar/` 模块，实现：

1. **`models.py`** — 核心数据类型 (`EightKFiling`, `EightKItem`, `Form4Transaction`)
2. **`client.py`** — EDGAR REST API 客户端（ticker→CIK 查询、8-K 列表、8-K 文本下载、Form 4 XML 下载）
3. **`__init__.py`** — 导出公共接口

### 关键实现细节

#### EDGAR 客户端约束

- User-Agent 头：`QuantPilot/1.0 jdawlaia@gmail.com`
- 限速：请求间隔 ≥ 0.11s（≤ 10 req/s）
- 全部使用 `httpx.AsyncClient`
- 基础 URL：
  - `https://data.sec.gov/submissions/CIK{cik:010d}.json` — ticker 的提交历史
  - `https://data.sec.gov/` — EDGAR data API
  - `https://www.sec.gov/` — 实际文件下载

#### 数据模型

```python
@dataclass
class EightKItem:
    item_number: str      # "1.01", "5.02", "8.01"
    item_title: str       # "Entry into Material Agreement" etc.
    text: str             # 清洗后的纯文本内容

@dataclass
class EightKFiling:
    ticker: str
    cik: str
    accession_number: str  # "0001234567-24-000001"
    filed_date: date
    period_of_report: date | None
    items: list[EightKItem]
    raw_html_url: str       # 主文档 URL

@dataclass
class Form4Transaction:
    ticker: str
    cik: str                 # issuer CIK
    insider_name: str
    insider_title: str       # CEO, CFO, Director, etc.
    transaction_date: date
    transaction_type: str    # "P" (purchase) or "S" (sale)
    shares: float
    price_per_share: float
    total_value: float
    is_10b5_1_plan: bool     # True → 计划性交易，通常排除
    accession_number: str
```

#### 客户端函数

```python
async def get_cik(ticker: str) -> str:
    """ticker → CIK（从 EDGAR company search）"""

async def get_recent_8k_filings(ticker: str, *, max_count: int = 5) -> list[EightKFiling]:
    """获取最近 N 份 8-K，含解析好的 items"""

async def get_form4_transactions(
    ticker: str,
    *,
    since_date: date | None = None,
    max_count: int = 100,
) -> list[Form4Transaction]:
    """获取最近 Form 4 transactions"""
```

---

## 验收标准

- [ ] **AC-1**: 模块文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/edgar/__init__.py`
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/edgar/models.py`
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/edgar/client.py`

- [ ] **AC-2**: 数据模型完整
  - `grep -q "EightKFiling\|EightKItem\|Form4Transaction" apps/stock-assistant/backend/src/quantpilot_stock/edgar/models.py`

- [ ] **AC-3**: 客户端函数签名
  - `grep -q "get_cik\|get_recent_8k_filings\|get_form4_transactions" apps/stock-assistant/backend/src/quantpilot_stock/edgar/client.py`

- [ ] **AC-4**: User-Agent 限速
  - `grep -q "QuantPilot\|rate.limit\|sleep\|asyncio.sleep\|_RATE_LIMIT" apps/stock-assistant/backend/src/quantpilot_stock/edgar/client.py`

- [ ] **AC-5**: 单元测试通过（httpx mock，不发真实请求）
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run pytest tests/test_edgar_client.py -v)` 退出码 0
  - 至少 8 个测试（CIK 查询、8-K 解析、Form4 解析、网络错误处理）

- [ ] **AC-6**: mypy 通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/edgar/)` 退出码 0

---

## 文件影响范围

新建（本任务核心文件）：
- `apps/stock-assistant/backend/src/quantpilot_stock/edgar/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/edgar/models.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/edgar/client.py`
- `apps/stock-assistant/backend/tests/test_edgar_client.py`

修改：
- `apps/stock-assistant/backend/pyproject.toml`（添加 `rapidfuzz>=3.0.0`；使用 html.parser 故不需要 lxml）

**注（批次说明）**：以下文件属于同批次并行任务（F.2.2–F.2.5），与本任务共同提交：
- `edgar/diff_engine.py`、`edgar/form4_engine.py`（F.2.2/F.2.3）
- `api/sec.py`、`main.py`（F.2.4）
- `SECEventsPanel.tsx`、`client.ts`、`RiskReviewCenter.tsx`（F.2.5）
- `tests/test_edgar_diff_engine.py`、`tests/test_form4_cluster.py`、`tests/test_sec_api.py`
- `docs/tasks/phaseF2/`、`docs/acceptance/phaseF2/`
