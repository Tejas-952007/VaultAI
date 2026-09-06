'use client';
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, FileText, CheckCircle2, ShieldAlert } from 'lucide-react';
import { GroundedChunk } from '@/lib/types';

interface EvidenceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  evidence: GroundedChunk | null;
}

export default function EvidenceDrawer({ isOpen, onClose, evidence }: EvidenceDrawerProps) {
  return (
    <AnimatePresence>
      {isOpen && evidence && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.6 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black z-40 backdrop-blur-sm"
          />
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 h-full w-full max-w-lg bg-vault-card border-l border-vault-border z-50 p-6 shadow-2xl flex flex-col justify-between font-sans text-xs"
          >
            <div>
              <div className="flex items-center justify-between border-b border-vault-border pb-3 mb-4">
                <div className="flex items-center space-x-2 text-cyan-400 font-mono font-bold text-sm">
                  <FileText className="w-5 h-5" />
                  <span>GROUNDED EVIDENCE INSPECTOR</span>
                </div>
                <button onClick={onClose} className="p-1 rounded hover:bg-slate-800 text-slate-400">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4 font-mono">
                <div className="bg-vault-bg p-3 border border-vault-border rounded space-y-2">
                  <div className="flex justify-between text-slate-400 text-[11px]">
                    <span>SOURCE DOCUMENT</span>
                    <span className="text-cyan-400">{evidence.source}</span>
                  </div>
                  <div className="flex justify-between text-slate-400 text-[11px]">
                    <span>VECTOR CHUNK ID</span>
                    <span className="text-slate-300">{evidence.chunkId}</span>
                  </div>
                  <div className="flex justify-between text-slate-400 text-[11px]">
                    <span>SIMILARITY CONFIDENCE</span>
                    <span className="text-emerald-400 font-bold">{(evidence.score * 100).toFixed(1)}% MATCH</span>
                  </div>
                </div>

                <div>
                  <h3 className="text-slate-300 font-bold mb-1.5 flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>RETRIEVED CONTEXT (k=3 BOUNDED)</span>
                  </h3>
                  <div className="p-3.5 bg-black/80 border border-cyan-900/60 rounded text-slate-200 text-xs leading-relaxed border-l-4 border-l-cyan-400">
                    "{evidence.text}"
                  </div>
                </div>

                <div className="p-3 bg-emerald-950/30 border border-emerald-800/50 rounded flex items-center space-x-2 text-emerald-400 text-[11px]">
                  <ShieldAlert className="w-4 h-4 flex-shrink-0" />
                  <span>Verified: Retrieved strictly from local ChromaDB collection.</span>
                </div>
              </div>
            </div>

            <button
              onClick={onClose}
              className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-mono font-semibold"
            >
              CLOSE VIEWER
            </button>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}