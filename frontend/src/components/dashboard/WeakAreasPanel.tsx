"use client";

import { motion } from "framer-motion";
import { AlertCircle, Target } from "lucide-react";
import { useRouter } from "next/navigation";

interface MasteryRecord {
  concept_id: string;
  concept_slug: string;
  concept_name: string;
  mastery_score: number;
}

interface WeakAreasPanelProps {
  weakAreas: MasteryRecord[];
}

export default function WeakAreasPanel({ weakAreas }: WeakAreasPanelProps) {
  const router = useRouter();

  if (weakAreas.length === 0) {
    return null; // Or show a celebration message if there are no weak areas
  }

  return (
    <div className="rounded-3xl border border-white/5 bg-[#111111] p-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-rose-500/10 text-rose-400">
          <AlertCircle className="w-4 h-4" />
        </div>
        <h3 className="font-serif text-xl text-white tracking-tight">Areas to Strengthen</h3>
      </div>

      <div className="space-y-3">
        {weakAreas.map((area, index) => (
          <motion.div
            key={area.concept_id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="flex items-center justify-between p-4 rounded-2xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.04] transition-colors group"
          >
            <div>
              <p className="text-sm font-medium text-white mb-1 group-hover:text-rose-300 transition-colors">
                {area.concept_name}
              </p>
              <div className="flex items-center gap-2">
                <div className="w-16 h-1 bg-white/10 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-rose-500 rounded-full"
                    style={{ width: `${area.mastery_score * 100}%` }}
                  />
                </div>
                <span className="text-xs text-zinc-500">
                  {Math.round(area.mastery_score * 100)}% Mastery
                </span>
              </div>
            </div>
            
            <button
              onClick={() => router.push(`/quiz?conceptId=${area.concept_id}&quizType=practice`)}
              className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-white/5 text-zinc-300 hover:bg-rose-500 hover:text-white transition-all"
            >
              <Target className="w-3.5 h-3.5" /> Practice
            </button>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
