'use client';
import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import BootSplash from '@/components/BootSplash';
import ZeroEgressGraph from '@/components/ZeroEgressGraph';
import ModelStatusPill from '@/components/ModelStatusPill';
import EvidenceDrawer from '@/components/EvidenceDrawer';
import { ChatMessage, GroundedChunk, DocumentItem } from '@/lib/types';
import { VaultAPI, HealthResponse } from '@/lib/api';
import {
  Send, Paperclip, FileText, Eye,
  Sparkles, ArrowRight, Layers, ChevronRight, RefreshCw,
  AlertTriangle, CheckCircle2
} from 'lucide-react';

const SUGGESTED_PROMPTS = [
  { icon: '📋', title: 'Summarize uploaded document', query: 'Summarize the key points from the uploaded document.' },
  { icon: '🔍', title: 'Find specific information', query: 'What are the main safety requirements mentioned in the document?' },
  { icon: '📊', title: 'Extract structured data', query: 'List all numeric limits or thresholds mentioned in the document.' },
];

const stableTimestamp = '—';

export default function WorkbenchPage() {
  const [inputPrompt, setInputPrompt] = useState('');
  const [selectedEvidence, setSelectedEvidence] = useState<GroundedChunk | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [visionImagePath, setVisionImagePath] = useState<string | undefined>();
  const [visionUploadError, setVisionUploadError] = useState<string | null>(null);
  const [isUploadingVision, setIsUploadingVision] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const visionInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-init',
      role: 'assistant',
      content: 'VaultAI sovereign runtime is initialising. Checking backend health…',
      timestamp: stableTimestamp,
    }
  ]);

  // ── Bootstrap: health + document list ────────────────────────────────────
  useEffect(() => {
    async function init() {
      try {
        const h = await VaultAPI.getHealth();
        setHealth(h);
        setMessages([{
          id: 'msg-init',
          role: 'assistant',
          content: `VaultAI runtime ready. Backend: ${h.status} | Ollama: ${h.ollama_status} | Model: ${h.ollama_model}. Upload a PDF to the Knowledge Base and start querying.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        }]);
        try {
          const docs = await VaultAPI.listDocuments();
          setDocuments(docs.map(d => ({
            id: d.id,
            name: d.filename,
            chunks: d.chunks_count,
            sha256: d.sha256,
            ingestedAt: d.created_at,
            status: d.status,
          })));
        } catch {
          // Document access is permission-protected; health remains authoritative.
        }
      } catch {
        setHealth(null);
        setMessages([{
          id: 'msg-init',
          role: 'assistant',
          content: '⚠️ Backend unavailable. Start the FastAPI server (uvicorn backend.app.main:app --reload) and refresh.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
          error: 'backend_unavailable',
        }]);
      }
    }
    init();
  }, []);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ── PDF upload ────────────────────────────────────────────────────────────
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith('.pdf')) {
      setUploadError('Only PDF files are supported.');
      return;
    }
    setUploadError(null);
    setIsUploading(true);
    try {
      const doc = await VaultAPI.uploadDocument(file);
      setDocuments(prev => [...prev.filter(d => d.id !== doc.id), {
        id: doc.id,
        name: doc.filename,
        chunks: doc.chunks_count,
        sha256: doc.sha256,
        ingestedAt: doc.created_at,
        status: doc.status,
      }]);
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // ── Chat ──────────────────────────────────────────────────────────────────
  const executeQuery = async (queryText: string) => {
    if (!queryText.trim() || isExecuting) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: queryText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    };

    setIsExecuting(true);
    setMessages(prev => [...prev, userMsg]);
    setInputPrompt('');

    try {
      const resp = await VaultAPI.chat({ message: queryText, image_path: visionImagePath });

      // Map backend evidence to UI GroundedChunk
      const evidence: GroundedChunk[] = (resp.evidence || []).map(e => ({
        documentId: e.document_id,
        source: e.source,
        chunkId: e.chunk_id,
        score: e.score,
        text: e.snippet,
      }));

      const agentMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: resp.answer,
        route: resp.route,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        evidence: evidence.length > 0 ? evidence : undefined,
        provenance: {
          model: resp.model,
          route: resp.route,
          durationMs: resp.duration_ms,
          requestId: resp.request_id,
          status: resp.status,
        },
      };
      if (resp.generated_code) {
        agentMsg.content += `\n\nGenerated code:\n${resp.generated_code}`;
      }
      if (resp.sandbox_result) {
        agentMsg.content += `\n\nSandbox stdout:\n${resp.sandbox_result.stdout || '(none)'}\nExit code: ${resp.sandbox_result.exit_code}`;
      }
      setMessages(prev => [...prev, agentMsg]);
    } catch (err: unknown) {
      const errorMsg: ChatMessage = {
        id: `msg-err-${Date.now()}`,
        role: 'assistant',
        content: `Error: ${err instanceof Error ? err.message : 'Request failed. Check the backend server.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        error: 'chat_error',
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleVisionUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setVisionUploadError(null);
    setIsUploadingVision(true);
    try {
      const result = await VaultAPI.uploadVisionImage(file);
      setVisionImagePath(result.image_path);
    } catch (err: unknown) {
      setVisionUploadError(err instanceof Error ? err.message : 'Image upload failed.');
    } finally {
      setIsUploadingVision(false);
      if (visionInputRef.current) visionInputRef.current.value = '';
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <>
      <BootSplash />

      <div className="h-[calc(100vh-3.5rem)] grid grid-cols-12 gap-0 overflow-hidden font-sans">

        {/* ── LEFT SIDEBAR: Knowledge Base + Model Status ── */}
        <aside className="col-span-12 md:col-span-3 border-r border-white/[0.08] bg-[#090D16]/90 p-4 flex flex-col justify-between overflow-y-auto">
          <div className="space-y-6">

            {/* Knowledge Base — real documents from backend */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-mono font-bold tracking-wider text-slate-400 uppercase flex items-center space-x-1.5">
                  <Layers className="w-3.5 h-3.5 text-cyan-400" />
                  <span>LOCAL VECTOR REPO</span>
                </span>
                <span className="text-[10px] bg-cyan-500/10 text-cyan-400 px-2 py-0.5 rounded border border-cyan-500/20 font-mono">
                  ChromaDB
                </span>
              </div>

              {/* Upload button */}
              <label className={`mb-2 flex items-center justify-center gap-2 px-3 py-2 rounded-lg border text-xs font-mono cursor-pointer transition-all ${isUploading ? 'border-slate-700 text-slate-500 cursor-wait' : 'border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10'}`}>
                <Paperclip className="w-3.5 h-3.5" />
                {isUploading ? 'Uploading…' : 'Upload PDF'}
                <input ref={fileInputRef} type="file" accept=".pdf" className="hidden" onChange={handleFileUpload} disabled={isUploading} />
              </label>
              {uploadError && <p className="text-[10px] text-red-400 font-mono mb-2">{uploadError}</p>}

              {/* Document list */}
              <div className="space-y-1.5">
                {documents.length === 0 ? (
                  <p className="text-[11px] text-slate-500 font-mono italic px-1">No documents ingested yet.</p>
                ) : documents.map((doc) => (
                  <div key={doc.id} className="group flex items-center justify-between p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.05] hover:border-cyan-500/30 hover:bg-white/[0.04] transition-all">
                    <div className="flex items-center space-x-2.5 truncate">
                      <div className="w-6 h-6 rounded bg-slate-800/80 flex items-center justify-center text-cyan-400 group-hover:bg-cyan-500/20">
                        <FileText className="w-3.5 h-3.5" />
                      </div>
                      <div className="truncate">
                        <span className="text-xs font-medium text-slate-300 block truncate">{doc.name}</span>
                        <span className="text-[10px] text-slate-500 font-mono">{doc.status}</span>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/40 px-1.5 py-0.5 rounded border border-cyan-800/40">
                      {doc.chunks} ch
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Model status — real health from backend */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-mono font-bold tracking-wider text-slate-400 uppercase">
                  ACTIVE MODEL
                </span>
                <span className={`text-[10px] font-mono font-semibold ${health?.ollama_status === 'available' ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {health ? (health.ollama_status === 'available' ? 'ONLINE' : 'OFFLINE') : '…'}
                </span>
              </div>
              <div className="space-y-2">
                <ModelStatusPill
                  name={health?.ollama_model || 'Ollama'}
                  role="Text & Knowledge Reasoning"
                  status={health?.ollama_status === 'available' ? 'ready' : 'error'}
                />
                <ModelStatusPill name="qwen2.5-coder:7b" role="Code Agent" status={health?.available_models?.includes('qwen2.5-coder:7b') ? 'ready' : 'error'} />
                <ModelStatusPill name="qwen3-vl:8b" role="Vision Agent" status={health?.available_models?.includes('qwen3-vl:8b') ? 'ready' : 'error'} />
              </div>
            </div>
          </div>

          {/* Backend info */}
          <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06] text-xs font-mono text-slate-400 flex items-center justify-between">
            <span className="text-slate-500 text-[10px]">BACKEND v{health?.version ?? '—'}</span>
            <span className={`text-[11px] font-semibold ${health?.status === 'ok' ? 'text-emerald-400' : 'text-amber-400'}`}>
              {health?.status === 'ok' ? 'OK' : 'UNREACHABLE'}
            </span>
          </div>
        </aside>

        {/* ── CENTER: Chat ── */}
        <section className="col-span-12 md:col-span-6 flex flex-col justify-between p-5 bg-gradient-to-b from-transparent to-[#05080E]/80 relative overflow-hidden">

          {/* Message stream */}
          <div className="flex-1 overflow-y-auto space-y-5 pr-2">
            {messages.map((msg) => (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                key={msg.id}
                className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                {/* Route badge */}
                {msg.route && (
                  <span className="inline-flex items-center space-x-1 text-[10px] font-mono text-cyan-300 bg-cyan-500/10 border border-cyan-500/30 px-2.5 py-0.5 rounded-full mb-1.5 shadow-sm shadow-cyan-500/10">
                    <Sparkles className="w-3 h-3 text-cyan-400" />
                    <span>Route: {msg.route}</span>
                  </span>
                )}

                {/* Bubble */}
                <div className={`p-4 rounded-2xl text-sm leading-relaxed max-w-xl ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-r from-cyan-600 to-cyan-500 text-black font-medium shadow-lg shadow-cyan-500/10'
                    : msg.error
                      ? 'glass-panel text-red-300 border-red-500/20'
                      : 'glass-panel text-slate-200 border-white/[0.08]'
                }`}>
                  <p>{msg.content}</p>

                  {/* Evidence button */}
                  {msg.evidence && msg.evidence.length > 0 && (
                    <button
                      onClick={() => {
                        setSelectedEvidence(msg.evidence![0]);
                        setIsDrawerOpen(true);
                      }}
                      className="mt-3 flex items-center space-x-2 px-3 py-1.5 bg-cyan-500/10 border border-cyan-500/30 hover:bg-cyan-500/20 text-cyan-300 rounded-lg text-xs font-mono transition-all"
                    >
                      <Eye className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Inspect {msg.evidence.length} grounded source{msg.evidence.length > 1 ? 's' : ''}</span>
                      <ChevronRight className="w-3.5 h-3.5 ml-auto text-cyan-400/60" />
                    </button>
                  )}

                  {/* Provenance */}
                  {msg.provenance && (
                    <div className="mt-3 pt-3 border-t border-white/[0.08] text-[10px] font-mono text-slate-500 space-y-0.5">
                      <div className="flex items-center gap-1">
                        {msg.provenance.status === 'insufficient'
                          ? <AlertTriangle className="w-3 h-3 text-amber-400" />
                          : <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
                        <span className="uppercase">{msg.provenance.status}</span>
                        <span className="mx-1">·</span>
                        <span>{msg.provenance.model}</span>
                        <span className="mx-1">·</span>
                        <span>{Math.round(msg.provenance.durationMs)}ms</span>
                      </div>
                      <div className="text-slate-600">req: {msg.provenance.requestId}</div>
                    </div>
                  )}
                </div>

                <span className="text-[10px] text-slate-500 mt-1.5 font-mono">{msg.timestamp}</span>
              </motion.div>
            ))}
            <div ref={messagesEndRef} />

            {/* Prompt suggestions (fresh session) */}
            {messages.length === 1 && (
              <div className="pt-4 space-y-2">
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
                  SUGGESTED QUERIES:
                </span>
                <div className="grid grid-cols-1 gap-2">
                  {SUGGESTED_PROMPTS.map((p, i) => (
                    <button
                      key={i}
                      onClick={() => executeQuery(p.query)}
                      className="p-3 text-left rounded-xl bg-white/[0.02] border border-white/[0.06] hover:border-cyan-500/40 hover:bg-cyan-500/[0.04] transition-all flex items-center justify-between group"
                    >
                      <div className="flex items-center space-x-3">
                        <span className="text-lg">{p.icon}</span>
                        <div>
                          <span className="text-xs font-semibold text-slate-200 block group-hover:text-cyan-300">{p.title}</span>
                          <span className="text-[11px] text-slate-400 line-clamp-1">{p.query}</span>
                        </div>
                      </div>
                      <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-cyan-400 group-hover:translate-x-0.5 transition-all" />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Input bar */}
          <div className="mt-4 pt-3 border-t border-white/[0.08]">
            <div className="mb-2 flex items-center gap-2 text-[10px] font-mono text-slate-400">
              <label className="cursor-pointer text-cyan-400 hover:text-cyan-300">
                <Paperclip className="inline w-3 h-3 mr-1" />
                {isUploadingVision ? 'Uploading image…' : 'Attach image'}
                <input ref={visionInputRef} type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={handleVisionUpload} disabled={isUploadingVision} />
              </label>
              {visionImagePath && <span className="text-emerald-400">Image ready</span>}
              {visionUploadError && <span className="text-red-400">{visionUploadError}</span>}
            </div>
            <div className="glass-panel-glow p-2 rounded-2xl flex items-center space-x-2">
              <input
                type="text"
                value={inputPrompt}
                disabled={isExecuting}
                onChange={(e) => setInputPrompt(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && executeQuery(inputPrompt)}
                placeholder={isExecuting ? 'Querying LangGraph + RAG pipeline…' : 'Ask a question about your uploaded documents…'}
                className="flex-1 bg-transparent px-2 py-1 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none font-sans"
              />
              <button
                disabled={isExecuting || !inputPrompt.trim()}
                onClick={() => executeQuery(inputPrompt)}
                className={`p-2.5 rounded-xl font-semibold flex items-center justify-center transition-all ${
                  isExecuting || !inputPrompt.trim()
                    ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                    : 'bg-gradient-to-r from-cyan-500 to-emerald-400 text-black shadow-md shadow-cyan-500/20 hover:scale-105 active:scale-95'
                }`}
              >
                {isExecuting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </div>
          </div>
        </section>

        {/* ── RIGHT SIDEBAR: Telemetry + Evidence ── */}
        <aside className="col-span-12 md:col-span-3 border-l border-white/[0.08] bg-[#090D16]/90 p-4 space-y-4 overflow-y-auto">

          {/* Sovereignty telemetry — clarified as UI visualisation only */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-mono font-bold tracking-wider text-slate-400 uppercase">
                EGRESS MONITOR
              </span>
              <span className="text-[10px] text-cyan-400 font-mono">UI ONLY</span>
            </div>
            <ZeroEgressGraph />
            <p className="text-[10px] text-slate-600 font-mono mt-1">Network isolation not instrumented in this build.</p>
          </div>

          {/* Live evidence panel */}
          <div>
            <span className="text-[11px] font-mono font-bold tracking-wider text-slate-400 uppercase block mb-2">
              GROUNDED EVIDENCE
            </span>
            {selectedEvidence ? (
              <div
                onClick={() => setIsDrawerOpen(true)}
                className="glass-panel p-3.5 rounded-xl hover:border-cyan-500/40 cursor-pointer space-y-2 transition-all group"
              >
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span className="text-cyan-300 font-semibold group-hover:text-cyan-400 truncate max-w-[150px]">
                    {selectedEvidence.source}
                  </span>
                  <span className="text-emerald-400 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                    {(selectedEvidence.score * 100).toFixed(1)}% Match
                  </span>
                </div>
                <p className="text-slate-300 text-xs leading-relaxed border-l-2 border-cyan-400 pl-2 line-clamp-3">
                  &ldquo;{selectedEvidence.text}&rdquo;
                </p>
                <span className="text-[10px] text-cyan-400 underline font-mono block pt-1">
                  Click to inspect full chunk context →
                </span>
              </div>
            ) : (
              <div className="glass-panel p-3.5 rounded-xl space-y-1">
                <p className="text-[11px] text-slate-500 font-mono italic">No evidence selected.</p>
                <p className="text-[10px] text-slate-600 font-mono">Send a query to retrieve grounded sources.</p>
              </div>
            )}
          </div>

          {/* Structured execution output is shown in the assistant response. */}
          <div>
            <span className="text-[11px] font-mono font-bold tracking-wider text-slate-400 uppercase block mb-2">
              DOCKER SANDBOX REPL
            </span>
            <div className="bg-black/90 p-3 rounded-xl border border-white/[0.08] font-mono text-xs text-slate-500 text-center py-6">
              Run a coding request in Chat to see backend sandbox output here.
            </div>
          </div>
        </aside>
      </div>

      {/* Evidence drawer */}
      <EvidenceDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        evidence={selectedEvidence}
      />
    </>
  );
}