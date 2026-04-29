# Task phaseF2.edgar-diff-engine: 8-K 文本差分引擎

**Phase**: Phase F.2
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/edgar/diff_engine.py`。

### 核心逻辑

对同一公司的**前后两份 8-K**，在同一 item 编号内做段落级文本差分：

1. 将 item 文本按段落（空行）分割
2. 用 `rapidfuzz.fuzz.ratio` 做段落相似度匹配（贪心对齐，O(n²)，item 一般 < 50 段）
3. 输出三类变化：
   - `"added"`：新增段落（在旧版中找不到 similarity ≥ 0.7 的对应段落）
   - `"removed"`：删除段落（在新版中找不到）
   - `"modified"`：相似但有改动（0.7 ≤ similarity < 0.95）

### 输出数据模型

```python
@dataclass
class ParagraphDiff:
    diff_type: Literal["added", "removed", "modified", "unchanged"]
    old_text: str | None    # "removed" / "modified" 时有值
    new_text: str | None    # "added" / "modified" 时有值
    similarity: float       # 0.0 = 新增/删除；0-1 = 修改程度

@dataclass
class ItemDiff:
    item_number: str
    item_title: str
    paragraphs: list[ParagraphDiff]
    has_material_change: bool  # 有 added 或 removed 段落，或修改段落 similarity < 0.85
    change_score: float        # 0-1，越大越有料

@dataclass
class EightKDiff:
    ticker: str
    old_accession: str
    new_accession: str
    old_filed_date: date
    new_filed_date: date
    item_diffs: list[ItemDiff]
    overall_change_score: float  # max of item change_scores
```

### 关键函数

```python
def diff_8k_filings(old: EightKFiling, new: EightKFiling) -> EightKDiff:
    """对两份 8-K 做 item-level 差分，返回 EightKDiff."""
```

---

## 验收标准

- [ ] **AC-1**: 文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/edgar/diff_engine.py`

- [ ] **AC-2**: 关键符号存在
  - `grep -q "ParagraphDiff\|ItemDiff\|EightKDiff\|diff_8k_filings" apps/stock-assistant/backend/src/quantpilot_stock/edgar/diff_engine.py`

- [ ] **AC-3**: rapidfuzz 引用
  - `grep -q "rapidfuzz" apps/stock-assistant/backend/src/quantpilot_stock/edgar/diff_engine.py`

- [ ] **AC-4**: 单元测试通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run pytest tests/test_edgar_diff_engine.py -v)` 退出码 0
  - 至少 6 个测试（added/removed/modified/unchanged 检测，change_score 值域，identical filing → score=0）

- [ ] **AC-5**: mypy 通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/edgar/diff_engine.py)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/edgar/diff_engine.py`
- `apps/stock-assistant/backend/tests/test_edgar_diff_engine.py`
