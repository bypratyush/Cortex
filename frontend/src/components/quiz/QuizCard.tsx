"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight } from "lucide-react";
import Editor from "@monaco-editor/react";

interface Question {
  id: string;
  prompt: string;
  question_type: string;
  choices?: string[];
  starter_code?: string;
}

interface QuizCardProps {
  question: Question;
  currentIndex: number;
  total: number;
  onNext: (answer: string) => void;
}

export default function QuizCard({ question, currentIndex, total, onNext }: QuizCardProps) {
  const [answer, setAnswer] = useState<string>(question.starter_code || "");
  const [selectedChoice, setSelectedChoice] = useState<string | null>(null);

  // Reset state when question changes
  // We use key on the motion.div to force re-render, but this ensures internal state is clean
  if (question.question_type === "mcq" && answer !== selectedChoice && selectedChoice !== null) {
    setAnswer(selectedChoice);
  }

  const handleNext = () => {
    if (question.question_type === "mcq" && selectedChoice) {
      onNext(selectedChoice);
    } else {
      onNext(answer);
    }
    // Reset for next question
    setAnswer("");
    setSelectedChoice(null);
  };

  const isNextDisabled = () => {
    if (question.question_type === "mcq") return !selectedChoice;
    return answer.trim().length === 0;
  };

  return (
    <motion.div
      key={question.id}
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      transition={{ duration: 0.5, ease: "easeInOut" }}
      className="max-w-2xl mx-auto w-full"
    >
      {/* Progress */}
      <div className="flex items-center gap-4 mb-8">
        <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-indigo-500 rounded-full"
            initial={{ width: `${(currentIndex / total) * 100}%` }}
            animate={{ width: `${((currentIndex + 1) / total) * 100}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
        <span className="text-xs font-mono text-zinc-500 uppercase tracking-widest">
          {currentIndex + 1} / {total}
        </span>
      </div>

      <div className="bg-gradient-to-b from-white/[0.05] to-white/[0.02] border border-white/10 rounded-3xl p-8 md:p-12 shadow-2xl backdrop-blur-xl">
        <h2 className="font-serif text-3xl md:text-4xl text-white mb-8 leading-tight">
          {question.prompt}
        </h2>

        <div className="mb-10">
          {/* MCQ */}
          {question.question_type === "mcq" && question.choices && (
            <div className="space-y-3">
              {question.choices.map((choice, idx) => {
                const isSelected = selectedChoice === choice;
                return (
                  <button
                    key={idx}
                    onClick={() => setSelectedChoice(choice)}
                    className={`w-full text-left px-6 py-4 rounded-xl border transition-all ${
                      isSelected
                        ? "bg-indigo-500/20 border-indigo-500/50 text-white"
                        : "bg-white/5 border-white/10 text-zinc-300 hover:bg-white/10"
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-5 h-5 rounded-full border flex items-center justify-center ${
                        isSelected ? "border-indigo-400" : "border-zinc-600"
                      }`}>
                        {isSelected && <div className="w-2.5 h-2.5 rounded-full bg-indigo-400" />}
                      </div>
                      <span className="text-lg">{choice}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {/* Short Answer */}
          {question.question_type === "short_answer" && (
            <textarea
              autoFocus
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Type your answer here..."
              className="w-full bg-black/50 border border-white/10 rounded-2xl p-6 text-white text-lg focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 resize-none h-40 transition-all"
            />
          )}

          {/* Code Understanding (Read-only code + Text input) */}
          {question.question_type === "code_understanding" && (
            <div className="space-y-6">
              <div className="rounded-2xl overflow-hidden border border-white/10">
                <Editor
                  height="200px"
                  language="python"
                  theme="vs-dark"
                  value={question.starter_code || ""}
                  options={{ readOnly: true, minimap: { enabled: false }, fontSize: 14 }}
                />
              </div>
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Explain what the code does..."
                className="w-full bg-black/50 border border-white/10 rounded-2xl p-4 text-white focus:outline-none focus:border-indigo-500/50 resize-none h-24"
              />
            </div>
          )}

          {/* Coding Exercise (Editable Monaco) */}
          {question.question_type === "coding_exercise" && (
            <div className="rounded-2xl overflow-hidden border border-white/10 focus-within:border-indigo-500/50 transition-colors">
              <Editor
                height="300px"
                language="python"
                theme="vs-dark"
                value={answer}
                onChange={(val) => setAnswer(val || "")}
                options={{ minimap: { enabled: false }, fontSize: 14 }}
              />
            </div>
          )}
        </div>

        <div className="flex justify-end">
          <button
            onClick={handleNext}
            disabled={isNextDisabled()}
            className="flex items-center gap-2 bg-white text-black font-semibold px-8 py-3 rounded-full hover:bg-zinc-200 transition-all disabled:opacity-50 disabled:hover:bg-white"
          >
            {currentIndex === total - 1 ? "Submit Quiz" : "Next Question"}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </motion.div>
  );
}
