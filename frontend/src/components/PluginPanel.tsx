/**
 * 插件管理面板.
 */
import { useCallback, useEffect, useState } from "react";

interface Plugin {
  name: string;
  type: string;
}

export default function PluginPanel() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [moduleName, setModuleName] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const loadPlugins = useCallback(async () => {
    try {
      const res = await fetch("/api/plugins");
      if (res.ok) {
        const d = (await res.json()) as { plugins: Plugin[]; count: number };
        setPlugins(d.plugins);
      }
    } catch (_) {}
  }, []);

  useEffect(() => {
    void loadPlugins();
  }, [loadPlugins]);

  const reloadModule = async () => {
    if (!moduleName) return;
    try {
      const res = await fetch("/api/plugins/reload", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ module_name: moduleName }),
      });
      const d = (await res.json()) as { message: string; plugins: Plugin[] };
      setMessage(d.message);
      setPlugins(d.plugins);
    } catch (e) {
      setMessage(String(e));
    }
  };

  return (
    <div className="flex gap-4">
      {/* ── 左侧：热加载 ──────────────────────────── */}
      <div className="w-72 shrink-0 bg-[#151619] border border-[#2A2D35] rounded-xl p-5 flex flex-col gap-3">
        <p className="text-xs font-mono uppercase tracking-wider text-[#8E9299]">
          热加载插件
        </p>

        <div className="flex flex-col gap-1">
          <label className="text-[10px] text-[#8E9299]">模块名称</label>
          <input
            value={moduleName}
            onChange={(e) => setModuleName(e.target.value)}
            placeholder="如 my_plugins.alerts"
            className="w-full bg-[#1C1E22] border border-[#2A2D35] rounded-lg px-3 py-1.5 text-xs text-white placeholder-[#4A4D55] outline-none focus:border-[#4A4D55] transition-colors"
          />
        </div>

        <button
          onClick={() => void reloadModule()}
          className="py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition-colors"
        >
          热加载
        </button>

        {message && (
          <p className="text-xs text-[#00C087]">{message}</p>
        )}
      </div>

      {/* ── 右侧：插件列表 ────────────────────────── */}
      <div className="flex-1 bg-[#151619] border border-[#2A2D35] rounded-xl p-6">
        <p className="text-xs font-mono uppercase tracking-wider text-[#8E9299] mb-5">
          已注册插件
          <span className="ml-2 normal-case text-[#4A4D55]">({plugins.length})</span>
        </p>

        {plugins.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-[#4A4D55] text-sm">
            暂无插件 — 通过热加载导入插件模块
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#2A2D35]">
                {["插件名称", "类型"].map((h) => (
                  <th
                    key={h}
                    className="px-4 py-2 text-[10px] font-mono uppercase tracking-wider text-[#8E9299]"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2A2D35]">
              {plugins.map((p) => (
                <tr
                  key={p.name}
                  className="hover:bg-[#1C1E22]/30 transition-colors"
                >
                  <td className="px-4 py-3 text-sm font-medium text-white">
                    {p.name}
                  </td>
                  <td className="px-4 py-3 text-xs text-[#8E9299] font-mono">
                    {p.type}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
