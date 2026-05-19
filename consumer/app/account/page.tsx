"use client";

import Link from "next/link";
import { AppNav } from "@/components/brand/app-nav";
import { Card, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { sarah } from "@/lib/mock-data";
import { CreditCard, Settings, LogOut, ArrowUpRight } from "lucide-react";

export default function AccountPage() {
  return (
    <div className="min-h-screen bg-paper">
      <AppNav />
      <main className="max-w-3xl mx-auto px-6 py-8 md:py-12">
        <div className="flex items-center gap-4 mb-8">
          <div className="h-16 w-16 rounded-full bg-kale flex items-center justify-center text-2xl font-bold text-lime">
            {sarah.initial}
          </div>
          <div>
            <h1 className="text-2xl font-bold text-ink">{sarah.name}</h1>
            <p className="text-sm text-muted">
              {sarah.flat} · {sarah.hood}
            </p>
          </div>
        </div>

        {/* Subscription */}
        <Card className="mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-[10px] font-bold tracking-[0.2em] uppercase text-muted">
                Current plan
              </p>
              <h2 className="text-2xl font-bold text-ink mt-1">{sarah.tier} tier</h2>
              <p className="text-sm text-muted mt-1">
                Plot #{sarah.plotId} · started {sarah.startedAt}
              </p>
            </div>
            <Badge variant="kale">Active</Badge>
          </div>
          <div className="grid grid-cols-2 gap-3 mt-4">
            <Button variant="secondary" size="sm" className="w-full">
              <CreditCard size={14} /> Billing
            </Button>
            <Button variant="coral" size="sm" className="w-full">
              <ArrowUpRight size={14} /> Upgrade to Real
            </Button>
          </div>
        </Card>

        {/* Settings */}
        <Card className="mb-6">
          <CardTitle>
            <span className="flex items-center gap-2">
              <Settings size={18} className="text-kale" /> Preferences
            </span>
          </CardTitle>
          <div className="mt-4 divide-y divide-hairline">
            <div className="py-3 flex items-center justify-between">
              <div>
                <p className="font-medium text-ink text-sm">WhatsApp updates</p>
                <p className="text-xs text-muted">Weekly + on harvest</p>
              </div>
              <Badge variant="default">On</Badge>
            </div>
            <div className="py-3 flex items-center justify-between">
              <div>
                <p className="font-medium text-ink text-sm">Delivery window</p>
                <p className="text-xs text-muted">Saturday morning</p>
              </div>
              <Button variant="ghost" size="sm">Change</Button>
            </div>
            <div className="py-3 flex items-center justify-between">
              <div>
                <p className="font-medium text-ink text-sm">Pause subscription</p>
                <p className="text-xs text-muted">For travel or holidays</p>
              </div>
              <Button variant="ghost" size="sm">Pause</Button>
            </div>
          </div>
        </Card>

        <div className="flex gap-3 justify-center">
          <Link href="/">
            <Button variant="ghost" size="sm">
              <LogOut size={14} /> Sign out
            </Button>
          </Link>
        </div>
      </main>
    </div>
  );
}
