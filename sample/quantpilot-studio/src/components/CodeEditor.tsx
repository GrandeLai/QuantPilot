import React from 'react';
import Editor from 'react-simple-code-editor';
import Prism from 'prismjs';
import 'prismjs/components/prism-python';
// No need for prism tomorrow theme if we use our own in index.css

const DEFAULT_CODE = `"""
在此编写您的策略代码。

可继承 BaseStrategy 并实现 on_bar 方法:
"""

from quantpilot.strategy.base import BaseStrategy, StrategyContext
from quantpilot.data.models import OHLCVBar

class MyStrategy(BaseStrategy):
    name = "我的策略"
    description = "策略描述"
    version = "1.0.0"
    default_params = {"period": 20}

    def on_bar(self, bar: OHLCVBar, context: StrategyContext) -> None:
        # 在此处理每根 K 线
        pass
`;

export const CodeEditor = () => {
  const [code, setCode] = React.useState(DEFAULT_CODE);

  return (
    <div className="flex-1 min-h-0 px-8 mb-6">
      <div className="h-full border border-[#30363d] bg-[#161b22]/40 rounded-xl overflow-hidden flex flex-col shadow-2xl">
        <div className="flex items-center justify-between px-4 h-10 border-b border-[#30363d] bg-[#161b22]/60">
          <div className="flex items-center gap-2 text-xs font-bold text-muted-foreground uppercase tracking-widest">
            <FileCode className="w-3.5 h-3.5" />
            main.py
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground/60">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-500/50" />
              PYTHON 3.10
            </div>
            <div className="h-3 w-px bg-[#30363d]" />
            <span className="text-[10px] font-mono text-muted-foreground/40 uppercase tracking-tighter">UTF-8</span>
          </div>
        </div>
        <div className="flex-1 overflow-auto custom-scrollbar relative">
          <div className="absolute left-0 top-0 bottom-0 w-12 bg-[#0d1117]/30 border-r border-[#30363d]/50 flex flex-col items-center pt-[20px] text-[11px] font-mono text-muted-foreground/30 select-none pointer-events-none">
            {code.split('\n').map((_, i) => (
              <div key={i} className="h-[21px] flex items-center justify-center">
                {i + 1}
              </div>
            ))}
          </div>
          <div className="pl-12 min-h-full">
            <Editor
              value={code}
              onValueChange={code => setCode(code)}
              highlight={code => Prism.highlight(code, Prism.languages.python, 'python')}
              padding={20}
              className="min-h-full"
              style={{
                fontFamily: '"JetBrains Mono", monospace',
                fontSize: 13,
                outline: 'none',
                lineHeight: '21px',
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

import { FileCode } from 'lucide-react';
