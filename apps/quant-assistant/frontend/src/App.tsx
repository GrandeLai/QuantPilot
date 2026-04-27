/**
 * QuantPilot Quant Assistant 研究前端 (Phase A skeleton).
 *
 * 当前为占位 shell，等 Phase B Rust quant-assistant 后端 MVP 上线时填充
 * 实际研究面板（BacktestPanel、SignalsPanel、QuantResearchPanel 等已 copy
 * 进 ./components/，Phase B 时 wire-up）。
 */

const QUANT_BACKEND = (import.meta.env?.QUANT_BACKEND as string | undefined) ?? "http://localhost:8002";

export function App() {
  return (
    <main style={{ padding: 24, fontFamily: "system-ui, sans-serif" }}>
      <header style={{ marginBottom: 24 }}>
        <h1>QuantPilot — Quant Assistant</h1>
        <p style={{ color: "#666" }}>
          自动化研究 + 规则化执行 + ONNX 推理（Phase A skeleton）
        </p>
      </header>
      <section>
        <p>Backend: <code>{QUANT_BACKEND}</code></p>
        <p>Phase A 临时态接 <code>apps/quant-assistant-py/</code> (port 8002)。</p>
        <p>Phase B+ 起改接 Rust <code>apps/quant-assistant/backend/</code>。</p>
      </section>
      <section style={{ marginTop: 24 }}>
        <h2>已就位的研究面板（待 Phase B wire-up）</h2>
        <ul>
          <li>BacktestPanel</li>
          <li>SignalsPanel</li>
          <li>QuantResearchPanel</li>
          <li>OptimizationPanel</li>
          <li>MLStrategyPanel</li>
          <li>StrategyEditor / StrategyWorkshop</li>
          <li>ValidationLab</li>
        </ul>
      </section>
    </main>
  );
}
