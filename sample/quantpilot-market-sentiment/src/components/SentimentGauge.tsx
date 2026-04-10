
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { motion } from 'motion/react';

interface SentimentGaugeProps {
  score: number;
}

export function SentimentGauge({ score }: SentimentGaugeProps) {
  // Map score (0-100) to rotation (-90 to 90 degrees)
  const rotation = (score / 100) * 180 - 90;

  const getSentimentLabel = (s: number) => {
    if (s >= 75) return { label: '极度看涨', color: 'text-emerald-500', bg: 'bg-emerald-500/10' };
    if (s >= 60) return { label: '看涨', color: 'text-green-500', bg: 'bg-green-500/10' };
    if (s >= 40) return { label: '中性', color: 'text-yellow-500', bg: 'bg-yellow-500/10' };
    if (s >= 25) return { label: '看跌', color: 'text-orange-500', bg: 'bg-orange-500/10' };
    return { label: '极度看跌', color: 'text-red-500', bg: 'bg-red-500/10' };
  };

  const sentiment = getSentimentLabel(score);

  return (
    <Card className="bg-muted/10 border-border h-full overflow-hidden">
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground">市场情绪指数</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center justify-center pt-4">
        <div className="relative w-48 h-24 overflow-hidden">
          {/* Gauge Background */}
          <svg viewBox="0 0 100 50" className="w-full h-full">
            <path
              d="M 10 50 A 40 40 0 0 1 90 50"
              fill="none"
              stroke="currentColor"
              strokeWidth="12"
              className="text-muted/20"
              strokeLinecap="round"
            />
            {/* Gradient Path */}
            <defs>
              <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#ef5350" />
                <stop offset="50%" stopColor="#fdd835" />
                <stop offset="100%" stopColor="#26a69a" />
              </linearGradient>
            </defs>
            <path
              d="M 10 50 A 40 40 0 0 1 90 50"
              fill="none"
              stroke="url(#gaugeGradient)"
              strokeWidth="12"
              strokeLinecap="round"
              opacity="0.8"
            />
          </svg>

          {/* Needle */}
          <motion.div
            className="absolute bottom-0 left-1/2 w-1 h-16 bg-foreground origin-bottom -translate-x-1/2"
            initial={{ rotate: -90 }}
            animate={{ rotate: rotation }}
            transition={{ type: 'spring', stiffness: 60, damping: 15 }}
          >
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3 h-3 bg-foreground rounded-full border-2 border-background shadow-lg" />
          </motion.div>
        </div>

        <div className="mt-4 text-center">
          <div className="text-4xl font-black tracking-tighter">{score}</div>
          <div className={`mt-1 px-3 py-1 rounded-full text-xs font-bold ${sentiment.bg} ${sentiment.color}`}>
            {sentiment.label}
          </div>
        </div>

        <div className="w-full mt-6 grid grid-cols-3 gap-2 text-[10px] uppercase font-bold text-muted-foreground text-center">
          <div>看跌</div>
          <div>中性</div>
          <div>看涨</div>
        </div>
      </CardContent>
    </Card>
  );
}
