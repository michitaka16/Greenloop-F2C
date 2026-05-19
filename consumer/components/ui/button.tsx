import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-semibold transition-all disabled:pointer-events-none disabled:opacity-50 cursor-pointer",
  {
    variants: {
      variant: {
        primary:    "bg-kale text-white hover:bg-[#1f3a0f] shadow-[0_2px_8px_rgba(45,80,22,0.15)]",
        secondary:  "bg-cream text-kale border border-kale/20 hover:border-kale hover:bg-paper",
        ghost:      "text-kale hover:bg-cream",
        coral:      "bg-coral text-white hover:bg-[#c8633e] shadow-[0_2px_8px_rgba(224,120,86,0.20)]",
        outline:    "border border-hairline text-ink hover:border-kale hover:text-kale",
      },
      size: {
        sm:  "h-9 px-4 text-sm",
        md:  "h-11 px-6 text-sm",
        lg:  "h-14 px-8 text-base",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant, size, className }))} {...props} />
  )
);
Button.displayName = "Button";
