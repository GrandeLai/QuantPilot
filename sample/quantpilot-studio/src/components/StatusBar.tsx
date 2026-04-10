import React from 'react';

export const StatusBar = () => {
  return (
    <div className="h-8 border-t bg-[#0d1117] px-4 flex items-center justify-between text-[10px] text-muted-foreground shrink-0 z-50">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
          SERVER: CONNECTED
        </div>
        <span>LATENCY: 12MS</span>
      </div>
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <span className="font-bold text-white uppercase tracking-wider">BTC/USD:</span>
          <span className="font-mono">$64,231.50</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-bold text-white uppercase tracking-wider">ETH/USD:</span>
          <span className="font-mono">$3,452.12</span>
        </div>
      </div>
    </div>
  );
};
