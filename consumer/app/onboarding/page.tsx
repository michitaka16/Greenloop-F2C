"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import { LeafMark } from "@/components/brand/leaf-mark";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check, ArrowRight, ArrowLeft } from "lucide-react";

type Tier = "Cloud" | "Joint" | "Real";
const tiers: {
  id: Tier;
  price: number;
  body: string;
  features: string[];
  recommended?: boolean;
}[] = [
  {
    id: "Cloud",
    price: 10,
    body: "Virtual herb plot. Live camera. Weekly sample box.",
    features: ["Live plot view", "Weekly sample box", "Cancel anytime"],
  },
  {
    id: "Joint",
    price: 80,
    body: "Shared kale slot. Weekly home delivery. Choose 2 crops.",
    features: ["Weekly delivery", "Choose 2 crops", "WhatsApp updates", "Pause for travel"],
    recommended: true,
  },
  {
    id: "Real",
    price: 200,
    body: "Dedicated multi-crop rack. Choose 4–5 crops. Premium varieties.",
    features: ["1m² dedicated rack", "4–5 crops", "Premium varieties", "Video harvest msg"],
  },
];

const cropOptions = [
  { id: "kale-curly", name: "Curly Kale", emoji: "🥬" },
  { id: "basil-thai", name: "Thai Basil", emoji: "🌿" },
  { id: "spinach", name: "Spinach", emoji: "🥬" },
  { id: "arugula", name: "Arugula", emoji: "🌱" },
  { id: "mint", name: "Mint", emoji: "🌿" },
  { id: "edible-flowers", name: "Edible Flowers", emoji: "🌸" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [tier, setTier] = useState<Tier | null>(null);
  const [crops, setCrops] = useState<string[]>([]);

  const cropLimit = tier === "Real" ? 5 : tier === "Joint" ? 2 : 1;

  function toggleCrop(id: string) {
    setCrops((prev) =>
      prev.includes(id)
        ? prev.filter((x) => x !== id)
        : prev.length < cropLimit
        ? [...prev, id]
        : prev
    );
  }

  function next() {
    if (step < 3) setStep(step + 1);
    else router.push("/plot");
  }

  function back() {
    if (step > 0) setStep(step - 1);
  }

  return (
    <div className="min-h-screen bg-paper flex flex-col">
      {/* Top bar */}
      <header className="border-b border-hairline bg-white">
        <div className="max-w-3xl mx-auto px-6 h-16 flex items-center justify-between">
          <LeafMark size="md" />
          <div className="flex items-center gap-2">
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className={`h-1 rounded-full transition-all ${
                  i === step ? "w-8 bg-kale" : i < step ? "w-4 bg-leaf" : "w-4 bg-hairline"
                }`}
              />
            ))}
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-3xl w-full mx-auto px-6 py-12">
        <AnimatePresence mode="wait">
          {/* Step 0: Welcome */}
          {step === 0 && (
            <motion.div
              key="welcome"
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -20, opacity: 0 }}
              className="text-center max-w-2xl mx-auto"
            >
              <Image
                src="/assets/leaf-dark.png"
                alt=""
                width={120}
                height={144}
                className="mx-auto mb-8"
                priority
              />
              <Badge variant="coral" className="mb-4">Welcome</Badge>
              <h1 className="text-4xl md:text-5xl font-bold text-kale">
                Let&apos;s start your plot.
              </h1>
              <p className="mt-6 text-lg text-ink">
                Three minutes. Three questions. Then your AI gets to work growing your first crop.
              </p>
              <Button size="lg" onClick={next} className="mt-10">
                Begin <ArrowRight size={18} />
              </Button>
              <p className="mt-4 text-xs text-muted">No card needed for trial</p>
            </motion.div>
          )}

          {/* Step 1: Tier selection */}
          {step === 1 && (
            <motion.div
              key="tier"
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -20, opacity: 0 }}
            >
              <p className="text-sm font-bold tracking-[0.2em] uppercase text-coral">Step 1 of 3</p>
              <h1 className="text-4xl font-bold text-ink mt-2">How much garden do you want?</h1>
              <p className="text-muted mt-2">Pick a tier. You can change anytime.</p>

              <div className="mt-8 space-y-4">
                {tiers.map((t) => {
                  const selected = tier === t.id;
                  return (
                    <button
                      key={t.id}
                      onClick={() => setTier(t.id)}
                      className={`w-full text-left p-6 rounded-3xl border-2 transition-all ${
                        selected
                          ? "border-kale bg-white shadow-[0_4px_16px_rgba(45,80,22,0.10)]"
                          : "border-hairline bg-white hover:border-kale/40"
                      }`}
                    >
                      <div className="flex items-start gap-4">
                        <div
                          className={`h-6 w-6 rounded-full border-2 flex items-center justify-center shrink-0 mt-0.5 transition-colors ${
                            selected ? "border-kale bg-kale" : "border-hairline"
                          }`}
                        >
                          {selected && <Check size={14} className="text-white" />}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-baseline gap-3 flex-wrap">
                            <h3 className="text-xl font-bold text-ink">{t.id}</h3>
                            {t.recommended && <Badge variant="coral">Most popular</Badge>}
                            <span className="ml-auto text-2xl font-bold text-kale">
                              S${t.price}
                              <span className="text-sm font-normal text-muted"> / mo</span>
                            </span>
                          </div>
                          <p className="text-sm text-ink mt-1">{t.body}</p>
                          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1">
                            {t.features.map((f) => (
                              <span key={f} className="text-xs text-muted flex items-center gap-1">
                                <Check size={12} className="text-leaf" /> {f}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>

              <div className="mt-10 flex gap-3">
                <Button variant="ghost" onClick={back}>
                  <ArrowLeft size={16} /> Back
                </Button>
                <Button onClick={next} disabled={!tier} className="ml-auto">
                  Continue <ArrowRight size={16} />
                </Button>
              </div>
            </motion.div>
          )}

          {/* Step 2: Crop selection */}
          {step === 2 && (
            <motion.div
              key="crops"
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -20, opacity: 0 }}
            >
              <p className="text-sm font-bold tracking-[0.2em] uppercase text-coral">Step 2 of 3</p>
              <h1 className="text-4xl font-bold text-ink mt-2">Pick your first crops.</h1>
              <p className="text-muted mt-2">
                You picked <strong className="text-kale">{tier}</strong>. Choose up to {cropLimit}{" "}
                {cropLimit === 1 ? "crop" : "crops"}.
              </p>

              <div className="mt-8 grid grid-cols-2 md:grid-cols-3 gap-3">
                {cropOptions.map((c) => {
                  const selected = crops.includes(c.id);
                  const disabled = !selected && crops.length >= cropLimit;
                  return (
                    <button
                      key={c.id}
                      onClick={() => toggleCrop(c.id)}
                      disabled={disabled}
                      className={`p-5 rounded-3xl border-2 transition-all text-center ${
                        selected
                          ? "border-kale bg-white shadow-[0_4px_16px_rgba(45,80,22,0.10)]"
                          : disabled
                          ? "border-hairline bg-cream/40 text-muted cursor-not-allowed opacity-50"
                          : "border-hairline bg-white hover:border-kale/40"
                      }`}
                    >
                      <div className="text-5xl mb-3">{c.emoji}</div>
                      <p className="font-bold text-ink text-sm">{c.name}</p>
                      {selected && (
                        <div className="mt-2 inline-flex items-center justify-center h-6 w-6 rounded-full bg-kale">
                          <Check size={14} className="text-white" />
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>

              <p className="mt-4 text-sm text-muted">
                Selected: {crops.length} / {cropLimit}
              </p>

              <div className="mt-10 flex gap-3">
                <Button variant="ghost" onClick={back}>
                  <ArrowLeft size={16} /> Back
                </Button>
                <Button onClick={next} disabled={crops.length === 0} className="ml-auto">
                  Continue <ArrowRight size={16} />
                </Button>
              </div>
            </motion.div>
          )}

          {/* Step 3: Confirmation */}
          {step === 3 && (
            <motion.div
              key="confirm"
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -20, opacity: 0 }}
              className="text-center max-w-xl mx-auto"
            >
              <div className="relative inline-block mb-8">
                <Image
                  src="/assets/leaf-dark.png"
                  alt=""
                  width={140}
                  height={168}
                  priority
                />
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", delay: 0.3 }}
                  className="absolute -bottom-2 -right-2 h-14 w-14 rounded-full bg-coral flex items-center justify-center"
                >
                  <Check size={28} className="text-white" strokeWidth={3} />
                </motion.div>
              </div>

              <Badge variant="coral" className="mb-4">Plot reserved</Badge>
              <h1 className="text-4xl md:text-5xl font-bold text-kale leading-tight">
                Welcome to your plot.
              </h1>
              <p className="mt-6 text-lg text-ink">
                Your <strong>{tier}</strong> tier is ready. We&apos;ve allocated Plot #042 with
                your {crops.length} chosen{" "}
                {crops.length === 1 ? "crop" : "crops"}. AI will start growing tomorrow at 06:00 SGT.
              </p>

              <div className="mt-8 bg-cream rounded-2xl p-6 text-left">
                <p className="text-xs font-bold tracking-[0.2em] uppercase text-muted">First harvest</p>
                <p className="text-2xl font-bold text-kale mt-1">~ 6 weeks</p>
                <p className="text-sm text-muted mt-1">
                  We&apos;ll WhatsApp you weekly, and Sarah&apos;s app shows live status anytime.
                </p>
              </div>

              <Button size="lg" onClick={next} className="mt-10">
                Open my plot <ArrowRight size={18} />
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
