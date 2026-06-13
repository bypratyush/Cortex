"use client";

import { useEffect, useState, useRef } from "react";
import { useUser, UserButton } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2 } from "lucide-react";
import { Toaster, toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";
import ContextNudgeModal from "@/components/onboarding/ContextNudgeModal";
import ProgressRing from "@/components/dashboard/ProgressRing";
import NextActionCard from "@/components/dashboard/NextActionCard";
import MasteryGrid from "@/components/dashboard/MasteryGrid";
import WeakAreasPanel from "@/components/dashboard/WeakAreasPanel";

interface DashboardData {
  user_id: string;
  domain_key: string;
  total_concepts_mastered: number;
  total_concepts_in_domain: number;
  overall_progress_percentage: number;
  mastery_map: any[];
  weak_areas: any[];
  next_action?: any;
}

export default function DashboardPage() {
  const { user, isLoaded } = useUser();
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const userId = useAuthStore((s) => s.userId);

  const [syncState, setSyncState] = useState<"syncing" | "done" | "error">("syncing");
  const [showNudge, setShowNudge] = useState(false);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const hasSynced = useRef(false);

  useEffect(() => {
    if (!isLoaded || !user) return;
    if (hasSynced.current) return;
    hasSynced.current = true;

    async function syncAndLoad() {
      try {
        const email = user!.primaryEmailAddress?.emailAddress ?? "";
        const name = user!.fullName ?? "User";

        // 1. Sync user to backend DB
        const syncRes = await api.post("/users/sync", {
          email,
          full_name: name,
          auth_provider: "clerk",
          auth_subject: user!.id,
        });

        const { user: dbUser, is_onboarded } = syncRes.data;
        setAuth(dbUser.id, email, name);

        // 2. If not onboarded → go to profiling
        if (!is_onboarded) {
          router.push("/onboarding");
          return;
        }

        // 3. Show signed in toast
        toast.success("Signed in successfully", {
          description: `Welcome back, ${user!.firstName}.`,
          duration: 3000,
        });

        // 4. Load Dashboard Overview Data
        try {
          const overviewRes = await api.get(`/dashboard/overview`);
          setDashboardData(overviewRes.data);
        } catch (err: any) {
          console.error("Failed to load dashboard overview:", err);
          // Don't fail the whole sync if overview fails, just keep it null or retry later
        }

        setSyncState("done");

        // 5. Show context nudge modal (always show on fresh dashboard load)
        setShowNudge(true);
      } catch (err: any) {
        console.error("Sync failed:", err);
        setSyncState("error");
      }
    }

    syncAndLoad();
  }, [user, isLoaded, setAuth, router]);

  if (!isLoaded || syncState === "syncing") {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex flex-col items-center justify-center text-white">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-4" />
        <p className="text-zinc-400 text-sm animate-pulse tracking-widest uppercase">
          Synchronizing Cortex Engine...
        </p>
      </div>
    );
  }

  if (syncState === "error") {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex flex-col items-center justify-center text-white">
        <p className="text-red-400 text-sm">
          Failed to connect to Cortex. Please refresh.
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-white font-sans">
      <Toaster position="top-center" theme="dark" />

      {/* Top Nav */}
      <header className="flex justify-between items-center px-8 py-5 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="bg-white text-black w-7 h-7 rounded-full flex items-center justify-center font-serif italic font-bold text-sm">
            C
          </div>
          <span className="font-serif text-lg tracking-tight">Cortex</span>
        </div>
        <div className="flex items-center gap-6">
          <span className="text-xs font-semibold tracking-widest text-zinc-500 uppercase cursor-pointer hover:text-white transition-colors">Curriculum</span>
          <UserButton afterSignOutUrl="/" />
        </div>
      </header>

      {/* Dashboard Content */}
      <main className="max-w-5xl mx-auto px-8 py-16">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-16">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <h1 className="font-serif text-5xl md:text-6xl tracking-tight mb-4">
              Welcome back,{" "}
              <span className="italic">{user?.firstName ?? "Learner"}</span>.
            </h1>
            <p className="text-zinc-500 text-lg">
              {dashboardData?.total_concepts_in_domain
                ? `Your curriculum is calibrated and ready.`
                : `Preparing your learning path...`}
            </p>
          </motion.div>

          {/* Progress Ring Hero */}
          {dashboardData && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
              className="flex items-center gap-6"
            >
              <div className="text-right hidden sm:block">
                <p className="text-white font-medium text-lg">Overall Progress</p>
                <p className="text-zinc-500 text-sm">
                  {dashboardData.total_concepts_mastered} of {dashboardData.total_concepts_in_domain} concepts mastered
                </p>
              </div>
              <ProgressRing percentage={dashboardData.overall_progress_percentage} size={110} strokeWidth={8} />
            </motion.div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            {/* Next Action */}
            <motion.div
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
            >
              {dashboardData?.next_action ? (
                <NextActionCard action={dashboardData.next_action} />
              ) : (
                <div className="rounded-3xl border border-white/5 bg-white/[0.02] p-8 text-center">
                  <p className="text-zinc-400">Loading your next action...</p>
                </div>
              )}
            </motion.div>

            {/* Mastery Grid */}
            <motion.div
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4, ease: "easeOut" }}
            >
              {dashboardData?.mastery_map && (
                <MasteryGrid masteryMap={dashboardData.mastery_map} />
              )}
            </motion.div>
          </div>

          <div className="space-y-8">
            {/* Weak Areas */}
            <motion.div
              initial={{ opacity: 0, x: 24 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.5, ease: "easeOut" }}
            >
              {dashboardData?.weak_areas && (
                <WeakAreasPanel weakAreas={dashboardData.weak_areas} />
              )}
            </motion.div>
          </div>
        </div>
      </main>

      {/* Context Nudge Modal */}
      <AnimatePresence>
        {showNudge && (
          <ContextNudgeModal
            onDismiss={() => setShowNudge(false)}
            conceptCount={dashboardData?.total_concepts_in_domain ?? 0}
          />
        )}
      </AnimatePresence>

      {/* Backdrop blur when nudge is open */}
      <AnimatePresence>
        {showNudge && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm pointer-events-none"
          />
        )}
      </AnimatePresence>
    </div>
  );
}
