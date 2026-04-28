# Acceptance Report: phaseE.ml-predict-endpoint

**Run at**: 2026-04-28T12:20:00Z
**Implementation PR**: commit 0e5720af0529a29fc39b7d410f228cf34c9bce19
**Diff range**: `HEAD~1..0e5720a`
**Acceptance-agent invocation**: claude-sonnet-4-6 session, 2026-04-28
**Verdict**: PASS

## 文件影响范围检查
- 改动文件总数：3
- 在白名单内：3
- 超出白名单：0

所有改动文件均在白名单内：
1. `apps/quant-assistant/backend/src/api/ml_predict.rs` — 新建（白名单：新建）
2. `apps/quant-assistant/backend/src/api/mod.rs` — 修改（白名单：修改）
3. `apps/quant-assistant/backend/src/main.rs` — 修改（白名单：可选修改，端点列表更新）

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: `test -f apps/quant-assistant/backend/src/api/ml_predict.rs` | ✅ PASS | `test -f` 返回退出码 0，文件存在 |
| AC-2: `grep -c "/api/ml/predict\|ml_predict" apps/quant-assistant/backend/src/api/mod.rs` >= 2 | ✅ PASS | grep -c 返回 2（`pub mod ml_predict;` + `.route("/api/ml/predict", post(ml_predict::predict))`）|
| AC-3: `cargo test` 全通过（含新端点的集成测试） | ✅ PASS | 66 tests pass: 34 unit + 2 main + 1 golden + 4 indicators + 4 onnx + 3 optimizer + 4 reports + 2 rhai + 4 walk_forward + 4 doc-tests；退出码 0 |
| AC-4: `grep "ml_predict\|ml/predict" apps/quant-assistant/backend/src/api/ml_predict.rs` 有输出 | ✅ PASS | 7 行匹配：module-level docstring、route definition、3 test function names、3 `.uri("/api/ml/predict")` calls |

## 测试执行日志摘要

### `export PATH="/Users/bytedance/.cargo/bin:$PATH" && cargo test`
- 退出码：0
- 关键输出：
  ```
  running 34 tests
  test api::ml_predict::tests::ml_predict_rejects_path_traversal ... ok
  test api::ml_predict::tests::ml_predict_rejects_unknown_model ... ok
  test api::ml_predict::tests::ml_predict_test_linear_returns_correct_output ... ok
  ...
  test result: ok. 34 passed; 0 failed; 0 ignored
  
  test result: ok. 2 passed; 0 failed; 0 ignored  (main.rs: root_lists_all_endpoints asserts /api/ml/predict)
  
  test result: ok. 1 passed (golden)
  test result: ok. 4 passed (indicators)
  test result: ok. 4 passed (onnx)
  test result: ok. 3 passed (optimizer)
  test result: ok. 4 passed (reports)
  test result: ok. 2 passed (rhai)
  test result: ok. 4 passed (walk_forward)
  Doc-tests: ok. 4 passed
  ```
- Total: 66 tests, 0 failures

## 代码 Review 备注

実装の品質は高い。主な観察：

1. **Module docstring**: `ml_predict.rs` has a module-level doc comment (`//!`) describing the endpoint, model path convention, and file structure. Satisfies CLAUDE.md convention.
2. **Type hints / Rust idioms**: `MlPredictRequest` and `MlPredictResponse` are properly typed with `Deserialize`/`Serialize` derives and doc comments on each field.
3. **Path traversal guard**: Checks for `/`, `..`, and empty string — covers the common attack vectors.
4. **No cross-app imports**: `ml_predict.rs` only imports from `crate::ml_runner` and `super::ApiError` — both within `quant-assistant/backend`.
5. **No `common/` reverse import**: Confirmed absent.
6. **Scope discipline**: No out-of-spec changes. The `main.rs` update is explicitly listed as "optional" in the spec and is limited to adding `/api/ml/predict` to the endpoint list in the doc comment + JSON response — exactly what was described.
7. **Test coverage**: 3 new integration tests cover happy path (correct prediction vs expected=1.2), path traversal rejection (400), and unknown model rejection (400). The `root_lists_all_endpoints` test in `main.rs` also implicitly validates registration.
8. **Error handling**: Maps both `MlRunner::load` and `MlRunner::predict` errors to `400 Bad Request` via `ApiError`, consistent with the spec requirements.

No blocking issues found.

## 后续动作

- PASS：PR 可合入 main。
- 建议更新 `docs/acceptance/INDEX.md` 添加此记录。
- 建议更新 `docs/architecture/quant-assistant-api.md` 补充 `POST /api/ml/predict` 端点文档（不阻塞合 PR）。
