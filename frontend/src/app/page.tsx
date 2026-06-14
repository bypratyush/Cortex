"use client";

import { motion } from "framer-motion";
import { ArrowRight, Asterisk } from "lucide-react";
import { SignUpButton, SignInButton, Show, UserButton } from "@clerk/nextjs";

export default function Home() {

  return (
    <main className="relative min-h-screen w-full overflow-hidden bg-[#0A0A0A] flex flex-col items-center justify-center font-sans text-white">
      {/* Background Video */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="absolute inset-0 w-full h-full object-cover z-0"
      >
        <source
          src="https://res.cloudinary.com/dfonotyfb/video/upload/v1775585556/dds3_1_rqhg7x.mp4"
          type="video/mp4"
        />
      </video>

      {/* Very subtle gradient overlay to ensure text readability without hiding the video */}
      <div className="absolute inset-0 bg-black/20 z-10" />

      {/* Top Navigation */}
      <div className="absolute top-6 left-0 right-0 z-50 flex justify-center px-6">
        <div className="w-full max-w-5xl flex justify-between items-start">
          {/* Main Nav Pill */}
          <nav className="flex items-center gap-8 bg-black/40 backdrop-blur-md border border-white/10 rounded-full px-2 py-2">
            <div className="bg-white text-black w-8 h-8 rounded-full flex items-center justify-center">
              <Asterisk className="w-5 h-5" />
            </div>
            <div className="flex items-center gap-8 px-4 text-xs font-semibold tracking-widest text-white/80">
              <a href="#" className="hover:text-white transition-colors">CURRICULUM</a>
              <a href="#" className="hover:text-white transition-colors">SOCRATIC AI</a>
              <a href="#" className="hover:text-white transition-colors">METHODOLOGY</a>
              <a href="#" className="hover:text-white transition-colors">PRICING</a>
              <SignInButton mode="modal">
                <button className="hover:text-white transition-colors uppercase cursor-pointer">LOGIN</button>
              </SignInButton>
            </div>
          </nav>

          {/* Right Action Button (User Profile or nothing if signed out) */}
          <Show when="signed-in">
            <div className="bg-black/40 backdrop-blur-md border border-white/10 w-12 h-12 rounded-full flex items-center justify-center hover:bg-black/60 transition-colors">
              <UserButton appearance={{ elements: { userButtonAvatarBox: "w-8 h-8" } }} />
            </div>
          </Show>
          <Show when="signed-out">
            <div className="w-12 h-12" /> {/* Spacer to keep layout balanced */}
          </Show>
        </div>
      </div>

      {/* Center Hero Content */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1.2, ease: "easeOut" }}
        className="relative z-20 flex flex-col items-center text-center mt-12"
      >
        {/* Top Badge */}
        <div className="mb-6 bg-white/5 backdrop-blur-sm border border-white/20 rounded-full px-4 py-1.5 text-[10px] font-bold uppercase tracking-[0.2em] text-white/70">
          SOCRATIC LEARNING ENGINE
        </div>

        {/* Serif Heading */}
        <h1 className="font-serif text-6xl md:text-[7rem] leading-[1.05] tracking-tight mb-10 drop-shadow-2xl">
          Deterministic<br />
          <span className="italic">learning</span>
        </h1>

        {/* Launch Button */}
        <Show when="signed-out">
          <SignUpButton mode="modal">
            <button
              className="group flex items-center gap-2 bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/20 rounded-full px-6 py-2.5 text-xs font-bold uppercase tracking-widest text-white transition-all hover:scale-105 active:scale-95"
            >
              INITIALIZE CORTEX <ArrowRight className="w-4 h-4 ml-1" />
            </button>
          </SignUpButton>
        </Show>
        <Show when="signed-in">
          <a
            href="/dashboard"
            className="group flex items-center gap-2 bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/20 rounded-full px-6 py-2.5 text-xs font-bold uppercase tracking-widest text-white transition-all hover:scale-105 active:scale-95"
          >
            ENTER DASHBOARD <ArrowRight className="w-4 h-4 ml-1" />
          </a>
        </Show>
      </motion.div>
    </main>
  );
}
