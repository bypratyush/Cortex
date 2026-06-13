"use client";

import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";

interface NextActionProps {
  action: {
    learning_path_item_id: string;
    concept_id: string;
    concept_name: string;
    item_type: string;
    reason: string | null;
  };
}

export default function NextActionCard({ action }: NextActionProps) {
  const router = useRouter();

  const handleStart = () => {
    // If it's a review or learn, go to lesson page. (We'll handle quizzes later)
    router.push(`/lesson?conceptId=${action.concept_id}&pathItemId=${action.learning_path_item_id}`);
  };

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="relative group rounded-3xl bg-gradient-to-b from-white/5 to-white/[0.02] border border-white/10 p-8 overflow-hidden"
    >
      {/* Background glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 blur-[80px] rounded-full pointer-events-none group-hover:bg-indigo-500/20 transition-colors duration-500" />
      
      <div className="relative z-10">
        <div className="flex items-center gap-2 mb-4">
          <div className="flex items-center justify-center w-6 h-6 rounded-lg bg-indigo-500/20 border border-indigo-500/30">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          </div>
          <span className="text-xs font-bold tracking-widest text-indigo-400 uppercase">
            Up Next
          </span>
          <span className="text-xs font-semibold tracking-wider text-zinc-600 uppercase ml-2 px-2 py-0.5 rounded-full border border-white/10 bg-black/20">
            {action.item_type}
          </span>
        </div>

        <h3 className="font-serif text-3xl md:text-4xl text-white tracking-tight mb-3">
          {action.concept_name}
        </h3>

        {action.reason && (
          <p className="text-zinc-400 text-sm leading-relaxed mb-8 max-w-md italic">
            "{action.reason}"
          </p>
        )}

        <button
          onClick={handleStart}
          className="flex items-center gap-2 bg-white text-black text-sm font-semibold px-6 py-3 rounded-full hover:bg-zinc-200 transition-colors"
        >
          Begin {action.item_type === "review" ? "Review" : "Lesson"} <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  );
}
