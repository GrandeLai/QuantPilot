import React from 'react';
import { 
  Plus, 
  ChevronDown, 
  ChevronRight, 
  FileCode, 
  Settings, 
  Terminal,
  Database,
  BrainCircuit,
  Zap,
  BarChart3,
  Code2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';

export const Sidebar = () => {
  const [openSections, setOpenSections] = React.useState<Record<string, boolean>>({
    'trading-algorithms': true,
    'trading-algorithms-2': true,
  });

  const toggleSection = (id: string) => {
    setOpenSections(prev => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="w-64 h-full border-r border-[#30363d] bg-[#0d1117] flex flex-col">
      <ScrollArea className="flex-1">
        <div className="py-6">
          <div className="px-6 py-2 flex items-center justify-between text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em]">
            <span>My Strategies</span>
            <Plus className="w-3.5 h-3.5 cursor-pointer hover:text-primary transition-colors" />
          </div>
          <SidebarItem icon={FileCode} label="Strategy 1" />
          <SidebarItem icon={FileCode} label="Strategy 2" active />

          <div className="mt-8">
            <div className="px-6 py-2 flex items-center justify-between text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em]">
              <span>Templates</span>
              <Plus className="w-3.5 h-3.5 cursor-pointer hover:text-primary transition-colors" />
            </div>
            
            <SidebarItem 
              icon={Code2} 
              label="Trading Algorithms" 
              hasChildren 
              isOpen={openSections['trading-algorithms']}
              onClick={() => toggleSection('trading-algorithms')}
            >
              <SidebarItem icon={BarChart3} label="MA_Crossover" indent={1} />
              <SidebarItem icon={BarChart3} label="RSI_Mean_Reversion" indent={1} />
              <SidebarItem icon={BarChart3} label="Bollinger_Breakout" indent={1} />
            </SidebarItem>

            <SidebarItem 
              icon={Code2} 
              label="Machine Learning" 
              hasChildren 
              isOpen={openSections['trading-algorithms-2']}
              onClick={() => toggleSection('trading-algorithms-2')}
            >
              <SidebarItem icon={BarChart3} label="LSTM Predictor" indent={1} />
              <SidebarItem icon={BarChart3} label="XGBoost Classifier" indent={1} />
            </SidebarItem>

            <SidebarItem 
              icon={Database} 
              label="Trading Analyse" 
              hasChildren 
              isOpen={openSections['analyse']}
              onClick={() => toggleSection('analyse')}
            />
          </div>
        </div>
      </ScrollArea>

      <div className="p-4 border-t border-[#30363d] flex flex-col gap-1">
        <Button variant="ghost" size="sm" className="justify-start gap-3 h-9 text-muted-foreground hover:text-foreground hover:bg-[#161b22]">
          <Settings className="w-4 h-4" />
          <span className="text-sm font-medium">Settings</span>
        </Button>
        <Button variant="ghost" size="sm" className="justify-start gap-3 h-9 text-muted-foreground hover:text-foreground hover:bg-[#161b22]">
          <Terminal className="w-4 h-4" />
          <span className="text-sm font-medium">Debug Console</span>
        </Button>
      </div>
    </div>
  );
};

const SidebarItem = ({ 
  icon: Icon, 
  label, 
  active, 
  indent = 0, 
  hasChildren, 
  isOpen,
  onClick,
  children
}: any) => (
  <div>
    <div 
      className={cn(
        "flex items-center gap-3 px-6 py-2 text-sm cursor-pointer transition-all hover:bg-[#161b22] group",
        active ? "bg-primary/10 text-primary font-bold border-r-2 border-primary" : "text-gray-400 hover:text-white"
      )}
      style={{ paddingLeft: indent > 0 ? `${indent * 16 + 24}px` : undefined }}
      onClick={onClick}
    >
      <Icon className={cn("w-4 h-4 shrink-0 transition-transform group-hover:scale-110", active ? "text-primary" : "text-muted-foreground group-hover:text-white")} />
      <span className="truncate flex-1">{label}</span>
      {hasChildren && (
        <ChevronRight className={cn("w-3.5 h-3.5 text-muted-foreground transition-transform duration-200", isOpen && "rotate-90")} />
      )}
    </div>
    {hasChildren && isOpen && children}
  </div>
);
