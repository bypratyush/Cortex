"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Check, Lock, BookOpen, Code2, Zap, ArrowRight, X, Map } from "lucide-react";
import { useRouter } from "next/navigation";
import { useRef, useState, useEffect } from "react";

export interface PathItem {
  id: string;
  concept_id: string;
  concept_slug: string;
  concept_name: string;
  position: number;
  item_type: "module" | "lesson" | "quiz" | "learn" | "review" | "practice" | "assessment";
  // Backend statuses: pending=locked, in_progress=active, completed=done
  status: "pending" | "in_progress" | "completed" | "skipped";
}

interface RoadmapModalProps {
  items: PathItem[];
  onClose: () => void;
}

const TYPE_CFG: Record<string, { label: string; color: string; shadow: string; Icon: any }> = {
  lesson:     { label: "Lesson", color: "#6366f1", shadow: "rgba(99,102,241,0.35)", Icon: Code2 },
  quiz:       { label: "Quiz",   color: "#8b5cf6", shadow: "rgba(139,92,246,0.35)", Icon: Zap },
  module:     { label: "Module", color: "#06b6d4", shadow: "rgba(6,182,212,0.35)",  Icon: BookOpen },
  learn:      { label: "Learn",  color: "#6366f1", shadow: "rgba(99,102,241,0.35)", Icon: Code2 },
  review:     { label: "Review", color: "#f59e0b", shadow: "rgba(245,158,11,0.35)", Icon: BookOpen },
  practice:   { label: "Practice", color: "#10b981", shadow: "rgba(16,185,129,0.35)", Icon: Code2 },
  assessment: { label: "Quiz",   color: "#8b5cf6", shadow: "rgba(139,92,246,0.35)", Icon: Zap },
};

function RoadmapNode({ item, idx, isLast, onClick }: {
  item: PathItem; idx: number; isLast: boolean; onClick: () => void;
}) {
  const isCompleted = item.status === "completed";
  const isActive    = item.status === "in_progress";
  const isLocked    = item.status === "pending" || item.status === "skipped";
  const cfg = TYPE_CFG[item.item_type] ?? TYPE_CFG.lesson;
  const { Icon } = cfg;

  return (
    <div className="relative flex items-center flex-shrink-0">
      {/* ── Card ── */}
      <motion.button
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: idx * 0.07, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        onClick={onClick}
        disabled={isLocked}
        whileHover={!isLocked ? { y: -4, scale: 1.02 } : {}}
        whileTap={!isLocked ? { scale: 0.97 } : {}}
        className={`relative flex flex-col w-52 rounded-2xl border text-left overflow-hidden transition-all duration-300 outline-none
          ${isActive    ? "border-white/20 bg-white/[0.06] cursor-pointer" :
            isCompleted ? "border-white/10 bg-white/[0.03] cursor-pointer" :
                          "border-white/5  bg-white/[0.01] cursor-not-allowed opacity-40"
          }`}
        style={{
          boxShadow: isActive
            ? `0 0 40px ${cfg.shadow}, 0 4px 24px rgba(0,0,0,0.6)`
            : isCompleted
            ? "0 4px 24px rgba(0,0,0,0.4)"
            : "none",
          backdropFilter: "blur(12px)",
        }}
      >
        {/* Top color strip */}
        <div
          className="h-1 w-full"
          style={{ background: isLocked ? "#27272a" : `linear-gradient(90deg, ${cfg.color}, ${cfg.color}88)` }}
        />

        <div className="p-5">
          {/* Icon + number */}
          <div className="flex items-center justify-between mb-4">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{
                background: isLocked ? "#18181b" : `${cfg.color}22`,
                border: `1.5px solid ${isLocked ? "#27272a" : cfg.color + "40"}`,
              }}
            >
              {isCompleted
                ? <Check className="w-5 h-5 text-emerald-400" strokeWidth={2.5} />
                : isLocked
                ? <Lock className="w-4 h-4 text-zinc-600" />
                : <Icon className="w-5 h-5" style={{ color: cfg.color }} />
              }
            </div>
            <span className="text-[10px] font-bold tracking-widest text-zinc-600 uppercase">
              #{idx + 1}
            </span>
          </div>

          {/* Badge */}
          <span
            className="inline-block text-[10px] font-bold tracking-widest uppercase px-2 py-0.5 rounded-full mb-2"
            style={{
              background: isLocked ? "#18181b" : `${cfg.color}18`,
              color: isLocked ? "#3f3f46" : cfg.color,
              border: `1px solid ${isLocked ? "#27272a" : cfg.color + "35"}`,
            }}
          >
            {cfg.label}
          </span>

          {/* Title */}
          <h3 className={`font-semibold text-sm leading-snug mb-3 ${
            isActive ? "text-white" : isCompleted ? "text-zinc-200" : "text-zinc-600"
          }`}>
            {item.concept_name}
          </h3>

          {/* Status row */}
          <div className="flex items-center justify-between">
            {isCompleted && (
              <span className="text-[11px] text-emerald-400 font-semibold flex items-center gap-1">
                <Check className="w-3 h-3" strokeWidth={3} /> Mastered
              </span>
            )}
            {isActive && (
              <span className="text-[11px] font-bold flex items-center gap-1" style={{ color: cfg.color }}>
                Start Now <ArrowRight className="w-3 h-3" />
              </span>
            )}
            {isLocked && (
              <span className="text-[11px] text-zinc-700 flex items-center gap-1">
                <Lock className="w-3 h-3" /> Locked
              </span>
            )}
          </div>
        </div>

        {/* Active glow pulse overlay */}
        {isActive && (
          <div
            className="absolute inset-0 rounded-2xl pointer-events-none animate-pulse"
            style={{ background: `radial-gradient(ellipse at top, ${cfg.color}08, transparent 70%)` }}
          />
        )}
      </motion.button>

      {/* ── Connector line to next node ── */}
      {!isLast && (
        <div className="flex items-center mx-3 flex-shrink-0 mt-2">
          <div className="flex items-center gap-1">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="rounded-full"
                style={{
                  width: 5,
                  height: 5,
                  background: isCompleted ? "#6366f1" : "#27272a",
                  opacity: isCompleted ? 1 - i * 0.25 : 0.4,
                }}
              />
            ))}
          </div>
          <ArrowRight
            className="w-3.5 h-3.5 ml-1"
            style={{ color: isCompleted ? "#6366f1" : "#3f3f46" }}
          />
        </div>
      )}
    </div>
  );
}

export default function RoadmapModal({ items, onClose }: RoadmapModalProps) {
  const router  = useRouter();
  const scrollRef = useRef<HTMLDivElement>(null);

  const handleNodeClick = (item: PathItem) => {
    if (item.status === "pending" || item.status === "skipped") return;
    onClose();
    router.push(`/lesson?conceptId=${item.concept_id}`);
  };

  // Scroll to active node on mount
  useEffect(() => {
    const activeIdx = items.findIndex(i => i.status === "active");
    if (activeIdx > 0 && scrollRef.current) {
      setTimeout(() => {
        scrollRef.current?.scrollTo({ left: activeIdx * 236, behavior: "smooth" });
      }, 400);
    }
  }, [items]);

  const completedCount = items.filter(i => i.status === "completed").length;
  const progressPct = Math.round((completedCount / Math.max(1, items.length)) * 100);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex flex-col items-center justify-center p-4 md:p-8"
        style={{ background: "rgba(0,0,0,0.85)", backdropFilter: "blur(16px)" }}
        onClick={(e) => e.target === e.currentTarget && onClose()}
      >
        <motion.div
          initial={{ opacity: 0, y: 32, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 16, scale: 0.97 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="relative w-full max-w-5xl rounded-3xl overflow-hidden border border-white/10"
          style={{ background: "linear-gradient(135deg, #0d0d12 0%, #0a0a0f 100%)" }}
        >
          {/* Header */}
          <div className="px-8 pt-8 pb-6 border-b border-white/[0.06] flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <Map className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-bold tracking-widest text-indigo-400 uppercase">Your Learning Roadmap</span>
              </div>
              <h2 className="font-serif text-2xl text-white mb-1">
                {items.length} concepts · Python Programming
              </h2>
              <p className="text-zinc-500 text-sm">
                Complete each lesson in order to unlock the next one
              </p>
            </div>

            <button
              onClick={onClose}
              className="w-9 h-9 rounded-xl flex items-center justify-center border border-white/10 bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white transition-all"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Progress bar */}
          <div className="px-8 py-4 border-b border-white/[0.06]">
            <div className="flex items-center justify-between text-xs text-zinc-500 mb-2">
              <span>{completedCount} of {items.length} concepts mastered</span>
              <span className="font-bold text-indigo-400">{progressPct}%</span>
            </div>
            <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{ background: "linear-gradient(90deg, #6366f1, #8b5cf6)" }}
                initial={{ width: 0 }}
                animate={{ width: `${progressPct}%` }}
                transition={{ delay: 0.3, duration: 0.8, ease: "easeOut" }}
              />
            </div>
          </div>

          {/* Horizontal Scroll Area */}
          <div
            ref={scrollRef}
            className="flex items-center px-8 py-8 overflow-x-auto gap-0 scrollbar-hide"
            style={{ scrollbarWidth: "none" }}
          >
            {items.map((item, idx) => (
              <RoadmapNode
                key={item.id}
                item={item}
                idx={idx}
                isLast={idx === items.length - 1}
                onClick={() => handleNodeClick(item)}
              />
            ))}
          </div>

          {/* Scroll hint */}
          <div className="absolute right-0 top-[40%] pointer-events-none"
            style={{ background: "linear-gradient(to left, #0a0a0f, transparent)", width: 80, height: 200 }}
          />

          {/* Footer */}
          <div className="px-8 py-5 border-t border-white/[0.06] flex items-center justify-between">
            <p className="text-xs text-zinc-600">
              ← Scroll to explore all {items.length} topics →
            </p>
            <button
              onClick={onClose}
              className="text-xs font-semibold text-zinc-400 hover:text-white transition-colors px-4 py-2 rounded-lg hover:bg-white/5"
            >
              Close
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
