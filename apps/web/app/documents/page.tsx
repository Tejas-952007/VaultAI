"use client";
import { useState, useEffect, useRef } from "react";
import { Upload, Search, Database, FileText, CheckCircle2, RefreshCw, AlertTriangle } from "lucide-react";
import { VaultAPI, DocumentMeta } from "@/lib/api";

export default function DocumentHub() {
  const [documents, setDocuments] = useState<DocumentMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const docs = await VaultAPI.listDocuments();
      setDocuments(docs);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load documents.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDocuments(); }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadError("Only PDF files are supported.");
      return;
    }
    setUploadError(null);
    setIsUploading(true);
    try {
      const doc = await VaultAPI.uploadDocument(file);
      setDocuments(prev => {
        const without = prev.filter(d => d.id !== doc.id);
        return [...without, doc];
      });
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const filtered = documents.filter(d =>
    d.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalChunks = documents.reduce((sum, d) => sum + d.chunks_count, 0);

  return (
    <div className="p-8 h-full overflow-y-auto space-y-8 bg-transparent">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-black text-slate-100 tracking-tighter uppercase">Knowledge Base</h1>
          <p className="text-slate-500 text-sm mt-1">ChromaDB Vector Store · {documents.length} document{documents.length !== 1 ? "s" : ""} indexed</p>
        </div>
        <div className="flex gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
            <input
              className="bg-navy/50 border border-slate-800 rounded-lg pl-10 pr-4 py-2 text-sm w-64 focus:border-cyan-500/50 focus:outline-none transition text-slate-300 placeholder:text-slate-600"
              placeholder="Filter documents…"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Upload button */}
          <label className={`flex items-center gap-2 px-6 py-2 rounded-lg text-xs font-bold transition cursor-pointer ${isUploading ? "bg-slate-700 text-slate-400 cursor-wait" : "bg-emerald-600 hover:bg-emerald-500 text-white"}`}>
            {isUploading ? <RefreshCw size={14} className="animate-spin" /> : <Upload size={14} />}
            {isUploading ? "Uploading…" : "Upload PDF"}
            <input ref={fileInputRef} type="file" accept=".pdf" className="hidden" onChange={handleUpload} disabled={isUploading} />
          </label>

          <button onClick={fetchDocuments} className="p-2 rounded-lg border border-slate-700 text-slate-400 hover:text-cyan-400 hover:border-cyan-500/50 transition" title="Refresh">
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {uploadError && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-mono">
          <AlertTriangle size={16} />
          {uploadError}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Document table */}
        <div className="lg:col-span-3">
          <div className="bg-navy/80 border border-slate-700 rounded-xl overflow-hidden backdrop-blur-md">
            <table className="w-full text-left text-[11px] font-medium">
              <thead>
                <tr className="bg-obsidian/50 text-slate-500 uppercase tracking-widest border-b border-slate-700">
                  <th className="px-6 py-4">Document</th>
                  <th className="px-6 py-4 text-center">Chunks</th>
                  <th className="px-6 py-4">Embedding Model</th>
                  <th className="px-6 py-4">Ingested</th>
                  <th className="px-6 py-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {loading && (
                  <tr>
                    <td colSpan={5} className="px-6 py-10 text-center text-slate-500 font-mono">
                      <RefreshCw size={20} className="animate-spin inline mr-2" />
                      Loading documents…
                    </td>
                  </tr>
                )}
                {!loading && error && (
                  <tr>
                    <td colSpan={5} className="px-6 py-10 text-center text-red-400 font-mono">
                      <AlertTriangle size={16} className="inline mr-2" />
                      {error}
                    </td>
                  </tr>
                )}
                {!loading && !error && filtered.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-6 py-10 text-center text-slate-600 font-mono italic">
                      {searchQuery ? "No matching documents." : "No documents available."}
                    </td>
                  </tr>
                )}
                {!loading && !error && filtered.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-700/20 transition group">
                    <td className="px-6 py-4 flex items-center gap-3">
                      <div className="p-2 bg-slate-800 rounded text-cyan-500"><FileText size={16} /></div>
                      <div>
                        <p className="text-slate-200 font-bold">{doc.filename}</p>
                        <p className="text-[9px] text-slate-500 uppercase font-mono">SHA-256: {doc.sha256.slice(0, 12)}…</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center text-slate-400 font-mono">{doc.chunks_count}</td>
                    <td className="px-6 py-4 text-slate-500 font-mono italic">all-MiniLM-L6-v2</td>
                    <td className="px-6 py-4 text-slate-500 font-mono text-[10px]">
                      {new Date(doc.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-[9px] font-black uppercase flex items-center gap-1 w-fit ${
                        doc.status === "indexed" ? "bg-emerald-500/10 text-emerald-500" : "bg-amber-500/10 text-amber-500 animate-pulse"
                      }`}>
                        {doc.status === "indexed" && <CheckCircle2 size={10} />}
                        {doc.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Stats panel */}
        <div className="space-y-6">
          <div className="bg-navy/80 border border-slate-700 rounded-xl p-6">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
              <Database size={16} className="text-cyan-500" /> Chroma Statistics
            </h3>
            <div className="space-y-6">
              <div>
                <p className="text-[10px] text-slate-500 uppercase font-bold">Documents</p>
                <p className="text-2xl font-black text-slate-100 font-mono">{documents.length}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 uppercase font-bold">Total Chunks</p>
                <p className="text-2xl font-black text-emerald-500 font-mono">{totalChunks.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 uppercase font-bold">Embedding Dim</p>
                <p className="text-2xl font-black text-cyan-500 font-mono">384</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 uppercase font-bold">Disk / Retrieval</p>
                <p className="text-xs font-mono text-slate-600 italic">N/A — not instrumented</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}