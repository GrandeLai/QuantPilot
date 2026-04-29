# Task F.18: Sector Momentum Heatmap

## 背景与目的

Sector rotation 是 alpha 的持续来源之一：
- 市场不同阶段，防御/周期/成长板块交替领涨
- 选股时知道哪些板块在领涨可以大幅提高胜率
- 机构常用 "sector momentum" 作为组合倾斜因子

数据源：11 个 SPDR 板块 ETF + SPY 基准，yfinance 免费获取

## 验收标准（AC）

### AC-1 引擎（sector_momentum/engine.py）

- [ ] `SECTOR_ETFS` = 11 SPDR 板块 ETF 字典（ticker → 中文板块名）
- [ ] `SectorReturn` dataclass：ticker, sector_name, return_1m, return_3m, return_6m, vs_spy_1m, grade(str)
- [ ] `SectorMomentumData` dataclass：sectors(list[SectorReturn]), top3(list[SectorReturn]), bottom3(list[SectorReturn]), spy_return_1m, as_of_date, data_available
- [ ] `_sector_grade(return_1m, vs_spy_1m)` → str: "leading"/"in_line"/"lagging"
- [ ] `compute_sector_momentum()` → `SectorMomentumData`（始终返回，永不抛出）
- [ ] 批量 yfinance 下载（yf.download，一次调用），超时/异常时 data_available=False

### AC-2 API（api/sector_momentum.py）

- [ ] `GET /api/sector-momentum` → 200 + SectorMomentumResponse（无 ticker 参数，始终 200）
- [ ] 路由通过 `include_with_api_alias` 注册

### AC-3 前端

- [ ] `SectorReturn`、`SectorMomentumData` 类型加入 `client.ts`
- [ ] `fetchSectorMomentum()` 加入 `client.ts`
- [ ] `SectorMomentumPanel.tsx`：板块表格（1M/3M/6M + vs SPY）+ top3/bottom3 高亮 + 降级提示
- [ ] `SectorMomentumPanel` 加入 `RiskReviewCenter.tsx`
- [ ] TypeScript 构建无报错

### AC-4 测试（≥ 12 个）

- [ ] `_sector_grade` 边界
- [ ] `compute_sector_momentum` happy path（mocked yf.download）
- [ ] yfinance 不可达 → data_available=False，永不抛出
- [ ] API 200 返回所有板块字段

## 文件白名单

- `apps/stock-assistant/backend/src/quantpilot_stock/sector_momentum/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/sector_momentum/engine.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/api/sector_momentum.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`
- `apps/stock-assistant/backend/tests/test_sector_momentum.py`
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- `apps/stock-assistant/frontends/workbench/src/components/SectorMomentumPanel.tsx`
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- `docs/tasks/phaseF18/sector-momentum.md`
- `docs/acceptance/phaseF18/sector-momentum.md`

## 11 SPDR 板块 ETF

XLK(科技), XLV(医疗健康), XLF(金融), XLY(非必需消费), XLP(必需消费),
XLE(能源), XLI(工业), XLB(材料), XLRE(房地产), XLU(公用事业), XLC(通信)

## grade 逻辑

```
if return_1m > spy_return_1m + 2.0:  grade = "leading"
elif return_1m < spy_return_1m - 2.0: grade = "lagging"
else:                                  grade = "in_line"
```
