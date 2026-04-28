//! Rhai 策略引擎封装.
//!
//! ## 用法
//! ```no_run
//! use quantpilot_quant::runtime::{RhaiEngine, Signal};
//!
//! let engine = RhaiEngine::new();
//! let strategy = engine.compile_file("strategies/ma_crossover.rhai")?;
//! let signal = engine.call_signal(&strategy, 105.0, 100.0)?;
//! assert_eq!(signal, Signal::Long);
//! # Ok::<(), String>(())
//! ```

use std::path::Path;

use rhai::{Engine, AST};

/// 策略信号（最简化 MVP；Phase C.x 扩 strength/reason 等）.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Signal {
    Long,
    Flat,
    Hold,
}

impl Signal {
    fn from_rhai_string(s: &str) -> Result<Self, String> {
        match s {
            "long" => Ok(Signal::Long),
            "flat" => Ok(Signal::Flat),
            "hold" => Ok(Signal::Hold),
            other => Err(format!("Rhai 策略返回未知 signal: {other}")),
        }
    }
}

/// 编译后的 Rhai 策略.
pub struct CompiledStrategy {
    ast: AST,
    name: String,
}

impl CompiledStrategy {
    pub fn name(&self) -> &str {
        &self.name
    }
}

/// Rhai 引擎封装，承载共享配置 + 注册的内置函数.
pub struct RhaiEngine {
    engine: Engine,
}

impl RhaiEngine {
    /// 创建默认配置的引擎.
    pub fn new() -> Self {
        let mut engine = Engine::new();
        // Phase C.1 仅设默认 limits；C.x 扩注册 sma/ema 等内置 indicator
        engine.set_max_expr_depths(64, 32);
        engine.set_max_call_levels(32);
        Self { engine }
    }

    /// 从文件编译策略.
    pub fn compile_file<P: AsRef<Path>>(&self, path: P) -> Result<CompiledStrategy, String> {
        let path = path.as_ref();
        let name = path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("unnamed")
            .to_string();

        let ast = self
            .engine
            .compile_file(path.to_path_buf())
            .map_err(|e| format!("Rhai compile error in {path:?}: {e}"))?;

        Ok(CompiledStrategy { ast, name })
    }

    /// 从字符串编译策略（test/inline 用途）.
    pub fn compile_str(&self, source: &str, name: &str) -> Result<CompiledStrategy, String> {
        let ast = self
            .engine
            .compile(source)
            .map_err(|e| format!("Rhai compile error in {name}: {e}"))?;
        Ok(CompiledStrategy {
            ast,
            name: name.to_string(),
        })
    }

    /// 调 Rhai 策略的 `signal(fast, slow)` 函数，返回 Signal 枚举.
    pub fn call_signal(
        &self,
        strategy: &CompiledStrategy,
        fast: f64,
        slow: f64,
    ) -> Result<Signal, String> {
        let result: String = self
            .engine
            .call_fn(&mut rhai::Scope::new(), &strategy.ast, "signal", (fast, slow))
            .map_err(|e| format!("Rhai call_fn signal in {} failed: {e}", strategy.name))?;
        Signal::from_rhai_string(&result)
    }
}

impl Default for RhaiEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const SAMPLE_SCRIPT: &str = r#"
        fn signal(fast, slow) {
            if fast > slow { return "long"; }
            if fast < slow { return "flat"; }
            return "hold";
        }
    "#;

    #[test]
    fn rhai_engine_compiles_and_calls_signal() {
        let engine = RhaiEngine::new();
        let strategy = engine.compile_str(SAMPLE_SCRIPT, "test").unwrap();

        assert_eq!(engine.call_signal(&strategy, 105.0, 100.0).unwrap(), Signal::Long);
        assert_eq!(engine.call_signal(&strategy, 95.0, 100.0).unwrap(), Signal::Flat);
        assert_eq!(engine.call_signal(&strategy, 100.0, 100.0).unwrap(), Signal::Hold);
    }

    #[test]
    fn unknown_signal_returns_error() {
        let bad_script = r#"
            fn signal(fast, slow) {
                return "buy_aggressive";  // not a valid signal
            }
        "#;
        let engine = RhaiEngine::new();
        let strategy = engine.compile_str(bad_script, "bad").unwrap();
        let err = engine.call_signal(&strategy, 1.0, 0.0).unwrap_err();
        assert!(err.contains("buy_aggressive"));
    }
}
