"use client";

import { motion } from "framer-motion";
import { CheckCircle2, XCircle, ArrowRight, BookOpen, MessageCircle } from "lucide-react";
import { useRouter } from "next/navigation";

interface QuestionResult {
  question_id: string;
  is_correct: boolean;
  explanation: string;
  expected_answer: string;
  learner_answer: string;
}

interface ResultsScreenProps {
  score: number;
  total: number;
  accuracy: number;
  feedback: QuestionResult[];
  onAskTutor?: () => void;
}

export default function ResultsScreen({ score, total, accuracy, feedback, onAskTutor }: ResultsScreenProps) {
  const router = useRouter();
  
  const isPass = accuracy >= 0.7;

  return (
    <div className="max-w-3xl mx-auto w-full py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-16"
      >
        <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-white/5 border border-white/10 mb-6 relative">
          <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50" cy="50" r="46"
              fill="transparent"
              stroke="rgba(255,255,255,0.1)"
              strokeWidth="4"
            />
            <motion.circle
              cx="50" cy="50" r="46"
              fill="transparent"
              stroke={isPass ? "#10b981" : "#f43f5e"} // Emerald or Rose
              strokeWidth="4"
              strokeDasharray={289}
              strokeDashoffset={289}
              animate={{ strokeDashoffset: 289 - (289 * accuracy) }}
              transition={{ duration: 1.5, ease: "easeOut", delay: 0.5 }}
            />
          </svg>
          <span className="font-serif text-3xl font-bold text-white relative z-10">
            {score}<span className="text-xl text-zinc-500">/{total}</span>
          </span>
        </div>
        
        <h2 className="font-serif text-5xl tracking-tight text-white mb-4">
          {isPass ? "Mastery Achieved" : "Needs Review"}
        </h2>
        <p className="text-zinc-400 text-lg">
          {isPass 
            ? "Excellent work. You have demonstrated a solid understanding."
            : "You're getting there. Review the feedback and try practicing again."}
        </p>
      </motion.div>

      <div className="space-y-6 mb-16">
        {feedback.map((item, idx) => (
          <motion.div
            key={item.question_id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + idx * 0.1 }}
            className={`rounded-2xl border p-6 ${
              item.is_correct 
                ? "bg-emerald-500/5 border-emerald-500/20" 
                : "bg-rose-500/5 border-rose-500/20"
            }`}
          >
            <div className="flex items-start gap-4">
              <div className="mt-1">
                {item.is_correct ? (
                  <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                ) : (
                  <XCircle className="w-6 h-6 text-rose-500" />
                )}
              </div>
              <div className="flex-1">
                <h4 className="text-white font-medium mb-4">Question {idx + 1}</h4>
                
                <div className="bg-black/30 rounded-xl p-4 mb-4 border border-white/5">
                  <p className="text-sm text-zinc-500 uppercase tracking-wider mb-1">Your Answer</p>
                  <p className={`text-base ${item.is_correct ? "text-emerald-300" : "text-rose-300"}`}>
                    {item.learner_answer}
                  </p>
                </div>

                {!item.is_correct && (
                  <div className="bg-emerald-500/10 rounded-xl p-4 mb-4 border border-emerald-500/20">
                    <p className="text-sm text-emerald-500 uppercase tracking-wider mb-1">Expected Answer</p>
                    <p className="text-base text-emerald-100">{item.expected_answer}</p>
                  </div>
                )}

                <div className="text-zinc-300 leading-relaxed">
                  <span className="font-semibold text-white">Feedback: </span>
                  {item.explanation}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <button
          onClick={() => router.push("/dashboard")}
          className="flex justify-center items-center gap-2 bg-white text-black font-semibold px-8 py-4 rounded-full hover:bg-zinc-200 transition-all"
        >
          <BookOpen className="w-5 h-5" />
          Continue Learning
        </button>
        <button
          onClick={onAskTutor}
          className="flex justify-center items-center gap-2 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-semibold px-8 py-4 rounded-full hover:bg-indigo-500/20 transition-all"
        >
          <MessageCircle className="w-5 h-5" />
          Ask Tutor About This
        </button>
      </div>
    </div>
  );
}
