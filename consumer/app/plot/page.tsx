"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { AppNav } from "@/components/brand/app-nav";
import { Card, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MaturityRing } from "@/components/plot/maturity-ring";
import { sarah, crops, status, upcomingDeliveries, recentEvents } from "@/lib/mock-data";
import {
  Calendar,
  MessageCircle,
  Sparkles,
  Sprout,
  Droplets,
  Zap,
  TrendingUp,
  ArrowRight,
} from "lucide-react";

function StatBox({
  icon: Icon,
  label,
  value,
  unit,
}: {
  icon: React.ComponentType<{ size?: number; className?: string }>;
  label: string;
  value: string | number;
  unit?: string;
}) {
  return (
    <div className="flex items-center gap-3 px-4 py-3 rounded-2xl bg-cream">
      <Icon size={18} className="text-kale shrink-0" />
      <div className="min-w-0">
        <p className="text-[10px] font-bold tracking-[0.15em] uppercase text-muted">{label}</p>
        <p className="text-sm font-semibold text-ink truncate">
          {value}
          {unit && <span className="text-xs font-normal text-muted ml-1">{unit}</span>}
        </p>
      </div>
    </div>
  );
}

export default function PlotPage() {
  return (
    <div className="min-h-screen bg-paper">
      <AppNav />

      <main className="max-w-6xl mx-auto px-6 py-8 md:py-12">
        {/* Greeting */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.4 }}
          className="mb-8"
        >
          <p className="text-sm text-muted">Good morning, {sarah.name.split(" ")[0]}.</p>
          <h1 className="text-3xl md:text-4xl font-bold text-ink mt-1">
            Your kale is <span className="text-kale">{status.maturity}% ready</span>.
          </h1>
        </motion.div>

        {/* Hero card */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <Card className="overflow-hidden p-0">
            <div className="grid md:grid-cols-2">
              {/* Left: Maturity ring */}
              <div className="bg-gradient-to-br from-cream via-white to-paper p-8 md:p-12 flex flex-col items-center justify-center border-b md:border-b-0 md:border-r border-hairline relative overflow-hidden">
                <Badge variant="coral" className="mb-6">FOR SARAH&apos;S DINNER</Badge>
                <MaturityRing percent={status.maturity} size={260} />
                <p className="mt-10 text-center text-sm text-muted">
                  Plot #{sarah.plotId} · Day {sarah.daysIn} of {sarah.totalDays}
                </p>
              </div>

              {/* Right: details */}
              <div className="p-8 md:p-12 flex flex-col">
                <p className="text-xs font-bold tracking-[0.2em] uppercase text-coral">Now growing</p>
                <h2 className="text-2xl font-bold text-ink mt-2">
                  Curly Kale <span className="text-muted font-normal">+ Thai Basil</span>
                </h2>
                <p className="mt-2 text-sm text-muted">Singapore vertical farm · run by AI 24/7</p>

                <div className="mt-6 p-4 bg-kale text-lime rounded-2xl">
                  <p className="text-xs font-bold tracking-[0.15em] uppercase text-lime/70">Next harvest</p>
                  <p className="text-2xl font-bold text-white mt-1">{sarah.nextHarvest}</p>
                  <p className="text-sm text-lime/90 mt-1">
                    Auto-tuned at {status.lastTuned} · weather-corrected
                  </p>
                </div>

                <div className="mt-6 grid grid-cols-2 gap-3">
                  <StatBox icon={Sprout} label="Crops" value={crops.length} />
                  <StatBox icon={Calendar} label="Day" value={`${sarah.daysIn}/${sarah.totalDays}`} />
                  <StatBox icon={Droplets} label="Water" value={status.waterUsedL} unit="L" />
                  <StatBox icon={Zap} label="Energy" value={status.energyKwh} unit="kWh/wk" />
                </div>

                <div className="mt-auto pt-6 flex flex-wrap gap-2">
                  <Link href="/chat" className="flex-1">
                    <Button variant="primary" className="w-full">
                      <MessageCircle size={16} /> Ask your kale
                    </Button>
                  </Link>
                  <Link href="/schedule">
                    <Button variant="secondary">
                      <Calendar size={16} /> Schedule
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </Card>
        </motion.div>

        {/* What's growing */}
        <section className="mt-12">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-ink">What&apos;s in your plot</h2>
            <Link href="/schedule" className="text-sm text-kale font-semibold hover:underline">
              See full schedule →
            </Link>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            {crops.map((crop, i) => {
              const pct = Math.round((crop.daysIn / crop.totalDays) * 100);
              return (
                <motion.div
                  key={crop.id}
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ duration: 0.4, delay: 0.2 + i * 0.1 }}
                >
                  <Card>
                    <div className="flex items-start gap-4">
                      <div className="h-14 w-14 rounded-2xl bg-cream flex items-center justify-center text-3xl shrink-0">
                        {crop.emoji}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-muted">{crop.variety}</p>
                        <h3 className="text-lg font-bold text-ink">{crop.name}</h3>
                        <div className="mt-3 flex items-center gap-3">
                          <div className="flex-1 h-1.5 bg-cream rounded-full overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${pct}%` }}
                              transition={{ duration: 1.2, delay: 0.4 + i * 0.1, ease: "easeOut" }}
                              className="h-full bg-leaf"
                            />
                          </div>
                          <span className="text-xs font-bold text-kale tabular-nums">{pct}%</span>
                        </div>
                        <p className="mt-2 text-xs text-muted">
                          Day {crop.daysIn} of {crop.totalDays}
                        </p>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        </section>

        {/* Two columns: deliveries + activity */}
        <div className="mt-12 grid md:grid-cols-2 gap-6">
          {/* Upcoming deliveries */}
          <Card>
            <CardTitle>
              <span className="flex items-center gap-2">
                <Calendar size={18} className="text-kale" /> Upcoming deliveries
              </span>
            </CardTitle>
            <div className="mt-4 space-y-4">
              {upcomingDeliveries.map((d, i) => (
                <div key={i} className="flex gap-4">
                  <div className="text-center shrink-0">
                    <p className="text-[10px] font-bold tracking-wider uppercase text-coral">
                      {d.date.split(" ")[0]}
                    </p>
                    <p className="text-2xl font-bold text-kale leading-tight">
                      {d.date.split(" ")[1]}
                    </p>
                  </div>
                  <div className="flex-1 border-l border-hairline pl-4">
                    {d.items.map((item, j) => (
                      <p key={j} className="text-sm text-ink">{item}</p>
                    ))}
                    <p className="mt-1 text-xs text-muted capitalize">{d.status}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Recent activity */}
          <Card>
            <CardTitle>
              <span className="flex items-center gap-2">
                <Sparkles size={18} className="text-kale" /> Recent activity
              </span>
            </CardTitle>
            <div className="mt-4 space-y-3">
              {recentEvents.slice(0, 5).map((e, i) => (
                <div key={i} className="flex gap-3 pb-3 border-b border-hairline last:border-0 last:pb-0">
                  <div className="h-8 w-8 rounded-full bg-cream flex items-center justify-center shrink-0">
                    <Sprout size={14} className="text-kale" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-ink leading-snug">{e.text}</p>
                    <p className="text-xs text-muted mt-0.5">{e.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Lifetime stats */}
        <section className="mt-12">
          <Card className="bg-kale text-lime border-kale">
            <div className="grid md:grid-cols-3 gap-6">
              <div>
                <p className="text-xs font-bold tracking-[0.2em] uppercase text-lime/70">Total grown</p>
                <p className="text-3xl font-bold text-white mt-1">{sarah.totalKgGrown} kg</p>
                <p className="text-xs text-lime/80 mt-1">since you joined</p>
              </div>
              <div>
                <p className="text-xs font-bold tracking-[0.2em] uppercase text-lime/70">Deliveries</p>
                <p className="text-3xl font-bold text-white mt-1">{sarah.totalDeliveries}</p>
                <p className="text-xs text-lime/80 mt-1">all on time</p>
              </div>
              <div className="flex items-center justify-end">
                <Link href="/account">
                  <Button variant="coral">
                    <TrendingUp size={16} /> Upgrade to Real
                    <ArrowRight size={16} />
                  </Button>
                </Link>
              </div>
            </div>
          </Card>
        </section>
      </main>
    </div>
  );
}
