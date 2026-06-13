"use client";

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Send, Loader2, User, Sparkles } from "lucide-react";
import { useTutorStore } from "@/store/useTutorStore";
import api from "@/lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  id: string;
  role: "learner" | "tutor";
  content: string;
}

export default function TutorDrawer() {
  const { isOpen, context, closeTutor, conversationId, setConversationId } = useTutorStore();
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Initialize Conversation
  useEffect(() => {
    if (!isOpen || !context?.conceptId) return;

    async function initConversation() {
      try {
        setLoading(true);
        // If we already have a conversationId for this context, just fetch messages
        // For simplicity, we'll start a new conversation every time the drawer opens for now
        // A better approach would be to cache conversationId based on conceptId
        const res = await api.post("/tutor/conversations", {
          concept_id: context!.conceptId,
          current_lesson_id: context!.lessonId || null,
          current_quiz_id: context!.quizId || null,
        });

        const newId = res.data.id;
        setConversationId(newId);
        
        // Fetch initial messages (the AI's greeting)
        const msgRes = await api.get(`/tutor/conversations/${newId}/messages`);
        setMessages(msgRes.data);
      } catch (err) {
        console.error("Failed to init tutor conversation:", err);
      } finally {
        setLoading(false);
      }
    }

    if (!conversationId) {
      initConversation();
    }
  }, [isOpen, context, conversationId, setConversationId]);

  const handleSend = async () => {
    if (!input.trim() || !conversationId) return;
    
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "learner",
      content: input,
    };
    
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.post(`/tutor/conversations/${conversationId}/messages`, {
        content: userMessage.content
      });
      // res.data contains [user_message, assistant_message]
      setMessages((prev) => {
        const withoutOptimistic = prev.filter(m => m.id !== userMessage.id);
        return [...withoutOptimistic, ...res.data];
      });
    } catch (err) {
      console.error("Failed to send message:", err);
      // Rollback on error could go here
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeTutor}
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
          />
          
          {/* Drawer */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-[#0A0A0A]/95 backdrop-blur-xl border-l border-white/10 flex flex-col shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-5 border-b border-white/5">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-serif text-lg text-white">Socratic Tutor</h3>
                  {context?.contextPill && (
                    <p className="text-xs text-zinc-500 font-mono tracking-wider uppercase">
                      {context.contextPill}
                    </p>
                  )}
                </div>
              </div>
              <button 
                onClick={closeTutor}
                className="p-2 text-zinc-400 hover:text-white hover:bg-white/10 rounded-full transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {messages.map((msg) => (
                <div 
                  key={msg.id} 
                  className={`flex gap-4 ${msg.role === "learner" ? "flex-row-reverse" : "flex-row"}`}
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                    msg.role === "learner" ? "bg-white/10 text-white" : "bg-indigo-500/20 text-indigo-400"
                  }`}>
                    {msg.role === "learner" ? <User className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
                  </div>
                  <div className={`px-5 py-3 rounded-2xl max-w-[80%] ${
                    msg.role === "learner" 
                      ? "bg-white/10 text-white rounded-tr-none" 
                      : "bg-indigo-500/10 border border-indigo-500/20 text-indigo-50 rounded-tl-none leading-relaxed prose prose-invert prose-p:leading-relaxed prose-pre:bg-black/50 prose-pre:border prose-pre:border-white/10 max-w-full"
                  }`}>
                    {msg.role === "learner" ? (
                      msg.content
                    ) : (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content.replace(/\\n/g, "\n")}
                      </ReactMarkdown>
                    )}
                  </div>
                </div>
              ))}
              
              {loading && messages.length > 0 && (
                <div className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center shrink-0 text-indigo-400">
                    <Loader2 className="w-4 h-4 animate-spin" />
                  </div>
                  <div className="px-5 py-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-tl-none">
                    <span className="animate-pulse">Thinking...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-6 border-t border-white/5 bg-black/50">
              <div className="relative flex items-center">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSend()}
                  placeholder="Ask a question..."
                  className="w-full bg-white/5 border border-white/10 rounded-full pl-6 pr-12 py-4 text-white focus:outline-none focus:border-indigo-500/50 transition-colors"
                />
                <button 
                  onClick={handleSend}
                  disabled={!input.trim() || loading}
                  className="absolute right-2 p-2 bg-indigo-500 hover:bg-indigo-600 disabled:bg-zinc-700 disabled:opacity-50 text-white rounded-full transition-colors"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
