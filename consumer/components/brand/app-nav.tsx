"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LeafMark } from "@/components/brand/leaf-mark";
import { cn } from "@/lib/utils";
import { Sprout, MessageCircle, Calendar, User } from "lucide-react";

const navItems = [
  { href: "/plot",     label: "Plot",     icon: Sprout },
  { href: "/chat",     label: "Chat",     icon: MessageCircle },
  { href: "/schedule", label: "Schedule", icon: Calendar },
  { href: "/account",  label: "Account",  icon: User },
];

export function AppNav() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-hairline">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <LeafMark size="md" />
        <nav className="hidden md:flex items-center gap-1">
          {navItems.map(({ href, label, icon: Icon }) => {
            const active = pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all",
                  active ? "bg-kale text-white" : "text-ink hover:bg-cream"
                )}
              >
                <Icon size={16} />
                {label}
              </Link>
            );
          })}
        </nav>
        <Link
          href="/account"
          className="md:hidden h-10 w-10 rounded-full bg-cream flex items-center justify-center"
        >
          <User size={18} className="text-kale" />
        </Link>
      </div>
      {/* Mobile nav */}
      <nav className="md:hidden border-t border-hairline bg-white">
        <div className="flex items-center justify-around">
          {navItems.slice(0, 3).map(({ href, label, icon: Icon }) => {
            const active = pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex flex-col items-center gap-1 py-3 px-4 text-[10px] font-semibold uppercase tracking-wider transition-colors",
                  active ? "text-kale" : "text-muted"
                )}
              >
                <Icon size={18} />
                {label}
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
