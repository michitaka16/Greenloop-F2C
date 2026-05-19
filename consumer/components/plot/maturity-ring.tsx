"use client";

import { motion } from "framer-motion";
import Image from "next/image";

export function MaturityRing({
  percent,
  size = 280,
}: {
  percent: number;
  size?: number;
}) {
  const stroke = 12;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percent / 100) * circumference;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      {/* Background circle */}
      <svg width={size} height={size} className="rotate-[-90deg]">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--cream)"
          strokeWidth={stroke}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--leaf)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.6, ease: "easeOut" }}
        />
      </svg>

      {/* Kale leaf in center */}
      <motion.div
        initial={{ scale: 0.85, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.6 }}
        className="absolute inset-0 flex items-center justify-center"
      >
        <Image
          src="/assets/leaf-dark.png"
          alt="kale"
          width={size * 0.5}
          height={size * 0.5 * 1.2}
          priority
        />
      </motion.div>

      {/* Percentage label */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 1.4, duration: 0.4 }}
        className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 bg-white px-4 py-2 rounded-full border border-hairline shadow-sm"
      >
        <p className="text-2xl font-bold text-kale leading-none">
          {percent}<span className="text-base font-normal text-muted">%</span>
        </p>
      </motion.div>
    </div>
  );
}
