"use client";

import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, ChevronDown, Check, X, Loader2 } from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";

interface ContextNudgeModalProps {
  onDismiss: () => void;
  conceptCount: number;
}

export default function ContextNudgeModal({ onDismiss, conceptCount }: ContextNudgeModalProps) {
  const userId = useAuthStore((s) => s.userId);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [context, setContext] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleNudgeClick = () => {
    if (!isExpanded) {
      setIsExpanded(true);
      // Small delay so the animation plays before focus
      setTimeout(() => textareaRef.current?.focus(), 350);
    } else {
      // If already expanded, re-focus the textarea
      textareaRef.current?.focus();
      setIsFocused(true);
    }
  };

  const handleSave = async () => {
    if (!context.trim() || !userId) return;
    setSaving(true);
    try {
      await api.put(`/onboarding/users/${userId}/profile`, {
        domain_key: "python_programming",
        goal: "career_growth",
        target_level: "job_ready",
        time_commitment: "1_hr_per_day",
        learning_style: "mixed",
        motivation: "career",
        current_level_summary: context.trim(),
      });
      setSaved(true);
      setTimeout(() => onDismiss(), 1200);
    } catch (e) {
      console.error("Failed to save context:", e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 40, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, scale: 0.97 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 w-full max-w-lg"
    >
      <div className="bg-[#111111] border border-white/10 rounded-3xl shadow-2xl shadow-black/60 overflow-hidden">

        {/* Header Row */}
        <div className="flex items-start justify-between px-6 pt-6 pb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-bold tracking-widest text-emerald-400 uppercase">
                Path Ready
              </span>
            </div>
            <h3 className="text-white font-serif text-xl leading-tight">
              Your curriculum is built.
            </h3>
            <p className="text-zinc-500 text-sm mt-0.5">
              {conceptCount} concepts · personalized to your profile
            </p>
          </div>
          <button
            onClick={onDismiss}
            className="text-zinc-600 hover:text-zinc-400 transition-colors mt-0.5"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Divider */}
        <div className="h-px bg-white/5 mx-6" />

        {/* Nudge Section */}
        <div className="px-6 py-4">
          <button
            onClick={handleNudgeClick}
            className="group w-full flex items-center justify-between rounded-2xl border border-white/8 bg-white/3 hover:bg-white/6 px-4 py-3 transition-all duration-200"
          >
            <div className="flex items-center gap-3">
              <div className="w-7 h-7 rounded-xl bg-indigo-500/15 flex items-center justify-center">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              </div>
              <div className="text-left">
                <p className="text-white text-sm font-medium">
                  Make it yours
                </p>
                <p className="text-zinc-500 text-xs">
                  Add your background — lessons and tutor adapt to it
                </p>
              </div>
            </div>
            <motion.div
              animate={{ rotate: isExpanded ? 180 : 0 }}
              transition={{ duration: 0.25 }}
            >
              <ChevronDown className="w-4 h-4 text-zinc-600" />
            </motion.div>
          </button>

          {/* Sliding Input */}
          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                className="overflow-hidden"
              >
                <div className="pt-3">
                  <motion.div
                    animate={{
                      borderColor: isFocused
                        ? "rgba(99, 102, 241, 0.5)"
                        : "rgba(255,255,255,0.06)",
                      boxShadow: isFocused
                        ? "0 0 0 3px rgba(99,102,241,0.1)"
                        : "none",
                    }}
                    transition={{ duration: 0.2 }}
                    className="rounded-2xl border bg-black/30 overflow-hidden"
                  >
                    <motion.textarea
                      ref={textareaRef}
                      value={context}
                      onChange={(e) => setContext(e.target.value)}
                      onFocus={() => setIsFocused(true)}
                      onBlur={() => setIsFocused(false)}
                      animate={{ height: isFocused ? 120 : 72 }}
                      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                      placeholder="e.g. I'm a JavaScript developer learning Python. I'm comfortable with async patterns but weak on OOP. I have a backend interview in 6 weeks..."
                      className="w-full bg-transparent text-white text-sm px-4 pt-3 pb-2 resize-none focus:outline-none placeholder-zinc-600 leading-relaxed"
                      style={{ height: isFocused ? 120 : 72 }}
                    />
                    <div className="flex items-center justify-between px-4 pb-3">
                      <span className="text-zinc-600 text-xs">
                        {context.length}/2000
                      </span>
                      <button
                        onClick={handleSave}
                        disabled={!context.trim() || saving || saved}
                        className={`flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all ${
                          saved
                            ? "bg-emerald-500/20 text-emerald-400"
                            : context.trim()
                            ? "bg-indigo-500 text-white hover:bg-indigo-400"
                            : "bg-white/5 text-zinc-600 cursor-not-allowed"
                        }`}
                      >
                        {saving ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : saved ? (
                          <>
                            <Check className="w-3 h-3" /> Saved
                          </>
                        ) : (
                          "Save context"
                        )}
                      </button>
                    </div>
                  </motion.div>
                  <p className="text-zinc-600 text-xs px-1 mt-2">
                    This context enriches your lessons and tutor — not the curriculum structure.
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div className="px-6 pb-5">
          <button
            onClick={onDismiss}
            className="w-full flex items-center justify-center gap-2 bg-white text-black text-sm font-semibold rounded-2xl py-3 hover:bg-zinc-100 transition-colors"
          >
            Start Learning →
          </button>
        </div>
      </div>
    </motion.div>
  );
}
