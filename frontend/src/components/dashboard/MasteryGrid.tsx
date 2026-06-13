"use client";

import { motion } from "framer-motion";

interface MasteryRecord {
  concept_id: string;
  concept_slug: string;
  concept_name: string;
  mastery_score: number;
}

interface MasteryGridProps {
  masteryMap: MasteryRecord[];
}

export default function MasteryGrid({ masteryMap }: MasteryGridProps) {
  // Color logic: green >= 0.85, amber >= 0.5, red < 0.5
  const getColor = (score: number) => {
    if (score >= 0.85) return "bg-emerald-500";
    if (score >= 0.5) return "bg-amber-500";
    if (score > 0) return "bg-rose-500";
    return "bg-white/10";
  };

  const getTrackColor = (score: number) => {
    if (score >= 0.85) return "bg-emerald-500/10";
    if (score >= 0.5) return "bg-amber-500/10";
    if (score > 0) return "bg-rose-500/10";
    return "bg-white/5";
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-serif text-2xl text-white">Mastery Map</h3>
        <span className="text-xs font-bold tracking-widest text-zinc-500 uppercase">
          {masteryMap.length} Concepts
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
        {masteryMap.map((record, index) => (
          <motion.div
            key={record.concept_id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="flex flex-col justify-center p-4 rounded-2xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.04] transition-colors cursor-pointer group"
          >
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm font-medium text-white group-hover:text-indigo-300 transition-colors truncate pr-2">
                {record.concept_name}
              </span>
              <span className="text-xs text-zinc-500 font-mono">
                {Math.round(record.mastery_score * 100)}%
              </span>
            </div>
            
            {/* Progress bar */}
            <div className={`h-1.5 w-full rounded-full overflow-hidden ${getTrackColor(record.mastery_score)}`}>
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${record.mastery_score * 100}%` }}
                transition={{ duration: 1, delay: 0.2 + index * 0.05 }}
                className={`h-full rounded-full ${getColor(record.mastery_score)}`}
              />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
