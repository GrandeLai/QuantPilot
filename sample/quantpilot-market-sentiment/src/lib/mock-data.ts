
export interface SentimentData {
  timestamp: string;
  bullish: number;
  bearish: number;
  neutral: number;
  score: number; // 0 to 100
}

export interface NewsItem {
  id: string;
  title: string;
  source: string;
  time: string;
  sentiment: 'bullish' | 'bearish' | 'neutral';
  impact: 'high' | 'medium' | 'low';
  summary: string;
}

export const mockSentimentHistory: SentimentData[] = [
  { timestamp: '09:00', bullish: 65, bearish: 25, neutral: 10, score: 72 },
  { timestamp: '10:00', bullish: 60, bearish: 30, neutral: 10, score: 68 },
  { timestamp: '11:00', bullish: 55, bearish: 35, neutral: 10, score: 62 },
  { timestamp: '12:00', bullish: 45, bearish: 45, neutral: 10, score: 50 },
  { timestamp: '13:00', bullish: 40, bearish: 50, neutral: 10, score: 45 },
  { timestamp: '14:00', bullish: 35, bearish: 55, neutral: 10, score: 40 },
  { timestamp: '15:00', bullish: 30, bearish: 60, neutral: 10, score: 35 },
  { timestamp: '16:00', bullish: 25, bearish: 65, neutral: 10, score: 30 },
];

export const mockNews: NewsItem[] = [
  {
    id: '1',
    title: 'Apple Reports Record Q2 Earnings, Beats Expectations',
    source: 'Bloomberg',
    time: '10 mins ago',
    sentiment: 'bullish',
    impact: 'high',
    summary: 'Apple Inc. announced financial results for its fiscal 2024 second quarter ended March 30, 2024. The company posted a quarterly revenue of $90.8 billion.'
  },
  {
    id: '2',
    title: 'iPhone Sales in China Face Stiff Competition',
    source: 'Reuters',
    time: '45 mins ago',
    sentiment: 'bearish',
    impact: 'medium',
    summary: 'Apple is facing increasing pressure in the Chinese market as local competitors gain market share with aggressive pricing and new features.'
  },
  {
    id: '3',
    title: 'Apple Announces New AI Integration for iOS 18',
    source: 'TechCrunch',
    time: '2 hours ago',
    sentiment: 'bullish',
    impact: 'high',
    summary: 'Apple is set to unveil a major overhaul of its operating system with deep AI integration across all native apps.'
  },
  {
    id: '4',
    title: 'Global Supply Chain Issues May Affect iPad Production',
    source: 'CNBC',
    time: '4 hours ago',
    sentiment: 'neutral',
    impact: 'low',
    summary: 'Recent logistical challenges in Southeast Asia could lead to minor delays in the shipment of next-generation iPad models.'
  },
  {
    id: '5',
    title: 'Analyst Downgrades AAPL Target Price to $190',
    source: 'Morgan Stanley',
    time: '6 hours ago',
    sentiment: 'bearish',
    impact: 'medium',
    summary: 'Analysts cite slowing growth in services revenue as a primary concern for the upcoming fiscal year.'
  }
];
