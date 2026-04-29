# Task phaseF.assistant-frontend-proxy: 修复 assistant frontend 缺失 Vite proxy

**Phase**: Phase F.1 修复
**Status**: pending
**Implementation PR**: <pending>
**Created**: 2026-04-29
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

`apps/stock-assistant/frontends/assistant/`（端口 5174）的 `vite.config.ts` 没有配置 `/api` proxy。前端代码 `src/api/client.ts` 中所有请求形如 `/api/advisor/overview`、`/api/crypto/research/latest`，但 dev server 没有 proxy → Vite SPA 回退到 `index.html` → 前端 `JSON.parse('<!doctype...')` 抛 `SyntaxError: Unexpected token '<'`。

用户在 ReviewAsk 复盘与问答 tab 看到的就是这个 error。

### 做什么

`apps/stock-assistant/frontends/assistant/vite.config.ts` 加 `server.proxy` 配置，与 workbench 同形：

```ts
server: {
  port: 5174,
  proxy: {
    "/api": {
      target: "http://127.0.0.1:8001",
      changeOrigin: true,
      rewrite: (p) => p.replace(/^\/api/, ""),
    },
  },
},
```

注意：
- workbench 用 5173；assistant 历来用 5174（见 `scripts/dev-stock.sh`）
- backend 用 `include_with_api_alias`，所以 rewrite `/api → ""` 后 backend 也能匹配

### 不做什么

- 不改 `client.ts`（URL 已经是 `/api/...` 正确格式）
- 不动 backend（路由本身正常）
- 不改 workbench
- 不引入新依赖

---

## 验收标准

- [ ] **AC-1**: vite.config.ts 含 proxy 配置
  - `grep -q "/api" apps/stock-assistant/frontends/assistant/vite.config.ts`
  - `grep -q "127.0.0.1:8001\|localhost:8001" apps/stock-assistant/frontends/assistant/vite.config.ts`
  - `grep -q "5174" apps/stock-assistant/frontends/assistant/vite.config.ts`
- [ ] **AC-2**: type-check + build 通过
  - `(cd apps/stock-assistant/frontends/assistant && npm run type-check)` 退出码 0
  - `(cd apps/stock-assistant/frontends/assistant && npm run build)` 退出码 0
- [ ] **AC-3**: 不引入新 npm 依赖
  - `git diff main -- apps/stock-assistant/frontends/assistant/package.json apps/stock-assistant/frontends/assistant/package-lock.json` 输出为空
- [ ] **AC-4**: 不动其它路径
  - `git diff main --name-only` 输出仅含 `apps/stock-assistant/frontends/assistant/vite.config.ts` + `docs/tasks/phaseF/assistant-frontend-proxy.md`
- [ ] **AC-5**: workbench proxy 模式一致 — `diff <(grep -A 10 "server:" apps/stock-assistant/frontends/workbench/vite.config.ts) <(grep -A 10 "server:" apps/stock-assistant/frontends/assistant/vite.config.ts)` 仅在端口号上不同（5173 vs 5174）

---

## 测试集合

```bash
(cd apps/stock-assistant/frontends/assistant && npm run type-check)
(cd apps/stock-assistant/frontends/assistant && npm run build)
git diff main -- apps/stock-assistant/frontends/assistant/package.json
git diff main --name-only
grep -A 10 "server:" apps/stock-assistant/frontends/assistant/vite.config.ts
```

---

## 文件影响范围

修改：
- `apps/stock-assistant/frontends/assistant/vite.config.ts`

新建：
- `docs/tasks/phaseF/assistant-frontend-proxy.md`

不允许改：所有其它路径。

---

## 引用

- **设计来源**：用户 bug 报告（5174 端口 ReviewAsk 抛 `SyntaxError: Unexpected token '<'`）
- **类比**：`apps/stock-assistant/frontends/workbench/vite.config.ts` 已有同款 proxy
