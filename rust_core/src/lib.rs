//! QuantPilot 核心计算引擎（Rust + PyO3）
//!
//! 提供高性能回测循环和量化计算原语，通过 PyO3 暴露给 Python 层。

use pyo3::prelude::*;

/// 返回 rust_core 模块版本号
#[pyfunction]
fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

/// 简单移动平均回测核心循环
///
/// # Arguments
/// * `closes` - 收盘价序列
/// * `fast_period` - 快线周期
/// * `slow_period` - 慢线周期
/// * `initial_cash` - 初始资金
///
/// # Returns
/// 每个时间步的组合净值序列
#[pyfunction]
fn run_ma_crossover_backtest(
    closes: Vec<f64>,
    fast_period: usize,
    slow_period: usize,
    initial_cash: f64,
) -> PyResult<Vec<f64>> {
    let n = closes.len();
    if n < slow_period {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "数据长度不足：需要至少 slow_period 个数据点",
        ));
    }

    let mut portfolio_values = vec![initial_cash; n];
    let mut position: f64 = 0.0;
    let mut cash: f64 = initial_cash;

    for i in slow_period..n {
        // 计算快线均值
        let fast_sum: f64 = closes[(i - fast_period)..i].iter().sum();
        let fast_ma = fast_sum / fast_period as f64;

        // 计算慢线均值
        let slow_sum: f64 = closes[(i - slow_period)..i].iter().sum();
        let slow_ma = slow_sum / slow_period as f64;

        let price = closes[i];

        if fast_ma > slow_ma && position == 0.0 && cash > 0.0 {
            // 金叉买入
            position = cash / price;
            cash = 0.0;
        } else if fast_ma < slow_ma && position > 0.0 {
            // 死叉卖出
            cash = position * price;
            position = 0.0;
        }

        portfolio_values[i] = cash + position * price;
    }

    // 填充前 slow_period 个时间步的净值
    for i in 0..slow_period {
        portfolio_values[i] = initial_cash;
    }

    Ok(portfolio_values)
}

/// 计算一组收益的夏普比率
///
/// # Arguments
/// * `returns` - 收益率序列（百分比形式，如 0.01 表示 1%）
/// * `risk_free_rate` - 年化无风险利率（如 0.02 表示 2%）
/// * `periods_per_year` - 每年交易周期数（日线=252，分钟=252*390）
#[pyfunction]
fn sharpe_ratio(returns: Vec<f64>, risk_free_rate: f64, periods_per_year: f64) -> f64 {
    let n = returns.len() as f64;
    if n < 2.0 {
        return 0.0;
    }

    let mean: f64 = returns.iter().sum::<f64>() / n;
    let variance: f64 = returns.iter().map(|r| (r - mean).powi(2)).sum::<f64>() / (n - 1.0);
    let std_dev = variance.sqrt();

    if std_dev == 0.0 {
        return 0.0;
    }

    let daily_risk_free = risk_free_rate / periods_per_year;
    (mean - daily_risk_free) / std_dev * periods_per_year.sqrt()
}

/// 计算最大回撤
///
/// # Arguments
/// * `portfolio_values` - 组合净值序列
///
/// # Returns
/// (最大回撤比例, 回撤开始索引, 回撤结束索引)
#[pyfunction]
fn max_drawdown(portfolio_values: Vec<f64>) -> (f64, usize, usize) {
    let n = portfolio_values.len();
    if n < 2 {
        return (0.0, 0, 0);
    }

    let mut max_dd = 0.0f64;
    let mut peak = portfolio_values[0];
    let mut peak_idx = 0usize;
    let mut dd_start = 0usize;
    let mut dd_end = 0usize;

    for i in 1..n {
        if portfolio_values[i] > peak {
            peak = portfolio_values[i];
            peak_idx = i;
        }
        let dd = (peak - portfolio_values[i]) / peak;
        if dd > max_dd {
            max_dd = dd;
            dd_start = peak_idx;
            dd_end = i;
        }
    }

    (max_dd, dd_start, dd_end)
}

/// QuantPilot Rust 核心模块
#[pymodule]
fn quantpilot_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(run_ma_crossover_backtest, m)?)?;
    m.add_function(wrap_pyfunction!(sharpe_ratio, m)?)?;
    m.add_function(wrap_pyfunction!(max_drawdown, m)?)?;
    Ok(())
}
