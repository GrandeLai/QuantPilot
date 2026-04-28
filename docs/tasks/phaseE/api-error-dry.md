# Task phaseE.api-error-dry: 提取共享 ApiError（B1）

**Phase**: Phase E (post)
**Status**: pending
**Created**: 2026-04-28
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

`apps/quant-assistant/backend/src/api/` 下四个模块（backtest.rs、indicators.rs、optimize.rs、walk_forward.rs）各自定义了相同的 `ApiError` 结构体和 `impl IntoResponse`：

```rust
pub struct ApiError(pub StatusCode, pub String);

impl IntoResponse for ApiError {
    fn into_response(self) -> axum::response::Response {
        (self.0, Json(serde_json::json!({"error": self.1}))).into_response()
    }
}
```

这是重复代码（DRY 违反），应抽取到 `api/mod.rs`。

### 做什么

1. **在 `src/api/mod.rs` 中添加共享 `ApiError`**：
   - 定义 `pub struct ApiError(pub StatusCode, pub String);`
   - 实现 `impl IntoResponse for ApiError`
   - 添加必要 imports（axum::http::StatusCode、axum::response::IntoResponse、axum::Json）

2. **从 4 个子模块中删除重复定义**：
   - `src/api/backtest.rs`：删除本地 `ApiError` 定义和 `impl IntoResponse`；改用 `super::ApiError`
   - `src/api/indicators.rs`：同上
   - `src/api/optimize.rs`：同上
   - `src/api/walk_forward.rs`：同上

3. **更新各模块 import**：
   - 各模块的 handler 签名中 `ApiError` 仍然直接可用（通过 `super::ApiError` 或直接添加 `use super::ApiError;`）
   - 无需修改 handler 函数体中的 `ApiError(...)` 调用

### 不做什么

- 不修改 handler 函数的业务逻辑
- 不修改前端
- 不添加新的 Rust 依赖
- 不修改 `main.rs`

---

## 验收标准

- [ ] **AC-1**: `(cd apps/quant-assistant/backend && cargo test)` 通过（含所有现有测试）
- [ ] **AC-2**: `grep -c "pub struct ApiError" apps/quant-assistant/backend/src/api/mod.rs` == 1（共享定义只在 mod.rs 中）
- [ ] **AC-3**: `grep -rn "pub struct ApiError" apps/quant-assistant/backend/src/api/{backtest,indicators,optimize,walk_forward}.rs` 无输出（子模块中已删除）
- [ ] **AC-4**: `(cd apps/quant-assistant/backend && cargo build)` 无编译警告（不含 unused import 警告）

---

## 文件影响范围（白名单）

修改：
- `apps/quant-assistant/backend/src/api/mod.rs`
- `apps/quant-assistant/backend/src/api/backtest.rs`
- `apps/quant-assistant/backend/src/api/indicators.rs`
- `apps/quant-assistant/backend/src/api/optimize.rs`
- `apps/quant-assistant/backend/src/api/walk_forward.rs`
