"use client";

import { useMemo } from "react";

/**
 * Animated gradient background with floating translucent green shapes.
 * Lightweight — pure CSS animations, no canvas or 3D.
 */
export default function AnimatedBackground() {
  const shapes = useMemo(() => {
    return [
      { size: 320, x: "10%", y: "15%", color: "bg-brand-green/10", duration: "14s", delay: "0s", rounded: "rounded-full" },
      { size: 220, x: "75%", y: "10%", color: "bg-brand-teal/10", duration: "18s", delay: "2s", rounded: "rounded-3xl" },
      { size: 180, x: "60%", y: "70%", color: "bg-brand-emerald/10", duration: "16s", delay: "4s", rounded: "rounded-full" },
      { size: 260, x: "20%", y: "75%", color: "bg-brand-green/8", duration: "20s", delay: "1s", rounded: "rounded-3xl" },
      { size: 140, x: "85%", y: "50%", color: "bg-brand-lime/8", duration: "12s", delay: "3s", rounded: "rounded-full" },
      { size: 200, x: "40%", y: "35%", color: "bg-brand-teal/8", duration: "22s", delay: "5s", rounded: "rounded-full" },
    ];
  }, []);

  return (
    <div className="fixed inset-0 -z-10 overflow-hidden bg-animated-gradient">
      {shapes.map((s, i) => (
        <div
          key={i}
          className={`floating-shape absolute blur-3xl ${s.color} ${s.rounded}`}
          style={{
            width: s.size,
            height: s.size,
            left: s.x,
            top: s.y,
            "--duration": s.duration,
            "--delay": s.delay,
          } as React.CSSProperties}
        />
      ))}
    </div>
  );
}
