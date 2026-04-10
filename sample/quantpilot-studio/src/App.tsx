/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { Sidebar } from './components/Sidebar';
import { EditorHeader, Console } from './components/EditorLayout';
import { CodeEditor } from './components/CodeEditor';
import { TooltipProvider } from './components/ui/tooltip';
import { TopNavbar } from './components/TopNavbar';
import { PortfolioDashboard } from './components/PortfolioDashboard';
import { StatusBar } from './components/StatusBar';

export default function App() {
  const [activeTab, setActiveTab] = React.useState('portfolio');

  return (
    <TooltipProvider>
      <div className="flex flex-col h-screen w-full overflow-hidden bg-[#0d1117] text-foreground font-sans">
        {/* Top Navigation Bar */}
        <TopNavbar activeTab={activeTab} onTabChange={setActiveTab} />

        <div className="flex flex-1 overflow-hidden">
          {activeTab === 'strategy' ? (
            <>
              {/* Sidebar */}
              <Sidebar />

              {/* Main Content Area (Strategy Editor) */}
              <div className="flex-1 flex flex-col min-w-0 bg-[#0d1117]">
                {/* Strategy Info Header */}
                <EditorHeader />

                {/* Editor Area */}
                <CodeEditor />

                {/* Bottom Console */}
                <Console />
              </div>
            </>
          ) : activeTab === 'portfolio' ? (
            <PortfolioDashboard />
          ) : (
            <div className="flex-1 flex items-center justify-center text-muted-foreground">
              <div className="text-center">
                <h2 className="text-xl font-bold mb-2">Coming Soon</h2>
                <p>The {activeTab} view is currently under development.</p>
              </div>
            </div>
          )}
        </div>

        {/* Global Status Bar */}
        <StatusBar />
      </div>
    </TooltipProvider>
  );
}

