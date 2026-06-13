"use client";

import { useEffect, useState, useRef, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Loader2, ArrowRight, MessageCircle } from "lucide-react";
import { motion } from "framer-motion";
import { Toaster, toast } from "sonner";
import api from "@/lib/api";
import LessonViewer from "@/components/lesson/LessonViewer";
import { useTutorStore } from "@/store/useTutorStore";

function LessonContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const conceptId = searchParams.get("conceptId");
  const pathItemId = searchParams.get("pathItemId");

  const [lesson, setLesson] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);
  const fetchedRef = useRef(false);

  useEffect(() => {
    if (!conceptId || fetchedRef.current) return;
    fetchedRef.current = true;

    async function loadLesson() {
      try {
        const payload: any = { concept_id: conceptId };
        if (pathItemId) {
          payload.learning_path_item_id = pathItemId;
        }

        const res = await api.post("/lessons/generate", payload);
        setLesson(res.data);
      } catch (err) {
        console.error("Failed to load lesson:", err);
        toast.error("Failed to generate lesson content.");
      } finally {
        setLoading(false);
      }
    }

    loadLesson();
  }, [conceptId, pathItemId]);

  const handleComplete = async () => {
    if (!lesson) return;
    setCompleting(true);
    try {
      await api.post(`/lessons/${lesson.id}/complete`, { completed: true });
      toast.success("Lesson completed!");
      
      // Navigate to quiz
      const url = new URL("/quiz", window.location.origin);
      url.searchParams.set("conceptId", conceptId!);
      if (pathItemId) {
        url.searchParams.set("pathItemId", pathItemId);
      }
      url.searchParams.set("quizType", "mastery_check");
      
      router.push(url.toString());
    } catch (err) {
      console.error("Failed to complete lesson:", err);
      toast.error("Failed to mark lesson as complete.");
      setCompleting(false);
    }
  };

  if (!conceptId) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex flex-col items-center justify-center text-white">
        <p className="text-zinc-400 text-sm">Missing concept ID.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex flex-col items-center justify-center text-white">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-4" />
        <p className="text-zinc-400 text-sm animate-pulse tracking-widest uppercase">
          Synthesizing Knowledge...
        </p>
      </div>
    );
  }

  if (!lesson) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex flex-col items-center justify-center text-white">
        <p className="text-red-400 text-sm">Could not load lesson. Please try again.</p>
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
          <span className="font-serif text-lg tracking-tight text-zinc-400">Lesson Mode</span>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-grow px-8 pb-32">
        <LessonViewer 
          title={lesson.title} 
          sections={lesson.content_payload.sections} 
        />
      </main>

      {/* Bottom Action Bar */}
      <motion.div 
        initial={{ y: 100 }}
        animate={{ y: 0 }}
        transition={{ delay: 1, duration: 0.8, ease: "easeOut" }}
        className="fixed bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-[#0A0A0A] via-[#0A0A0A]/90 to-transparent pointer-events-none flex justify-center items-center gap-4"
      >
        <button 
          onClick={() => useTutorStore.getState().openTutor({
            conceptId: conceptId,
            lessonId: lesson?.id,
            contextPill: lesson?.title
          })}
          className="pointer-events-auto flex items-center gap-2 px-6 py-4 rounded-full bg-[#1A1A1A] border border-white/10 text-zinc-300 hover:text-white hover:bg-white/20 transition-all shadow-xl font-semibold text-sm hover:scale-105 active:scale-95"
        >
          <MessageCircle className="w-5 h-5" />
          Ask Tutor
        </button>

        <button
          onClick={handleComplete}
          disabled={completing}
          className="pointer-events-auto flex items-center gap-2 bg-white text-black text-sm font-semibold px-8 py-4 rounded-full hover:bg-zinc-200 hover:scale-105 active:scale-95 transition-all shadow-[0_0_40px_rgba(255,255,255,0.1)] disabled:opacity-50 disabled:hover:scale-100"
        >
          {completing ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <>
              I understand this concept
              <ArrowRight className="w-5 h-5" />
            </>
          )}
        </button>
      </motion.div>
    </div>
  );
}

export default function LessonPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#0A0A0A] flex flex-col items-center justify-center text-white">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
      </div>
    }>
      <LessonContent />
    </Suspense>
  );
}
