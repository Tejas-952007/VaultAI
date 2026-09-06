"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";

const BOOT_LOGS = [
  "INITIALIZING LOCAL SOVEREIGN RUNTIME...",
  "VERIFYING SHA-256 ARTIFACT PROVENANCE...",
  "ISOLATING NETWORK NAMESPACES (AIR-GAP ENFORCED)...",
  "LOADING CHROMA VECTOR EMBEDDINGS (k=3 CONSTRAINTS)...",
  "WARMING LOCAL OLLAMA CORES: Qwen3.5 | DeepSeek 1.3B | Qwen3-VL:8B...",
  "VAULTAI WORKBENCH IS READY."
];

export default function BootSplash() {
  const [logs, setLogs] = useState<string[]>([]);
  const [isVisible, setIsVisible] = useState(true);
  const [bootTime, setBootTime] = useState<string | null>(null);

  useEffect(() => {
    setBootTime(new Date().toLocaleTimeString());
    let timeout: NodeJS.Timeout;
    BOOT_LOGS.forEach((log, index) => {
      timeout = setTimeout(() => {
        setLogs(prev => [...prev, log]);
        if (index === BOOT_LOGS.length - 1) {
          setTimeout(() => setIsVisible(false), 800);
        }
      }, index * 350);
    });
    return () => clearTimeout(timeout);
  }, []);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div 
          exit={{ opacity: 0, scale: 1.05 }}
          className="fixed inset-0 z-[100] bg-obsidian flex flex-col items-center justify-center p-6 font-mono"
        >
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-12 relative"
          >
            <div className="w-24 h-24 border-2 border-emerald-500 rotate-45 flex items-center justify-center relative shadow-[0_0_30px_rgba(16,185,129,0.3)]">
              <div className="absolute inset-1 border border-emerald-500/30" />
              <span className="-rotate-45 text-emerald-500 font-bold text-2xl tracking-tighter">VAI</span>
            </div>
          </motion.div>

          <div className="w-full max-w-md space-y-1">
            {logs.map((log, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-[10px] text-emerald-500/80 uppercase tracking-widest"
              >
                <span className="text-emerald-500/40 mr-2">[{bootTime ?? '--:--:--'}]</span>
                {log}
              </motion.div>
            ))}
            <motion.div 
              animate={{ opacity: [0, 1, 0] }}
              transition={{ repeat: Infinity, duration: 0.8 }}
              className="w-2 h-4 bg-emerald-500 inline-block align-middle ml-1"
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}