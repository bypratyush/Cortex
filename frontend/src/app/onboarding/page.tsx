"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Check, Loader2 } from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";

// ─── Types ────────────────────────────────────────────────────────────────────
type GoalType = "career_growth" | "college_course" | "build_projects" | "interview_preparation" | "hobby";
type TargetLevel = "beginner" | "intermediate" | "advanced" | "job_ready";
type TimeCommitment = "15_min_per_day" | "30_min_per_day" | "1_hr_per_day" | "2_plus_hr_per_day";
type LearningStyle = "reading" | "examples" | "practice" | "mixed";
type MotivationType = "curiosity" | "career" | "exams" | "building_products";

interface Answers {
  goal: GoalType | null;
  target_level: TargetLevel | null;
  time_commitment: TimeCommitment | null;
  learning_style: LearningStyle | null;
  motivation: MotivationType | null;
}

// ─── Config ───────────────────────────────────────────────────────────────────
const GOALS: { value: GoalType; emoji: string; label: string; desc: string }[] = [
  { value: "career_growth", emoji: "🎯", label: "Career Growth", desc: "Level up professionally" },
  { value: "college_course", emoji: "🎓", label: "College Course", desc: "Ace your coursework" },
  { value: "build_projects", emoji: "🛠️", label: "Build Projects", desc: "Ship real things" },
  { value: "interview_preparation", emoji: "💼", label: "Interview Prep", desc: "Land the role" },
  { value: "hobby", emoji: "🌱", label: "Personal Hobby", desc: "Learn for the joy of it" },
];

const LEVELS: { value: TargetLevel; label: string; desc: string }[] = [
  { value: "beginner", label: "Beginner", desc: "Starting from scratch" },
  { value: "intermediate", label: "Intermediate", desc: "Have some foundations" },
  { value: "advanced", label: "Advanced", desc: "Comfortable, going deeper" },
  { value: "job_ready", label: "Job Ready", desc: "Production-grade mastery" },
];

const TIMES: { value: TimeCommitment; label: string; sub: string }[] = [
  { value: "15_min_per_day", label: "15 min", sub: "Light touch" },
  { value: "30_min_per_day", label: "30 min", sub: "Steady pace" },
  { value: "1_hr_per_day", label: "1 hr", sub: "Committed" },
  { value: "2_plus_hr_per_day", label: "2+ hrs", sub: "Full send" },
];

const MOTIVATIONS: { value: MotivationType; emoji: string; label: string }[] = [
  { value: "curiosity", emoji: "🔍", label: "Curiosity" },
  { value: "career", emoji: "💼", label: "Career" },
  { value: "exams", emoji: "📝", label: "Exams" },
  { value: "building_products", emoji: "🏗️", label: "Building" },
];

const STYLES: { value: LearningStyle; emoji: string; label: string }[] = [
  { value: "reading", emoji: "📖", label: "Reading" },
  { value: "examples", emoji: "💡", label: "Examples" },
  { value: "practice", emoji: "⚡", label: "Practice" },
  { value: "mixed", emoji: "🔀", label: "Mixed" },
];

// ─── Shared animation variants ─────────────────────────────────────────────
const stepVariants = {
  enter: { opacity: 0, y: 24, scale: 0.98 },
  center: { opacity: 1, y: 0, scale: 1 },
  exit: { opacity: 0, y: -16, scale: 0.98 },
};

// ─── Building Screen ──────────────────────────────────────────────────────────
function BuildingScreen() {
  const stages = [
    "Analyzing your profile...",
    "Mapping concepts...",
    "Ordering prerequisites...",
    "Calibrating thresholds...",
    "Your path is ready.",
  ];
  const [stageIdx, setStageIdx] = useState(0);

  // Advance stages for visual effect
  useState(() => {
    const id = setInterval(() => {
      setStageIdx((i) => {
        if (i >= stages.length - 1) { clearInterval(id); return i; }
        return i + 1;
      });
    }, 700);
    return () => clearInterval(id);
  });

  return (
    <div className="min-h-screen bg-[#080808] flex flex-col items-center justify-center text-white">
      {/* Glow */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-96 h-96 rounded-full bg-indigo-500/8 blur-[120px]" />
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6 }}
        className="flex flex-col items-center gap-8 relative z-10"
      >
        <div className="relative">
          <div className="w-16 h-16 rounded-full border border-white/10 flex items-center justify-center">
            <Loader2 className="w-7 h-7 animate-spin text-indigo-400" />
          </div>
          <div className="absolute inset-0 rounded-full border border-indigo-500/30 animate-ping" />
        </div>

        <div className="text-center">
          <h2 className="font-serif text-3xl mb-3">Building your path</h2>
          <AnimatePresence mode="wait">
            <motion.p
              key={stageIdx}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.3 }}
              className={`text-sm tracking-wide ${stageIdx === stages.length - 1 ? "text-emerald-400" : "text-zinc-500"}`}
            >
              {stages[stageIdx]}
            </motion.p>
          </AnimatePresence>
        </div>

        {/* Progress bar */}
        <div className="w-48 h-px bg-white/5 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-indigo-500 rounded-full"
            animate={{ width: `${((stageIdx + 1) / stages.length) * 100}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
      </motion.div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function OnboardingPage() {
  const router = useRouter();
  const userId = useAuthStore((s) => s.userId);

  const [step, setStep] = useState(0);
  const [building, setBuilding] = useState(false);
  const [answers, setAnswers] = useState<Answers>({
    goal: null,
    target_level: null,
    time_commitment: null,
    learning_style: null,
    motivation: null,
  });

  const totalSteps = 5; // 0=intro, 1=goal, 2=level, 3=time, 4=motivation+style

  const canAdvance = () => {
    if (step === 0) return true;
    if (step === 1) return !!answers.goal;
    if (step === 2) return !!answers.target_level;
    if (step === 3) return !!answers.time_commitment;
    if (step === 4) return !!answers.motivation && !!answers.learning_style;
    return false;
  };

  const handleNext = () => {
    if (step < totalSteps - 1) setStep((s) => s + 1);
    else handleSubmit();
  };

  const handleSubmit = async () => {
    if (!userId) return;
    setBuilding(true);

    try {
      // 1. Save learner profile
      await api.put(`/onboarding/users/${userId}/profile`, {
        domain_key: "python_programming",
        goal: answers.goal,
        target_level: answers.target_level,
        time_commitment: answers.time_commitment,
        learning_style: answers.learning_style,
        motivation: answers.motivation,
        current_level_summary: "Profiling complete.",
      });

      // 2. Generate curriculum
      await api.post(`/curriculum/users/${userId}/generate`);

      // 3. Show building screen for a moment, then redirect
      await new Promise((r) => setTimeout(r, 3500));
      router.push("/dashboard");
    } catch (err) {
      console.error("Onboarding failed:", err);
      setBuilding(false);
    }
  };

  if (building) return <BuildingScreen />;

  return (
    <div className="min-h-screen bg-[#080808] text-white flex flex-col items-center justify-center relative overflow-hidden">
      {/* Ambient background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-indigo-600/5 blur-[150px]" />
      </div>

      {/* Step dots */}
      {step > 0 && (
        <div className="absolute top-8 left-0 right-0 flex justify-center gap-2">
          {[1, 2, 3, 4].map((i) => (
            <motion.div
              key={i}
              animate={{
                width: step === i ? 24 : 6,
                backgroundColor: step >= i ? "#6366f1" : "rgba(255,255,255,0.1)",
              }}
              transition={{ duration: 0.3 }}
              className="h-1.5 rounded-full"
            />
          ))}
        </div>
      )}

      {/* Step Content */}
      <div className="w-full max-w-xl px-6 relative z-10">
        <AnimatePresence mode="wait">

          {/* ── Step 0: Welcome ── */}
          {step === 0 && (
            <motion.div
              key="step-0"
              variants={stepVariants} initial="enter" animate="center" exit="exit"
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="flex flex-col items-center text-center"
            >
              <div className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-8">
                <span className="font-serif italic text-xl font-bold">C</span>
              </div>
              <h1 className="font-serif text-5xl md:text-6xl leading-tight tracking-tight mb-5">
                Let's calibrate<br />
                <span className="italic">your mind.</span>
              </h1>
              <p className="text-zinc-400 text-lg mb-12 leading-relaxed max-w-sm">
                Answer 4 questions. Cortex builds a deterministic learning path — precise, ordered, and built for you.
              </p>
              <button
                onClick={handleNext}
                className="flex items-center gap-2 bg-white text-black font-semibold text-sm px-7 py-3.5 rounded-full hover:bg-zinc-100 transition-all hover:scale-105 active:scale-95"
              >
                Begin Calibration <ArrowRight className="w-4 h-4" />
              </button>
            </motion.div>
          )}

          {/* ── Step 1: Goal ── */}
          {step === 1 && (
            <motion.div
              key="step-1"
              variants={stepVariants} initial="enter" animate="center" exit="exit"
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            >
              <p className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-3">Step 1 of 4</p>
              <h2 className="font-serif text-4xl md:text-5xl tracking-tight mb-2">
                What brings you here?
              </h2>
              <p className="text-zinc-500 text-base mb-8">Your goal shapes everything Cortex builds for you.</p>
              <div className="grid grid-cols-2 gap-3">
                {GOALS.map((g) => (
                  <motion.button
                    key={g.value}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setAnswers((a) => ({ ...a, goal: g.value }))}
                    className={`relative text-left p-4 rounded-2xl border transition-all duration-200 ${
                      answers.goal === g.value
                        ? "border-indigo-500 bg-indigo-500/10 shadow-[0_0_20px_rgba(99,102,241,0.15)]"
                        : "border-white/8 bg-white/3 hover:bg-white/6 hover:border-white/15"
                    }`}
                  >
                    {answers.goal === g.value && (
                      <motion.div
                        initial={{ scale: 0 }} animate={{ scale: 1 }}
                        className="absolute top-3 right-3 w-5 h-5 rounded-full bg-indigo-500 flex items-center justify-center"
                      >
                        <Check className="w-3 h-3 text-white" />
                      </motion.div>
                    )}
                    <span className="text-2xl mb-2 block">{g.emoji}</span>
                    <p className="font-semibold text-sm text-white">{g.label}</p>
                    <p className="text-xs text-zinc-500 mt-0.5">{g.desc}</p>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}

          {/* ── Step 2: Target Level ── */}
          {step === 2 && (
            <motion.div
              key="step-2"
              variants={stepVariants} initial="enter" animate="center" exit="exit"
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            >
              <p className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-3">Step 2 of 4</p>
              <h2 className="font-serif text-4xl md:text-5xl tracking-tight mb-2">
                Where are you right now?
              </h2>
              <p className="text-zinc-500 text-base mb-10">This sets your mastery thresholds — be honest.</p>

              {/* Visual path selector */}
              <div className="relative">
                {/* Track line */}
                <div className="absolute top-6 left-6 right-6 h-px bg-white/10" />
                <div className="flex justify-between relative">
                  {LEVELS.map((l, i) => {
                    const isSelected = answers.target_level === l.value;
                    const selectedIdx = LEVELS.findIndex((lv) => lv.value === answers.target_level);
                    const isPast = selectedIdx >= 0 && i <= selectedIdx;
                    return (
                      <button
                        key={l.value}
                        onClick={() => setAnswers((a) => ({ ...a, target_level: l.value }))}
                        className="flex flex-col items-center gap-3 w-24 group"
                      >
                        <motion.div
                          animate={{
                            backgroundColor: isSelected ? "#6366f1" : isPast ? "rgba(99,102,241,0.2)" : "rgba(255,255,255,0.05)",
                            borderColor: isSelected ? "#6366f1" : isPast ? "rgba(99,102,241,0.4)" : "rgba(255,255,255,0.1)",
                            scale: isSelected ? 1.15 : 1,
                          }}
                          transition={{ duration: 0.25 }}
                          className="w-12 h-12 rounded-full border-2 flex items-center justify-center"
                        >
                          {isSelected && (
                            <motion.div
                              initial={{ scale: 0 }} animate={{ scale: 1 }}
                            >
                              <Check className="w-5 h-5 text-white" />
                            </motion.div>
                          )}
                        </motion.div>
                        <div className="text-center">
                          <p className={`text-sm font-semibold transition-colors ${isSelected ? "text-white" : "text-zinc-500"}`}>{l.label}</p>
                          <p className="text-xs text-zinc-600 mt-0.5 leading-tight">{l.desc}</p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </motion.div>
          )}

          {/* ── Step 3: Time Commitment ── */}
          {step === 3 && (
            <motion.div
              key="step-3"
              variants={stepVariants} initial="enter" animate="center" exit="exit"
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            >
              <p className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-3">Step 3 of 4</p>
              <h2 className="font-serif text-4xl md:text-5xl tracking-tight mb-2">
                How much time daily?
              </h2>
              <p className="text-zinc-500 text-base mb-10">Cortex paces your path to fit your schedule.</p>

              <div className="grid grid-cols-2 gap-3">
                {TIMES.map((t) => (
                  <motion.button
                    key={t.value}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setAnswers((a) => ({ ...a, time_commitment: t.value }))}
                    className={`text-left p-5 rounded-2xl border transition-all duration-200 ${
                      answers.time_commitment === t.value
                        ? "border-indigo-500 bg-indigo-500/10 shadow-[0_0_20px_rgba(99,102,241,0.15)]"
                        : "border-white/8 bg-white/3 hover:bg-white/6 hover:border-white/15"
                    }`}
                  >
                    <p className={`font-serif text-3xl font-bold mb-1 ${answers.time_commitment === t.value ? "text-indigo-300" : "text-white"}`}>
                      {t.label}
                    </p>
                    <p className="text-xs text-zinc-500">{t.sub}</p>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}

          {/* ── Step 4: Motivation + Learning Style ── */}
          {step === 4 && (
            <motion.div
              key="step-4"
              variants={stepVariants} initial="enter" animate="center" exit="exit"
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            >
              <p className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-3">Step 4 of 4</p>
              <h2 className="font-serif text-4xl md:text-5xl tracking-tight mb-2">
                One last thing.
              </h2>
              <p className="text-zinc-500 text-base mb-8">What drives you, and how do you learn best?</p>

              {/* Motivation */}
              <p className="text-xs font-semibold tracking-widest text-zinc-600 uppercase mb-3">What drives you?</p>
              <div className="grid grid-cols-4 gap-2 mb-8">
                {MOTIVATIONS.map((m) => (
                  <motion.button
                    key={m.value}
                    whileHover={{ scale: 1.04 }}
                    whileTap={{ scale: 0.96 }}
                    onClick={() => setAnswers((a) => ({ ...a, motivation: m.value }))}
                    className={`flex flex-col items-center gap-2 py-4 rounded-2xl border transition-all duration-200 ${
                      answers.motivation === m.value
                        ? "border-indigo-500 bg-indigo-500/10"
                        : "border-white/8 bg-white/3 hover:bg-white/6 hover:border-white/15"
                    }`}
                  >
                    <span className="text-2xl">{m.emoji}</span>
                    <span className="text-xs font-medium text-zinc-400">{m.label}</span>
                  </motion.button>
                ))}
              </div>

              {/* Learning Style */}
              <p className="text-xs font-semibold tracking-widest text-zinc-600 uppercase mb-3">How do you learn best?</p>
              <div className="grid grid-cols-4 gap-2">
                {STYLES.map((s) => (
                  <motion.button
                    key={s.value}
                    whileHover={{ scale: 1.04 }}
                    whileTap={{ scale: 0.96 }}
                    onClick={() => setAnswers((a) => ({ ...a, learning_style: s.value }))}
                    className={`flex flex-col items-center gap-2 py-4 rounded-2xl border transition-all duration-200 ${
                      answers.learning_style === s.value
                        ? "border-emerald-500 bg-emerald-500/10"
                        : "border-white/8 bg-white/3 hover:bg-white/6 hover:border-white/15"
                    }`}
                  >
                    <span className="text-2xl">{s.emoji}</span>
                    <span className="text-xs font-medium text-zinc-400">{s.label}</span>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </div>

      {/* Next / Submit button */}
      {step > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="absolute bottom-10 left-0 right-0 flex justify-center"
        >
          <motion.button
            onClick={handleNext}
            disabled={!canAdvance()}
            whileHover={canAdvance() ? { scale: 1.04 } : {}}
            whileTap={canAdvance() ? { scale: 0.96 } : {}}
            className={`flex items-center gap-2 font-semibold text-sm px-7 py-3.5 rounded-full transition-all duration-200 ${
              canAdvance()
                ? "bg-white text-black hover:bg-zinc-100"
                : "bg-white/8 text-zinc-600 cursor-not-allowed"
            }`}
          >
            {step === totalSteps - 1 ? (
              <>Build my path <ArrowRight className="w-4 h-4" /></>
            ) : (
              <>Continue <ArrowRight className="w-4 h-4" /></>
            )}
          </motion.button>
        </motion.div>
      )}

      {/* Back button */}
      {step > 1 && (
        <button
          onClick={() => setStep((s) => s - 1)}
          className="absolute bottom-10 left-8 text-xs text-zinc-600 hover:text-zinc-400 transition-colors"
        >
          ← Back
        </button>
      )}
    </div>
  );
}
