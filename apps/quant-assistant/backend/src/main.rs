//! QuantPilot Rust quant-assistant 服务入口（axum）.
//!
//! Phase B MVP：仅 /healthz 端点。
//! Phase B 后续 + Phase C：增加 /backtest, /factors, /signals 等。

use std::net::SocketAddr;

use anyhow::Result;
use axum::{
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;
use tracing::info;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[derive(Serialize)]
struct HealthResponse {
    status: &'static str,
    service: &'static str,
    version: &'static str,
    started_at: String,
}

async fn healthz() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok",
        service: "quant-assistant",
        version: quantpilot_quant::version(),
        started_at: Utc::now().to_rfc3339(),
    })
}

async fn root() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "message": "QuantPilot Quant Assistant (Rust)",
        "version": quantpilot_quant::version(),
        "endpoints": ["/healthz", "/backtest"],
    }))
}

#[derive(Deserialize)]
struct BacktestRequest {
    symbol: String,
    closes: Vec<f64>,
    fast_period: usize,
    slow_period: usize,
    initial_cash: f64,
    /// Optional：Sharpe 计算用，默认 0.0
    #[serde(default)]
    risk_free_rate: f64,
    /// Optional：年化周期数，日线 = 252（默认）
    #[serde(default = "default_periods_per_year")]
    periods_per_year: f64,
}

fn default_periods_per_year() -> f64 {
    252.0
}

#[derive(Serialize)]
struct BacktestResponse {
    symbol: String,
    fast_period: usize,
    slow_period: usize,
    initial_cash: f64,
    equity_curve: Vec<f64>,
    total_return: f64,
    sharpe_ratio: f64,
    max_drawdown: f64,
    max_drawdown_start: usize,
    max_drawdown_end: usize,
}

async fn backtest(Json(req): Json<BacktestRequest>) -> Result<Json<BacktestResponse>, ApiError> {
    let equity_curve = quantpilot_quant::run_ma_crossover_backtest(
        &req.closes,
        req.fast_period,
        req.slow_period,
        req.initial_cash,
    )
    .map_err(ApiError::BadRequest)?;

    // 日收益率序列
    let returns: Vec<f64> = equity_curve
        .windows(2)
        .map(|w| (w[1] - w[0]) / w[0])
        .collect();

    let sharpe = quantpilot_quant::sharpe_ratio(&returns, req.risk_free_rate, req.periods_per_year);
    let (max_dd, dd_start, dd_end) = quantpilot_quant::max_drawdown(&equity_curve);
    let total_return = equity_curve
        .last()
        .map(|v| (v - req.initial_cash) / req.initial_cash)
        .unwrap_or(0.0);

    Ok(Json(BacktestResponse {
        symbol: req.symbol,
        fast_period: req.fast_period,
        slow_period: req.slow_period,
        initial_cash: req.initial_cash,
        equity_curve,
        total_return,
        sharpe_ratio: sharpe,
        max_drawdown: max_dd,
        max_drawdown_start: dd_start,
        max_drawdown_end: dd_end,
    }))
}

#[derive(Debug)]
enum ApiError {
    BadRequest(String),
}

impl IntoResponse for ApiError {
    fn into_response(self) -> axum::response::Response {
        match self {
            ApiError::BadRequest(msg) => {
                (StatusCode::BAD_REQUEST, Json(serde_json::json!({"error": msg}))).into_response()
            }
        }
    }
}

fn build_app() -> Router {
    Router::new()
        .route("/", get(root))
        .route("/healthz", get(healthz))
        .route("/backtest", post(backtest))
        .layer(CorsLayer::permissive())
        .layer(TraceLayer::new_for_http())
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info,tower_http=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    let port: u16 = std::env::var("QUANTPILOT_QUANT_PORT")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(8002);

    let addr = SocketAddr::from(([127, 0, 0, 1], port));
    let app = build_app();

    info!("QuantPilot Rust quant-assistant listening on http://{addr}");

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::body::to_bytes;
    use axum::http::{Request, StatusCode};
    use tower::ServiceExt;

    #[tokio::test]
    async fn healthz_returns_ok_status() {
        let app = build_app();
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/healthz")
                    .body(axum::body::Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);

        let body = to_bytes(response.into_body(), usize::MAX).await.unwrap();
        let body_str = std::str::from_utf8(&body).unwrap();
        assert!(body_str.contains("\"status\":\"ok\""));
        assert!(body_str.contains("\"service\":\"quant-assistant\""));
    }

    #[tokio::test]
    async fn root_returns_welcome_message() {
        let app = build_app();
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/")
                    .body(axum::body::Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);
    }
}
