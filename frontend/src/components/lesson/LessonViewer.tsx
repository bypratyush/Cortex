"use client";

import { motion } from "framer-motion";
import CodeBlock from "./CodeBlock";
import { Info, Lightbulb, AlertTriangle } from "lucide-react";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface LessonSection {
  type: string;
  content?: string;
  items?: Array<{
    type: string;
    content: string;
    language?: string;
  }>;
}

interface LessonViewerProps {
  title: string;
  sections: LessonSection[];
}

export default function LessonViewer({ title, sections }: LessonViewerProps) {
  const leftSections = sections.filter(s => s.type === "explanation" || s.type === "callout");
  const rightSections = sections.filter(s => s.type === "analogy" || s.type === "examples");

  return (
    <div className="max-w-[100rem] mx-auto py-12 px-6 lg:px-12">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 xl:gap-20 items-start">
        
        {/* Left Column: Core Lesson Theory (Sticky) */}
        <div className="lg:col-span-5 xl:col-span-5 lg:sticky lg:top-24 space-y-10">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="font-serif text-5xl md:text-6xl tracking-tight text-white leading-tight"
          >
            {title}
          </motion.h1>

          <div className="space-y-10 pb-12">
            {leftSections.map((section, idx) => (
              <motion.div
                key={`left-${idx}`}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.6, delay: idx * 0.1 }}
              >
                {/* Explanation / Text */}
                {section.type === "explanation" && (
                  <div className="prose prose-invert prose-indigo prose-lg max-w-none 
                    prose-p:leading-[1.9] prose-p:text-zinc-300 prose-p:mb-8 
                    prose-headings:font-serif prose-headings:font-normal prose-headings:text-white prose-headings:mt-12 prose-headings:mb-6
                    prose-h2:text-3xl prose-h3:text-2xl 
                    prose-strong:text-white prose-strong:font-semibold
                    prose-ul:text-zinc-300 prose-ul:space-y-3 prose-li:leading-relaxed
                    prose-code:text-indigo-300 prose-code:bg-indigo-500/10 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:font-mono prose-code:text-sm prose-code:font-medium prose-code:before:content-none prose-code:after:content-none"
                  >
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {section.content || ""}
                    </ReactMarkdown>
                  </div>
                )}

                {/* Callout (Info/Warning) */}
                {section.type === "callout" && (
                  <div className="my-8 rounded-3xl bg-white/5 border border-white/10 p-6 flex gap-4 items-start">
                    <Info className="w-6 h-6 text-zinc-400 flex-shrink-0 mt-1" />
                    <p className="text-zinc-300">
                      {section.content}
                    </p>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>

        {/* Right Column: Mental Model & Examples Bento Grid */}
        <div className="lg:col-span-7 xl:col-span-7 space-y-12">
          {rightSections.map((section, idx) => (
            <motion.div
              key={`right-${idx}`}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.3 + (idx * 0.1) }}
            >
              {/* Analogy Callout */}
              {section.type === "analogy" && (
                <div className="mb-12 rounded-3xl bg-gradient-to-br from-indigo-500/10 to-purple-500/5 border border-indigo-500/20 p-8 flex gap-6 items-start shadow-2xl backdrop-blur-sm relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl -mr-24 -mt-24 pointer-events-none" />
                  
                  <div className="flex-shrink-0 w-12 h-12 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400 mt-1 shadow-inner border border-indigo-500/30 relative z-10">
                    <Lightbulb className="w-6 h-6" />
                  </div>
                  <div className="flex-1 relative z-10">
                    <h4 className="text-indigo-300 font-semibold uppercase tracking-[0.2em] text-xs mb-3">
                      Mental Model
                    </h4>
                    <div className="prose prose-invert prose-indigo prose-lg text-zinc-200 leading-relaxed prose-p:leading-[1.8] prose-strong:text-white prose-p:last:mb-0">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {section.content || ""}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              )}

              {/* Examples */}
              {section.type === "examples" && section.items && (
                <div>
                  <div className="flex items-center gap-4 mb-8">
                    <div className="w-12 h-px bg-indigo-500/50" />
                    <h4 className="text-white font-serif text-3xl">Examples in Practice</h4>
                    <div className="flex-1 h-px bg-gradient-to-r from-indigo-500/20 to-transparent" />
                  </div>
                  <div className="grid grid-cols-1 gap-8 items-start">
                    {section.items.map((item, itemIdx) => (
                      <div 
                        key={itemIdx} 
                        className="flex flex-col bg-[#050505] border border-white/10 rounded-3xl p-8 shadow-2xl hover:border-indigo-500/30 transition-all duration-300 group h-full w-full"
                      >
                        {item.type === "text" && (
                          <div className="prose prose-invert prose-indigo prose-md mb-6 text-zinc-400 group-hover:text-zinc-300 transition-colors max-w-none">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {item.content}
                            </ReactMarkdown>
                          </div>
                        )}
                        {item.type === "code" && (
                          <div className="mt-auto w-full overflow-hidden">
                            <CodeBlock 
                                code={item.content} 
                                language={item.language || "python"} 
                                output={(item as any).output} 
                            />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </div>
        
      </div>
    </div>
  );
}
