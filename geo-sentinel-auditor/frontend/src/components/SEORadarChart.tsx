import { useState, useEffect } from "react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";

interface Props {
  data: {
    overall: number;
    google: number;
    content: number;
    social: number;
  };
}

export function SEORadarChart({ data }: Props) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const chartData = [
    { subject: "Overall", A: data.overall, fullMark: 100 },
    { subject: "Google Presence", A: data.google, fullMark: 100 },
    { subject: "Content", A: data.content, fullMark: 100 },
    { subject: "Social", A: data.social, fullMark: 100 },
  ];

  if (!isMounted) return <div className="w-full h-[300px] mt-4 mb-8 bg-white/5 animate-pulse rounded-full" />;

  return (
    <div className="w-full h-[300px] min-h-[300px] mt-4 mb-8 relative">
      <ResponsiveContainer width="100%" height="100%" debounce={100}>
        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
          <PolarGrid stroke="#374151" />
          <PolarAngleAxis 
            dataKey="subject" 
            tick={{ fill: "#9ca3af", fontSize: 11 }} 
          />
          <PolarRadiusAxis 
            angle={30} 
            domain={[0, 100]} 
            tick={false} 
            axisLine={false} 
          />
          <Radar
            name="SEO Score"
            dataKey="A"
            stroke="#818cf8"
            fill="#818cf8"
            fillOpacity={0.6}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
