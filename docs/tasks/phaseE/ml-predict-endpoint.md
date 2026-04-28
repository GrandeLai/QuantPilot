# Task phaseE.ml-predict-endpoint: POST /api/ml/predict ONNX 推理端点（A3）

**Phase**: Phase E (post)
**Status**: pending
**Created**: 2026-04-28
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

`apps/quant-assistant/backend/src/ml_runner.rs` 已实现完整的 ONNX 推理引擎（`MlRunner::load` + `MlRunner::predict`），并有通过测试。但没有对应的 HTTP 端点。本任务添加 `POST /api/ml/predict` 端点，将 `MlRunner` 接入 HTTP API 层。

### 做什么

1. **新建 `src/api/ml_predict.rs`**：

   **请求体**：
   ```json
   {
     "model_id": "test_linear",
     "features": [1.0, 2.0]
   }
   ```

   **响应体** `200 OK`：
   ```json
   {
     "model_id": "test_linear",
     "n_features": 2,
     "predictions": [1.2]
   }
   ```

   **模型路径约定**：`{CARGO_MANIFEST_DIR}/../../../common/data-store/models/<model_id>/`（与现有测试一致）

   **错误处理**：
   - `model_id` 含 `/` 或 `..` 时返回 `400 Bad Request`（路径遍历防护）
   - 模型目录不存在 / meta.json 损坏 / model.onnx 加载失败 → `400 Bad Request` + `{"error": "..."}`
   - 特征数量不匹配 → `400 Bad Request`

2. **在 `src/api/mod.rs` 中注册路由**：
   - `pub mod ml_predict;`
   - `.route("/api/ml/predict", post(ml_predict::predict))`

3. **在 `main.rs` 中更新端点列表文档（可选）**：
   - 如果 `main.rs` 有硬编码端点列表，添加 `/api/ml/predict`

### 不做什么

- 不添加模型缓存（每次请求重新加载）
- 不修改 `ml_runner.rs`
- 不修改前端

---

## 验收标准

- [ ] **AC-1**: `test -f apps/quant-assistant/backend/src/api/ml_predict.rs`
- [ ] **AC-2**: `grep -c "/api/ml/predict\|ml_predict" apps/quant-assistant/backend/src/api/mod.rs` >= 2（路由 + 模块声明）
- [ ] **AC-3**: `(export PATH="/Users/bytedance/.cargo/bin:$PATH" && cd apps/quant-assistant/backend && cargo test)` 全通过（含新端点的集成测试）
- [ ] **AC-4**: `grep "ml_predict\|ml/predict" apps/quant-assistant/backend/src/api/ml_predict.rs` 有输出

---

## 文件影响范围（白名单）

新建：
- `apps/quant-assistant/backend/src/api/ml_predict.rs`

修改：
- `apps/quant-assistant/backend/src/api/mod.rs`
- `apps/quant-assistant/backend/src/main.rs`（可选：端点列表更新）
