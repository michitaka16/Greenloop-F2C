"use client";

import { motion } from "framer-motion";
import { AppNav } from "@/components/brand/app-nav";
import { Card, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { upcomingDeliveries, crops } from "@/lib/mock-data";
import { Calendar, Truck, Sprout } from "lucide-react";

export default function SchedulePage() {
  return (
    <div className="min-h-screen bg-paper">
      <AppNav />
      <main className="max-w-4xl mx-auto px-6 py-8 md:py-12">
        <div className="mb-8">
          <Badge variant="coral" className="mb-2">VRP · 48ms solve</Badge>
          <h1 className="text-3xl md:text-4xl font-bold text-ink">Your harvest calendar.</h1>
          <p className="text-muted mt-1">
            Optimised for your weekly rhythm, weather-corrected.
          </p>
        </div>

        {/* Upcoming */}
        <section className="mb-12">
          <h2 className="text-sm font-bold tracking-[0.2em] uppercase text-muted mb-4">
            Upcoming deliveries
          </h2>
          <div className="space-y-3">
            {upcomingDeliveries.map((d, i) => (
              <motion.div
                key={i}
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: i * 0.08 }}
              >
                <Card>
                  <div className="flex items-center gap-6">
                    <div className="text-center shrink-0 min-w-16">
                      <p className="text-[10px] font-bold tracking-wider uppercase text-coral">
                        {d.date.split(" ")[0]}
                      </p>
                      <p className="text-3xl font-bold text-kale leading-none mt-1">
                        {d.date.split(" ")[1]}
                      </p>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap mb-2">
                        <Truck size={14} className="text-kale" />
                        <p className="text-xs font-bold tracking-wider uppercase text-muted">
                          Delivery window 09:00–11:00
                        </p>
                      </div>
                      {d.items.map((item, j) => (
                        <p key={j} className="text-sm text-ink flex items-center gap-2">
                          <Sprout size={14} className="text-leaf" /> {item}
                        </p>
                      ))}
                    </div>
                    <Badge variant={d.status === "scheduled" ? "default" : "outline"}>
                      {d.status}
                    </Badge>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Crop timeline */}
        <section>
          <h2 className="text-sm font-bold tracking-[0.2em] uppercase text-muted mb-4">
            Growth timeline
          </h2>
          <div className="space-y-4">
            {crops.map((c) => {
              const pct = (c.daysIn / c.totalDays) * 100;
              return (
                <Card key={c.id}>
                  <div className="flex items-center gap-4 mb-3">
                    <div className="h-12 w-12 rounded-2xl bg-cream flex items-center justify-center text-2xl">
                      {c.emoji}
                    </div>
                    <div className="flex-1">
                      <p className="text-xs text-muted">{c.variety}</p>
                      <p className="font-bold text-ink">{c.name}</p>
                    </div>
                    <p className="text-sm text-muted">
                      Day {c.daysIn} / {c.totalDays}
                    </p>
                  </div>
                  <div className="relative h-8 bg-cream rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ duration: 1.2, ease: "easeOut" }}
                      className="absolute inset-y-0 left-0 bg-gradient-to-r from-leaf to-kale rounded-full"
                    />
                    <div className="absolute inset-0 flex items-center px-3">
                      <span className="text-xs font-bold text-white drop-shadow-sm">
                        {Math.round(pct)}% mature
                      </span>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </section>
      </main>
    </div>
  );
}
