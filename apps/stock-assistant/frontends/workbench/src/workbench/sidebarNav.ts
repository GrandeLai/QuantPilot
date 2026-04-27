/**
 * 侧栏导航配置 — 每个 WorkbenchTab 对应的二级导航项列表.
 */

import {
  Activity,
  BarChart2,
  BookOpen,
  Brain,
  Briefcase,
  FlaskConical,
  LineChart,
  List,
  PlayCircle,
  Shield,
  TrendingUp,
  Zap,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { WorkbenchTab } from "./navigation";

export interface SidebarNavItem {
  key: string;
  label: string;
  icon: LucideIcon;
  description: string;
}

/** 每个 Tab 的侧栏导航项（按展示顺序排列）. */
export const SIDEBAR_NAV: Record<WorkbenchTab, SidebarNavItem[]> = {
  research: [
    {
      key: "quant_research",
      label: "量化研究",
      icon: Brain,
      description: "因子库 · ML训练 · 参数优化",
    },
    {
      key: "market",
      label: "行情总览",
      icon: Activity,
      description: "多市场实时行情",
    },
    {
      key: "screener",
      label: "因子筛选",
      icon: List,
      description: "资产筛选与评分",
    },
    {
      key: "chart",
      label: "K线图表",
      icon: BarChart2,
      description: "加密资产历史图表",
    },
  ],

  strategy: [
    {
      key: "strategy_workshop",
      label: "策略工坊",
      icon: BookOpen,
      description: "创建与编辑策略代码",
    },
  ],

  validation: [
    {
      key: "autopilot",
      label: "AutoPilot",
      icon: Zap,
      description: "一键启动全量化流程",
    },
    {
      key: "validation_lab",
      label: "验证实验室",
      icon: FlaskConical,
      description: "Walk-Forward 验证",
    },
    {
      key: "crypto_research",
      label: "ML 研究摘要",
      icon: Brain,
      description: "LightGBM 训练结果",
    },
    {
      key: "backtest",
      label: "策略回测",
      icon: PlayCircle,
      description: "加密策略历史回测",
    },
  ],

  run: [
    {
      key: "trading",
      label: "交易执行",
      icon: Zap,
      description: "实盘 / 模拟盘",
    },
    {
      key: "crypto_spot",
      label: "加密现货",
      icon: TrendingUp,
      description: "BTC / ETH 现货",
    },
    {
      key: "crypto_futures",
      label: "加密合约",
      icon: LineChart,
      description: "永续合约",
    },
    {
      key: "crypto_options",
      label: "加密期权",
      icon: Shield,
      description: "期权交易",
    },
  ],

  risk_review: [
    {
      key: "portfolio",
      label: "持仓组合",
      icon: Briefcase,
      description: "持仓与净值曲线",
    },
    {
      key: "backtest",
      label: "历史回测",
      icon: PlayCircle,
      description: "策略历史表现",
    },
    {
      key: "crypto_portfolio",
      label: "加密持仓",
      icon: TrendingUp,
      description: "加密资产组合",
    },
    {
      key: "crypto_orders",
      label: "加密订单",
      icon: List,
      description: "历史委托记录",
    },
  ],
};

/** 每个 Tab 进入时默认选中的导航项. */
export const SECTION_DEFAULT: Record<WorkbenchTab, string> = {
  research: "quant_research",
  strategy: "strategy_workshop",
  validation: "autopilot",
  run: "trading",
  risk_review: "portfolio",
};
