//! HTTP API 路由模块.
//!
//! 每个子模块对应一组相关端点：
//! - `backtest`：MA crossover 回测（含 trade 统计）
//! - `indicators`：SMA/EMA 指标计算
//! - `optimize`：网格搜索参数优化
//! - `walk_forward`：Walk-Forward CV

pub mod backtest;
pub mod indicators;
pub mod optimize;
pub mod walk_forward;

use axum::{routing::post, Router};

/// 构建所有 API 路由，挂载在 `/api` 前缀下.
pub fn router() -> Router {
    Router::new()
        .route("/api/backtest/run", post(backtest::run_backtest))
        .route("/api/walk-forward", post(walk_forward::run_walk_forward))
        .route("/api/optimize", post(optimize::run_optimize))
        .route("/api/indicators", post(indicators::compute_indicators))
}
