/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import PortfolioPanel from './components/PortfolioPanel';
import { 
  LayoutDashboard, 
  BarChart2, 
  Zap, 
  History, 
  Settings, 
  User,
  Bell,
  Search
} from 'lucide-react';
import { cn } from './lib/utils';

const NAV_ITEMS = [
  { id: 'dashboard', label: '看板', icon: LayoutDashboard },
  { id: 'strategy', label: '策略', icon: Zap },
  { id: 'trade', label: '交易', icon: BarChart2 },
  { id: 'backtest', label: '回测', icon: History },
  { id: 'portfolio', label: '组合', icon: Settings, active: true },
];

export default function App() {
  return (
    <div className="flex flex-col h-screen bg-[#0B0C0E]">
      {/* Top Navigation */}
      <header className="h-14 border-b border-[#2A2D35] bg-[#151619] flex items-center justify-between px-6 shrink-0">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
              <Zap size={20} className="text-black fill-black" />
            </div>
            <span className="text-xl font-bold text-white tracking-tight">QuantPilot</span>
          </div>
          
          <nav className="hidden md:flex items-center gap-1">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                className={cn(
                  "px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2",
                  item.active 
                    ? "bg-[#2A2D35] text-white" 
                    : "text-[#8E9299] hover:text-white hover:bg-[#1C1E22]"
                )}
              >
                <item.icon size={16} />
                {item.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-[#1C1E22] rounded-lg border border-[#2A2D35] text-[#8E9299]">
            <Search size={14} />
            <span className="text-xs">搜索...</span>
            <span className="text-[10px] bg-[#2A2D35] px-1.5 py-0.5 rounded border border-[#3A3D45]">⌘K</span>
          </div>
          <button className="text-[#8E9299] hover:text-white transition-colors relative">
            <Bell size={20} />
            <span className="absolute top-0 right-0 w-2 h-2 bg-[#FF4D4D] rounded-full border-2 border-[#151619]" />
          </button>
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#4A4D55] to-[#1C1E22] border border-[#2A2D35] flex items-center justify-center text-white text-xs font-bold cursor-pointer">
            JD
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <PortfolioPanel />
      </main>

      {/* Footer / Status Bar */}
      <footer className="h-8 border-t border-[#2A2D35] bg-[#151619] flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-[#00C087] animate-pulse" />
            <span className="text-[10px] text-[#8E9299] uppercase font-mono">Server: Connected</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-[#8E9299] uppercase font-mono">Latency: 12ms</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-[10px] text-[#8E9299] uppercase font-mono">BTC/USD: $64,231.50</span>
          <span className="text-[10px] text-[#8E9299] uppercase font-mono">ETH/USD: $3,452.12</span>
        </div>
      </footer>
    </div>
  );
}

