import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils";

export function LeafMark({
  variant = "default",
  size = "md",
  href = "/",
  className,
}: {
  variant?: "default" | "lime";
  size?: "sm" | "md" | "lg";
  href?: string | null;
  className?: string;
}) {
  const sizes = {
    sm: { img: 18, text: "text-[10px]" },
    md: { img: 24, text: "text-xs" },
    lg: { img: 32, text: "text-sm" },
  } as const;
  const s = sizes[size];
  const colors = {
    default: { src: "/assets/leaf-dark.png", text: "text-kale" },
    lime: { src: "/assets/leaf-lime.png", text: "text-lime" },
  } as const;
  const c = colors[variant];
  const inner = (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <Image src={c.src} alt="" width={s.img} height={Math.round(s.img * 1.2)} priority />
      <span className={cn("font-bold tracking-[0.25em]", s.text, c.text)}>ADOPT A KALE</span>
    </span>
  );
  if (href === null) return inner;
  return (
    <Link href={href} className="hover:opacity-80 transition-opacity">
      {inner}
    </Link>
  );
}
