
import React from 'react';
import { Search, Bell, User, LayoutDashboard, TrendingUp, ArrowLeftRight, History, ShieldCheck, Briefcase, Cpu, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export function Header() {
  return (
    <header className="h-14 border-b border-border bg-background flex items-center justify-between px-4 sticky top-0 z-50">
      <div className="flex items-center gap-8">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <TrendingUp className="text-primary-foreground w-5 h-5" />
          </div>
          <span className="font-bold text-xl tracking-tight">QuantPilot</span>
        </div>

        <nav className="hidden md:flex items-center gap-1">
          <NavItem icon={<LayoutDashboard size={16} />} label="看盘" active />
          <NavItem icon={<TrendingUp size={16} />} label="策略" />
          <NavItem icon={<ArrowLeftRight size={16} />} label="交易" />
          <NavItem icon={<History size={16} />} label="回测" />
          <NavItem icon={<ShieldCheck size={16} />} label="期权" />
          <NavItem icon={<Briefcase size={16} />} label="组合" />
          <NavItem icon={<Cpu size={16} />} label="AI" />
          <NavItem icon={<Settings size={16} />} label="系统" />
        </nav>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative hidden lg:block">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="搜索... ⌘K"
            className="w-64 pl-9 h-9 bg-muted/50 border-none focus-visible:ring-1"
          />
        </div>
        <Button variant="ghost" size="icon" className="relative">
          <Bell size={20} />
          <span className="absolute top-2 right-2 w-2 h-2 bg-destructive rounded-full border-2 border-background" />
        </Button>
        <div className="flex items-center gap-2 pl-2 border-l border-border">
          <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-xs font-bold">
            QP
          </div>
        </div>
      </div>
    </header>
  );
}

function NavItem({ icon, label, active = false }: { icon: React.ReactNode, label: string, active?: boolean }) {
  return (
    <Button
      variant={active ? "secondary" : "ghost"}
      size="sm"
      className={`flex items-center gap-2 px-3 h-9 ${active ? 'bg-muted' : 'text-muted-foreground hover:text-foreground'}`}
    >
      {icon}
      <span>{label}</span>
    </Button>
  );
}
