import * as React from "react";
import { cn } from "@/lib/utils";

export function Badge({
  children,
  variant = "default",
  className,
}: {
  children: React.ReactNode;
  variant?: "default" | "kale" | "coral" | "outline";
  className?: string;
}) {
  const variants = {
    default: "bg-cream text-kale",
    kale: "bg-kale text-lime",
    coral: "bg-coral/10 text-coral border border-coral/20",
    outline: "border border-hairline text-muted",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-[0.15em]",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
