import React from 'react';
import { 
  CheckCircle2, 
  Terminal as TerminalIcon, 
  X, 
  Code2, 
  Play, 
  Search, 
  Filter,
  Save,
  RefreshCw
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

export const EditorHeader = () => {
  return (
    <div className="bg-[#0d1117] p-8 pb-4 space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <div className="flex items-center gap-2 text-[11px] font-bold text-muted-foreground uppercase tracking-[0.2em] mb-1">
            <Code2 className="w-3 h-3" />
            Strategy Development
          </div>
          <h1 className="text-4xl font-bold text-white tracking-tight">My Strategy</h1>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input 
              placeholder="搜索代码..." 
              className="h-10 w-64 bg-[#161b22] border-[#30363d] pl-10 focus-visible:ring-primary"
            />
          </div>
          <Button variant="outline" size="icon" className="h-10 w-10 border-[#30363d] bg-[#161b22]">
            <Filter className="w-4 h-4" />
          </Button>
          <Button className="h-10 px-6 bg-white text-black hover:bg-gray-200 font-bold">
            <Play className="w-4 h-4 mr-2 fill-current" />
            Run Backtest
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-6 px-4 py-3 bg-[#161b22]/40 border border-[#30363d] rounded-xl">
        <div className="flex-1 max-w-[300px]">
          <label className="text-[10px] uppercase font-bold text-muted-foreground mb-1.5 block tracking-wider">Strategy Name</label>
          <Input 
            defaultValue="My Strategy" 
            className="h-9 bg-[#0d1117] border-[#30363d] focus-visible:ring-primary text-sm"
          />
        </div>
        <div className="flex-1">
          <label className="text-[10px] uppercase font-bold text-muted-foreground mb-1.5 block tracking-wider">Description</label>
          <Input 
            placeholder="Strategy description here (optional)" 
            className="h-9 bg-[#0d1117] border-[#30363d] focus-visible:ring-primary text-sm"
          />
        </div>
        <div className="flex items-end h-full pb-1 gap-4">
          <div className="flex items-center gap-1.5 text-[11px] text-green-500 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Auto-saved
          </div>
          <Button variant="ghost" size="sm" className="h-8 gap-2 text-muted-foreground hover:text-foreground">
            <Save className="w-3.5 h-3.5" />
            Save Now
          </Button>
        </div>
      </div>
    </div>
  );
};

export const Console = () => {
  return (
    <div className="h-64 mx-8 mb-8 border border-[#30363d] bg-[#161b22]/40 rounded-xl flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-4 h-10 border-b border-[#30363d] bg-[#161b22]/60">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
          <TerminalIcon className="w-3.5 h-3.5" />
          Debug Console
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-foreground">
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-foreground">
            <X className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>
      <div className="flex-1 p-4 font-mono text-xs text-muted-foreground overflow-auto">
        <div className="flex gap-2 mb-1.5">
          <span className="text-blue-400 font-bold">[INFO]</span>
          <span>Initializing QuantPilot engine...</span>
        </div>
        <div className="flex gap-2 mb-1.5">
          <span className="text-blue-400 font-bold">[INFO]</span>
          <span>Loading strategy: My Strategy v1.0.0</span>
        </div>
        <div className="flex gap-2 mb-1.5">
          <span className="text-green-400 font-bold">[SUCCESS]</span>
          <span>Engine ready. Waiting for backtest command.</span>
        </div>
        <div className="flex gap-2 mb-1.5">
          <span className="text-muted-foreground/50">---</span>
        </div>
        <div className="flex gap-2 mb-1.5">
          <span className="text-yellow-400 font-bold">[WARN]</span>
          <span>Strategy uses deprecated API: context.get_history(). Use context.data instead.</span>
        </div>
      </div>
    </div>
  );
};
