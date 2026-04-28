# Task phaseC.4.onnx: ONNX 推理端点 + Rhai ml_predict

**Phase**: C
**Status**: in-progress
**Created**: 2026-04-28
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么

- 在 `Cargo.toml` 添加 `tract-onnx` 依赖（纯 Rust，无 C++ 依赖）
- 新建 `src/ml_runner.rs`：
  - `pub struct FeatureSpec { name: String, dtype: String }`
  - `pub struct MlModelMeta { model_id, features: Vec<FeatureSpec>, input_shape: Vec<usize>, output_shape: Vec<usize> }`
  - `pub struct MlRunner { meta: MlModelMeta, plan: SimplePlan<...> }`（tract 推理计划）
  - `impl MlRunner`:
    - `pub fn load(model_dir: &Path) -> Result<Self, String>`：读 meta.json + 加载 model.onnx
    - `pub fn predict(&self, features: &[f64]) -> Result<Vec<f64>, String>`：ONNX 推理
- 在 `lib.rs` 添加 `pub mod ml_runner;`
- 在 `RhaiEngine::new()` 中通过闭包或 `register_fn` 注册 `ml_predict_from_dir(model_dir, features)`：
  接受 `model_dir: String` + `features: Array`，临时加载（MVP；生产版应做缓存，C.x 扩展）
- 新建 `common/data-store/models/test_linear/`:
  - `model.onnx`：一个极简线性模型（1 层 Gemm：`y = W @ x + b`，2 输入 → 1 输出）
  - `meta.json`：符合 `MlModelMeta` 结构（`model_id:"test_linear"`, `features:[f1,f2]`, `input_shape:[1,2]`, `output_shape:[1,1]`）
- 新建脚本 `tools/golden-generator/src/quantpilot_golden/cases/onnx_model.py`：
  用 `onnx` python 库生成上述测试模型
- 新建 `apps/quant-assistant/backend/tests/onnx_test.rs`：
  - `onnx_model_loads`：MlRunner::load 不报错
  - `onnx_prediction_matches_expected`：`W = [[0.5, 0.3]]`, `b = [0.1]`，输入 `[1.0, 2.0]` → `0.5*1.0 + 0.3*2.0 + 0.1 = 1.2`
  - `rhai_ml_predict_works`：Rhai 脚本中调用 `ml_predict_from_dir(path, features)` 返回正确结果

### 不做什么

- 不实现模型缓存（每次 call 重新加载；生产版留 C.x）
- 不在 HTTP 端点暴露（/ml/predict 路由留后续）
- 不支持批量推理（MVP 只做 single-sample）
- 不删除 quant-py 的 LGBMStrategy（它用的是 lightgbm，不是 ONNX；真正的 ONNX 推理替换在 step4 清理时做）

---

## 验收标准

- [ ] **AC-1**: `Cargo.toml` 含 `tract-onnx` 依赖
- [ ] **AC-2**: `src/ml_runner.rs` 存在，含 `MlRunner::load` 和 `MlRunner::predict`
- [ ] **AC-3**: `lib.rs` 含 `pub mod ml_runner`
- [ ] **AC-4**: `common/data-store/models/test_linear/model.onnx` 和 `meta.json` 存在
- [ ] **AC-5**: `runtime/engine.rs` 注册了 `ml_predict_from_dir` Rhai 函数
- [ ] **AC-6**: `cargo test` 全过
- [ ] **AC-7**: `onnx_prediction_matches_expected` 输出与 Python 计算的 `0.5*1 + 0.3*2 + 0.1 = 1.2` 一致（误差 < 1e-6）
- [ ] **AC-8**: `rhai_ml_predict_works` Rhai 调用通过
- [ ] **AC-9**: 已有测试不受影响（common 59、stock 165、quant-py 276）

---

## 测试集合

```bash
# AC-1
grep -q "tract-onnx" apps/quant-assistant/backend/Cargo.toml

# AC-2
test -f apps/quant-assistant/backend/src/ml_runner.rs
grep -q "pub fn load" apps/quant-assistant/backend/src/ml_runner.rs
grep -q "pub fn predict" apps/quant-assistant/backend/src/ml_runner.rs

# AC-3
grep -q "pub mod ml_runner" apps/quant-assistant/backend/src/lib.rs

# AC-4
test -f common/data-store/models/test_linear/model.onnx
test -f common/data-store/models/test_linear/meta.json

# AC-5
grep -q "ml_predict_from_dir" apps/quant-assistant/backend/src/runtime/engine.rs

# AC-6 + AC-7 + AC-8
(cd apps/quant-assistant/backend && cargo test 2>&1 | grep "test result")
(cd apps/quant-assistant/backend && cargo test --test onnx_test 2>&1 | grep -q "test result: ok")

# AC-9
(cd common/python && uv run --group dev pytest tests/ -q | tail -2 | grep -q "59 passed")
(cd apps/stock-assistant/backend && uv run pytest tests/ -q | tail -2 | grep -q "165 passed")
(cd apps/quant-assistant-py/backend && uv run pytest tests/ -q | tail -2 | grep -q "276 passed")
```

---

## 文件影响范围（白名单）

```
- apps/quant-assistant/backend/Cargo.toml
- apps/quant-assistant/backend/src/ml_runner.rs (新建)
- apps/quant-assistant/backend/src/lib.rs
- apps/quant-assistant/backend/src/runtime/engine.rs
- apps/quant-assistant/backend/tests/onnx_test.rs (新建)
- common/data-store/models/test_linear/model.onnx (新建)
- common/data-store/models/test_linear/meta.json (新建)
- tools/golden-generator/src/quantpilot_golden/cases/onnx_model.py (新建)
- tools/golden-generator/pyproject.toml (添加 onnx 依赖)
- docs/tasks/phaseC/c4-onnx.md (本文件)
```

---

## 引用

- **设计来源**：plan §5 "C.4.onnx：在 Rhai 中暴露 ml_predict("model_id", feature_vec) → ONNX 推理"，plan §6 "推理侧（Rust）"
- **ONNX runtime 选型**：`tract`（确认，plan 决策记录）
- **上游依赖**：phaseC.1.rhai（RhaiEngine）, phaseC.2.factor.sma（indicators）
- **下游依赖**：phaseC.5.optimize（C.5 可选择性调用 ml_predict 产生特征权重）
