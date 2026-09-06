"use client";
import { motion } from "framer-motion";

export default function AmbientRadarBg() {
  return (
    <div className="fixed inset-0 z-[-1] overflow-hidden pointer-events-none bg-obsidian">
      {/* Hex Grid Layer */}
      <div className="absolute inset-0 hex-grid opacity-30" />
      
      {/* Radar Sweep Line */}
      <motion.div 
        initial={{ top: "-10%" }}
        animate={{ top: "110%" }}
        transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
        className="absolute left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-cyan-500/40 to-transparent shadow-[0_0_15px_rgba(6,182,212,0.5)]"
      />

      {/* Radial Gradient Vignette */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,rgba(7,10,15,0.8)_100%)]" />
    </div>
  );
}