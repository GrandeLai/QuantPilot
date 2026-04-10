
import { TooltipProvider } from "@/components/ui/tooltip";
import { SentimentDashboard } from "./components/SentimentDashboard";

export default function App() {
  return (
    <TooltipProvider>
      <SentimentDashboard />
    </TooltipProvider>
  );
}
