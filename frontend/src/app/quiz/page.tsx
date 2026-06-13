"use client";

import { useEffect, useState, useRef, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Toaster, toast } from "sonner";
import api from "@/lib/api";
import QuizCard from "@/components/quiz/QuizCard";
import ResultsScreen from "@/components/quiz/ResultsScreen";
import { useTutorStore } from "@/store/useTutorStore";

function QuizContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const conceptId = searchParams.get("conceptId");
  const pathItemId = searchParams.get("pathItemId");
  const quizType = searchParams.get("quizType") || "mastery_check";

  const [quiz, setQuiz] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<{ question_id: string; answer: string }[]>([]);
  
  const [submitting, setSubmitting] = useState(false);
  const [results, setResults] = useState<any>(null);

  const fetchedRef = useRef(false);

  useEffect(() => {
    if (!conceptId || fetchedRef.current) return;
    fetchedRef.current = true;

    async function loadQuiz() {
      try {
        const payload: any = { 
          concept_id: conceptId,
          quiz_type: quizType,
          question_count: 3 
        };
        if (pathItemId) {
          payload.learning_path_item_id = pathItemId;
        }

        const res = await api.post("/quizzes/generate", payload);
        setQuiz(res.data);
      } catch (err) {
        console.error("Failed to load quiz:", err);
        toast.error("Failed to generate quiz.");
      } finally {
        setLoading(false);
      }
    }

    loadQuiz();
  }, [conceptId, pathItemId, quizType]);

  const handleNext = async (answer: string) => {
    if (!quiz) return;
    
    const currentQuestion = quiz.questions[currentIndex];
    const newAnswers = [...answers, { question_id: currentQuestion.id, answer }];
    setAnswers(newAnswers);

    if (currentIndex < quiz.questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      // Submit Quiz
      setSubmitting(true);
      try {
        const res = await api.post(`/quizzes/${quiz.id}/submit`, { answers: newAnswers });
        setResults(res.data);
        toast.success("Quiz submitted successfully!");
      } catch (err) {
        console.error("Failed to submit quiz:", err);
        toast.error("Failed to submit answers.");
      } finally {
        setSubmitting(false);
      }
    }
  };

  const handleAskTutor = () => {
    useTutorStore.getState().openTutor({
      conceptId: conceptId,
      quizId: quiz?.id,
      contextPill: quiz?.title || "Quiz Review"
    });
  };

  if (!conceptId) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex flex-col items-center justify-center text-white">
        <p className="text-zinc-400 text-sm">Missing concept ID.</p>
      </div>
    );
  }

  if (loading || submitting) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex flex-col items-center justify-center text-white">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-4" />
        <p className="text-zinc-400 text-sm animate-pulse tracking-widest uppercase">
          {submitting ? "Evaluating responses..." : "Generating quiz..."}
        </p>
      </div>
    );
  }

  if (!quiz) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex flex-col items-center justify-center text-white">
        <p className="text-red-400 text-sm">Could not load quiz. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-white font-sans flex flex-col">
      <Toaster position="top-center" theme="dark" />

      {/* Top Nav */}
      <header className="sticky top-0 z-30 bg-[#0A0A0A]/80 backdrop-blur-md border-b border-white/5 px-8 py-5 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div 
            onClick={() => router.push("/dashboard")}
            className="cursor-pointer bg-white/10 hover:bg-white/20 text-white w-8 h-8 rounded-full flex items-center justify-center transition-colors"
          >
            <span className="font-serif italic font-bold text-sm">C</span>
          </div>
          <span className="font-serif text-lg tracking-tight text-zinc-400">
            {results ? "Quiz Results" : "Mastery Check"}
          </span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow px-8 py-16 flex items-center justify-center relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-500/5 blur-[120px] rounded-full pointer-events-none" />

        <div className="relative z-10 w-full max-w-4xl">
          <AnimatePresence mode="wait">
            {!results ? (
              <QuizCard
                key={currentIndex} // Force re-render for animation and state reset
                question={quiz.questions[currentIndex]}
                currentIndex={currentIndex}
                total={quiz.questions.length}
                onNext={handleNext}
              />
            ) : (
              <ResultsScreen
                score={results.score}
                total={quiz.questions.length}
                accuracy={results.accuracy}
                feedback={results.feedback_payload.results}
                onAskTutor={handleAskTutor}
              />
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

export default function QuizPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#0A0A0A] flex flex-col items-center justify-center text-white">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
      </div>
    }>
      <QuizContent />
    </Suspense>
  );
}
