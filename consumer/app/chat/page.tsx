"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AppNav } from "@/components/brand/app-nav";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { sampleChat, suggestedQuestions, sarah, type ChatTurn } from "@/lib/mock-data";
import { Send, Sparkles, Loader2 } from "lucide-react";
import Image from "next/image";

// Mock RAG response generator. Wire to real /api/chat later.
function mockResponse(question: string): ChatTurn {
  const q = question.toLowerCase();
  if (q.includes("ready") || q.includes("when") || q.includes("harvest")) {
    return {
      id: crypto.randomUUID(),
      role: "kale",
      text: "Your curly kale is on track for harvest on May 28 — that's 11 days from today. The MILP harvest scheduler picked this date to maximize biomass while staying inside your weekly delivery window.",
      citations: [
        { source: "Plot 042 sensors", snippet: "Day 31 of 42, biomass 184g, leaf area 0.42m²" },
        { source: "Harvest schedule", snippet: "Optimal harvest window: May 27–30 (48ms MILP solve)" },
      ],
    };
  }
  if (q.includes("humidity") || q.includes("light") || q.includes("temperature")) {
    return {
      id: crypto.randomUUID(),
      role: "kale",
      text: "The PPO RL controller raised humidity by 2% and extended light by 5 minutes this morning. Reason: yesterday's leaf transpiration was 8% above the target curve, suggesting the kale is in its final-phase growth surge — extra moisture and light maximize the last 26% of biomass.",
      citations: [
        { source: "Climate log", snippet: "06:00 SGT — humidity 68→70%, photoperiod 14:00→14:05" },
        { source: "PPO RL agent", snippet: "Reward signal: +0.04 (transpiration above target)" },
      ],
    };
  }
  if (q.includes("flower") || q.includes("add") || q.includes("crop")) {
    return {
      id: crypto.randomUUID(),
      role: "kale",
      text: "You're on the Joint tier (S$80/mo, 2 crops). Edible flowers would need an upgrade to Real (S$200/mo, 4–5 crops). I can preview what your plot would look like with edible nasturtiums + viola alongside your existing kale and basil.",
      citations: [
        { source: "Subscription", snippet: "Joint tier: 2 crop slots active" },
        { source: "Crop catalog", snippet: "Real-tier additions: nasturtium, viola, mint, oregano" },
      ],
    };
  }
  if (q.includes("light") || q.includes("basil")) {
    return {
      id: crypto.randomUUID(),
      role: "kale",
      text: "Your Thai basil is getting 14 hours of LED at 240 µmol/m²/s — exactly its optimal range. Day 18 of 28 is right where we want it. The aroma compounds peak around day 24, so you'll start to smell it through the camera by next weekend.",
      citations: [
        { source: "Plot 042 sensors", snippet: "Basil PPFD: 240 µmol/m²/s, photoperiod: 14h" },
      ],
    };
  }
  if (q.includes("how much") || q.includes("year") || q.includes("total")) {
    return {
      id: crypto.randomUUID(),
      role: "kale",
      text: `You've grown ${sarah.totalKgGrown} kg of fresh produce since joining — that's about ${Math.round(sarah.totalKgGrown * 8)} salad servings, or roughly S$${Math.round(sarah.totalKgGrown * 18)} at supermarket prices for the same premium quality.`,
    };
  }
  return {
    id: crypto.randomUUID(),
    role: "kale",
    text: "I can tell you about your plot, your crops, the schedule, the AI's decisions, or your subscription. What would you like to know?",
  };
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatTurn[]>(sampleChat);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  function send(text: string) {
    if (!text.trim() || thinking) return;
    const userTurn: ChatTurn = { id: crypto.randomUUID(), role: "user", text };
    setMessages((m) => [...m, userTurn]);
    setInput("");
    setThinking(true);
    setTimeout(() => {
      setMessages((m) => [...m, mockResponse(text)]);
      setThinking(false);
    }, 700);
  }

  return (
    <div className="min-h-screen bg-paper flex flex-col">
      <AppNav />

      <main className="flex-1 max-w-3xl w-full mx-auto px-6 py-8 flex flex-col">
        <div className="mb-6">
          <Badge variant="coral" className="mb-2">RAG · &lt;500ms</Badge>
          <h1 className="text-3xl font-bold text-ink">Ask your kale.</h1>
          <p className="text-muted mt-1">
            Grounded in your plot&apos;s real-time sensors and AI decisions.
          </p>
        </div>

        {/* Messages */}
        <div className="flex-1 space-y-6 mb-6">
          <AnimatePresence initial={false}>
            {messages.map((m) => (
              <motion.div
                key={m.id}
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.3 }}
                className={m.role === "user" ? "flex justify-end" : "flex gap-3"}
              >
                {m.role === "kale" && (
                  <div className="h-9 w-9 rounded-full bg-kale flex items-center justify-center shrink-0">
                    <Image src="/assets/leaf-lime.png" alt="" width={18} height={22} />
                  </div>
                )}
                <div className={m.role === "user" ? "max-w-[80%]" : "flex-1"}>
                  <div
                    className={
                      m.role === "user"
                        ? "bg-kale text-white px-5 py-3 rounded-3xl rounded-br-md inline-block"
                        : "bg-white border border-hairline px-5 py-4 rounded-3xl rounded-tl-md"
                    }
                  >
                    <p className={m.role === "user" ? "text-white" : "text-ink leading-relaxed"}>
                      {m.text}
                    </p>
                  </div>

                  {m.citations && m.citations.length > 0 && (
                    <div className="mt-3 space-y-2">
                      <p className="text-[10px] font-bold tracking-[0.2em] uppercase text-muted">
                        Sources
                      </p>
                      {m.citations.map((c, i) => (
                        <div
                          key={i}
                          className="bg-cream rounded-2xl px-4 py-2 text-xs"
                        >
                          <p className="font-bold text-kale">{c.source}</p>
                          <p className="text-ink/70">{c.snippet}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}

            {thinking && (
              <motion.div
                key="thinking"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex gap-3"
              >
                <div className="h-9 w-9 rounded-full bg-kale flex items-center justify-center">
                  <Loader2 size={16} className="text-lime animate-spin" />
                </div>
                <div className="bg-white border border-hairline px-5 py-4 rounded-3xl rounded-tl-md">
                  <span className="flex gap-1 items-center text-muted">
                    <span className="h-2 w-2 rounded-full bg-leaf animate-pulse" />
                    <span className="h-2 w-2 rounded-full bg-leaf animate-pulse" style={{ animationDelay: "0.2s" }} />
                    <span className="h-2 w-2 rounded-full bg-leaf animate-pulse" style={{ animationDelay: "0.4s" }} />
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={scrollRef} />
        </div>

        {/* Suggested questions */}
        {messages.length <= 2 && (
          <div className="mb-4">
            <p className="text-[10px] font-bold tracking-[0.2em] uppercase text-muted mb-2">
              <Sparkles size={12} className="inline mr-1" /> Try asking
            </p>
            <div className="flex flex-wrap gap-2">
              {suggestedQuestions.map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="text-xs px-4 py-2 rounded-full bg-white border border-hairline hover:border-kale hover:text-kale transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="sticky bottom-4 bg-white border border-hairline rounded-full p-1.5 flex gap-2 items-center shadow-[0_4px_16px_rgba(0,0,0,0.06)]"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="How's my kale today?"
            className="flex-1 bg-transparent px-4 py-2 text-sm focus:outline-none"
            disabled={thinking}
          />
          <Button type="submit" size="sm" disabled={!input.trim() || thinking}>
            <Send size={14} />
          </Button>
        </form>
      </main>
    </div>
  );
}
