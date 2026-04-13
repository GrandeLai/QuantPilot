import { ASSISTANT_TABS } from "./navigation";

/**
 * Minimal investment assistant shell.
 */
export default function App() {
  return (
    <main>
      <h1>Investment Assistant</h1>
      <ul>
        {ASSISTANT_TABS.map((tab) => (
          <li key={tab.key}>{tab.label}</li>
        ))}
      </ul>
    </main>
  );
}
