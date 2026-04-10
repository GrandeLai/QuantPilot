import React from 'react';
import { 
  Zap, 
  LayoutGrid, 
  BarChart3, 
  History, 
  Settings, 
  Search, 
  Bell,
  Command
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface NavItemProps {
  icon: React.ElementType;
  label: string;
  active?: boolean;
  onClick?: () => void;
}

const NavItem = ({ icon: Icon, label, active, onClick }: NavItemProps) => (
  <div 
    onClick={onClick}
    className={cn(
      "flex items-center gap-2 px-3 py-1.5 rounded-md cursor-pointer transition-all text-sm font-medium",
      active 
        ? "bg-[#21262d] text-foreground" 
        : "text-muted-foreground hover:text-foreground hover:bg-accent/30"
    )}
  >
    <Icon className="w-4 h-4" />
    <span>{label}</span>
  </div>
);

export const TopNavbar = ({ activeTab, onTabChange }: { activeTab: string, onTabChange: (tab: string) => void }) => {
  return (
    <div className="h-14 border-b bg-[#0d1117] flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-8">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center text-black">
            <Zap className="w-5 h-5 fill-current" />
          </div>
          <span className="font-bold text-xl tracking-tight text-white">QuantPilot</span>
        </div>

        {/* Navigation */}
        <nav className="flex items-center gap-2">
          <NavItem icon={LayoutGrid} label="看板" active={activeTab === 'dashboard'} onClick={() => onTabChange('dashboard')} />
          <NavItem icon={Zap} label="策略" active={activeTab === 'strategy'} onClick={() => onTabChange('strategy')} />
          <NavItem icon={BarChart3} label="交易" active={activeTab === 'trading'} onClick={() => onTabChange('trading')} />
          <NavItem icon={History} label="回测" active={activeTab === 'backtest'} onClick={() => onTabChange('backtest')} />
          <NavItem icon={Settings} label="组合" active={activeTab === 'portfolio'} onClick={() => onTabChange('portfolio')} />
        </nav>
      </div>

      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="relative group">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors">
            <Search className="w-4 h-4" />
          </div>
          <Input 
            placeholder="搜索..." 
            className="h-9 w-64 bg-[#161b22] border-[#30363d] pl-9 pr-12 text-sm focus-visible:ring-1 focus-visible:ring-primary"
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-0.5 px-1.5 py-0.5 rounded border border-[#30363d] bg-[#0d1117] text-[10px] text-muted-foreground font-mono">
            <Command className="w-2.5 h-2.5" />
            <span>K</span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" className="relative h-9 w-9 text-muted-foreground hover:text-foreground">
            <Bell className="w-5 h-5" />
            <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-[#0d1117]" />
          </Button>
          
          <div className="w-8 h-8 rounded-full bg-[#30363d] flex items-center justify-center text-xs font-bold text-white cursor-pointer hover:ring-2 hover:ring-primary/50 transition-all">
            JD
          </div>
        </div>
      </div>
    </div>
  );
};
