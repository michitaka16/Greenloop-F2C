import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { LeafMark } from "@/components/brand/leaf-mark";
import { ArrowRight, Check } from "lucide-react";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-white">
      {/* Top nav */}
      <header className="border-b border-hairline">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <LeafMark size="md" />
          <div className="flex items-center gap-2">
            <Link href="/plot">
              <Button variant="ghost" size="sm">Sign in</Button>
            </Link>
            <Link href="/onboarding">
              <Button size="sm">Start your plot</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative max-w-6xl mx-auto px-6 pt-20 pb-24 md:pt-32 md:pb-40 overflow-hidden">
        {/* Decorative leaves */}
        <Image
          src="/assets/leaf-dark.png"
          alt=""
          width={400}
          height={480}
          className="hidden md:block absolute right-0 top-12 opacity-100 select-none pointer-events-none"
          priority
        />
        <Image
          src="/assets/leaf-lime.png"
          alt=""
          width={180}
          height={216}
          className="hidden md:block absolute right-72 top-56 opacity-90 select-none pointer-events-none"
        />

        <div className="relative max-w-2xl">
          <p className="text-sm font-bold tracking-[0.25em] text-coral uppercase mb-6">
            Singapore · 2026
          </p>
          <h1 className="text-6xl md:text-8xl font-bold text-kale leading-[0.95] tracking-tight">
            Adopt
            <br />
            a Kale.
          </h1>
          <p className="mt-8 text-2xl md:text-3xl italic text-coral font-semibold">
            Your apartment&apos;s vegetable patch.
          </p>
          <p className="mt-3 text-lg text-ink max-w-xl">
            80% of Singaporeans live in HDB flats. No garden. No allotment. We give you a
            real vertical-farm plot — grown by AI, harvested for your dinner.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row gap-3">
            <Link href="/onboarding">
              <Button size="lg">
                Start your plot <ArrowRight size={18} />
              </Button>
            </Link>
            <Link href="/plot">
              <Button variant="secondary" size="lg">
                See Sarah&apos;s plot
              </Button>
            </Link>
          </div>
          <p className="mt-6 text-sm text-muted">
            From S$10/mo · Cancel anytime · Singapore-grown · Pesticide-free
          </p>
        </div>
      </section>

      {/* Three tiers */}
      <section className="bg-paper border-y border-hairline">
        <div className="max-w-6xl mx-auto px-6 py-20">
          <p className="text-sm font-bold tracking-[0.25em] text-coral uppercase mb-2">
            Three tiers · One brand
          </p>
          <h2 className="text-4xl md:text-5xl font-bold text-ink mb-12 max-w-2xl">
            Pick how much garden you want.
          </h2>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Cloud */}
            <div className="bg-white rounded-3xl p-8 border border-hairline relative">
              <div className="h-2 w-12 bg-leaf rounded-full mb-6" />
              <p className="text-xs font-bold tracking-[0.2em] text-leaf uppercase">Cloud</p>
              <p className="text-5xl font-bold text-ink mt-2">
                S$10<span className="text-base text-muted font-normal"> / month</span>
              </p>
              <p className="mt-6 text-ink">Virtual herb plot. Live camera. Weekly micro-harvest sample box.</p>
              <ul className="mt-6 space-y-2 text-sm text-muted">
                <li className="flex gap-2"><Check size={16} className="text-leaf shrink-0 mt-0.5" /> Live plot view</li>
                <li className="flex gap-2"><Check size={16} className="text-leaf shrink-0 mt-0.5" /> Weekly sample box</li>
                <li className="flex gap-2"><Check size={16} className="text-leaf shrink-0 mt-0.5" /> Cancel anytime</li>
              </ul>
              <p className="mt-6 text-xs italic text-muted">Entry tier · low-friction trial</p>
            </div>

            {/* Joint */}
            <div className="bg-white rounded-3xl p-8 border-2 border-kale relative shadow-[0_8px_24px_rgba(45,80,22,0.08)]">
              <div className="absolute -top-3 left-8">
                <span className="bg-coral text-white text-[10px] font-bold tracking-[0.15em] uppercase px-3 py-1 rounded-full">Most popular</span>
              </div>
              <div className="h-2 w-12 bg-kale rounded-full mb-6" />
              <p className="text-xs font-bold tracking-[0.2em] text-kale uppercase">Joint</p>
              <p className="text-5xl font-bold text-ink mt-2">
                S$80<span className="text-base text-muted font-normal"> / month</span>
              </p>
              <p className="mt-6 text-ink">Shared kale slot. Weekly home delivery. Choose 2 crops.</p>
              <ul className="mt-6 space-y-2 text-sm text-muted">
                <li className="flex gap-2"><Check size={16} className="text-kale shrink-0 mt-0.5" /> Weekly delivery</li>
                <li className="flex gap-2"><Check size={16} className="text-kale shrink-0 mt-0.5" /> Choose 2 crops</li>
                <li className="flex gap-2"><Check size={16} className="text-kale shrink-0 mt-0.5" /> WhatsApp updates</li>
                <li className="flex gap-2"><Check size={16} className="text-kale shrink-0 mt-0.5" /> Pause for travel</li>
              </ul>
              <p className="mt-6 text-xs italic text-muted">Most popular · weekly meals</p>
            </div>

            {/* Real */}
            <div className="bg-kale rounded-3xl p-8 text-white relative">
              <div className="h-2 w-12 bg-coral rounded-full mb-6" />
              <p className="text-xs font-bold tracking-[0.2em] text-coral uppercase">Real</p>
              <p className="text-5xl font-bold mt-2">
                S$200<span className="text-base text-lime font-normal"> / month</span>
              </p>
              <p className="mt-6 text-lime">Dedicated multi-crop rack. Weekly delivery. Choose 4–5 crops.</p>
              <ul className="mt-6 space-y-2 text-sm text-lime/80">
                <li className="flex gap-2"><Check size={16} className="text-lime shrink-0 mt-0.5" /> Dedicated 1m² rack</li>
                <li className="flex gap-2"><Check size={16} className="text-lime shrink-0 mt-0.5" /> 4–5 crops at once</li>
                <li className="flex gap-2"><Check size={16} className="text-lime shrink-0 mt-0.5" /> Premium varieties</li>
                <li className="flex gap-2"><Check size={16} className="text-lime shrink-0 mt-0.5" /> Video harvest msg</li>
              </ul>
              <p className="mt-6 text-xs italic text-lime/70">Premium tier · serious cooks</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-hairline">
        <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col md:flex-row items-center justify-between gap-4">
          <LeafMark size="sm" href={null} />
          <p className="text-xs text-muted">
            © 2026 GreenLoop F2C · Singapore · MGMT 655 Capstone
          </p>
        </div>
      </footer>
    </main>
  );
}
