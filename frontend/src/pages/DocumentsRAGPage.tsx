import React, { useState, useEffect } from 'react';
import {
  FileText,
  UploadCloud,
  Search,
  Bot,
  Sparkles,
  Layers,
  CheckCircle2,
  AlertCircle,
  FileCheck,
} from 'lucide-react';
import { aiService } from '../services/ai.service';
import { DocumentRecord, DocumentQueryResponse } from '../types';
import { formatDate } from '../utils/formatters';
import { useToast } from '../context/ToastContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Skeleton } from '../components/ui/Skeleton';

export const DocumentsRAGPage: React.FC = () => {
  const { showToast } = useToast();

  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);
  const [isUploading, setIsUploading] = useState(false);

  const [searchQuery, setSearchQuery] = useState('');
  const [queryResult, setQueryResult] = useState<DocumentQueryResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  const fetchDocuments = async () => {
    setIsLoadingDocs(true);
    try {
      const list = await aiService.getDocuments();
      setDocuments(list);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setIsLoadingDocs(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      await aiService.uploadDocument(file);
      showToast('success', 'Document Ingested', `Parsed and generated embeddings for ${file.name}.`);
      fetchDocuments();
    } catch (err: any) {
      showToast('error', 'Upload Error', err.response?.data?.detail || 'Failed to upload document');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const handleRunQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim() || isSearching) return;

    setIsSearching(true);
    try {
      const res = await aiService.queryDocuments(searchQuery);
      setQueryResult(res);
    } catch (err) {
      showToast('error', 'Query Error', 'Failed to perform vector RAG search.');
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Vector RAG Financial Document Intelligence
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Semantic search and conversational grounding over vendor contracts, SLAs, invoices, and company expense policies
          </p>
        </div>

        {/* Upload Button */}
        <div>
          <label className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold cursor-pointer shadow-md transition-all">
            <UploadCloud className="w-4 h-4" />
            {isUploading ? 'Ingesting Document...' : 'Upload Contract / Policy'}
            <input
              type="file"
              accept=".txt,.csv,.json,.pdf,.md"
              onChange={handleFileUpload}
              disabled={isUploading}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Main RAG Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Document Ingestion Library */}
        <Card className="border-slate-800 p-5 space-y-4 bg-slate-900/60">
          <CardHeader className="p-0 pb-3 border-b border-slate-800">
            <CardTitle className="text-base font-bold text-slate-100 flex items-center gap-2">
              <FileText className="w-4 h-4 text-cyan-400" />
              Indexed Documents ({documents.length})
            </CardTitle>
            <CardDescription>Knowledge base available for RAG grounding</CardDescription>
          </CardHeader>

          <div className="space-y-2.5 max-h-96 overflow-y-auto">
            {isLoadingDocs ? (
              [...Array(3)].map((_, i) => <Skeleton key={i} className="h-14 rounded-xl" />)
            ) : documents.length === 0 ? (
              <div className="p-6 text-center text-slate-400 text-xs">
                No documents uploaded yet. Upload contract terms or company policies above.
              </div>
            ) : (
              documents.map((doc) => (
                <div
                  key={doc.id}
                  className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between text-xs"
                >
                  <div className="space-y-0.5 max-w-[180px]">
                    <div className="font-semibold text-slate-200 truncate">{doc.filename}</div>
                    <div className="text-[10px] text-slate-400">
                      {(doc.file_size_bytes / 1024).toFixed(1)} KB • {formatDate(doc.uploaded_at)}
                    </div>
                  </div>
                  <Badge variant="success">INDEXED</Badge>
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Vector Semantic Search & Q&A Studio */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="border-slate-800 p-6 space-y-5 bg-slate-900/60">
            <div>
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                Ask Your Financial Knowledge Base
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Enter queries like "What is the penalty for AWS early termination?", "What are our SaaS reimbursement rules?", or "What is our discount tier?"
              </p>
            </div>

            <form onSubmit={handleRunQuery} className="flex gap-2">
              <Input
                placeholder="Ask questions about your uploaded agreements, policies, or statements..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="text-xs bg-slate-950 border-slate-800"
              />
              <Button
                variant="primary"
                size="sm"
                type="submit"
                isLoading={isSearching}
                disabled={!searchQuery.trim()}
                leftIcon={<Search className="w-4 h-4" />}
              >
                Search
              </Button>
            </form>

            {/* Answer Display */}
            {queryResult && (
              <div className="space-y-4 pt-4 border-t border-slate-800">
                <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-500/30 text-xs space-y-2">
                  <div className="flex items-center gap-1.5 text-indigo-300 font-bold uppercase tracking-wider text-[10px]">
                    <Bot className="w-3.5 h-3.5 text-indigo-400" /> Grounded Contract Intelligence
                  </div>
                  <p className="text-slate-200 leading-relaxed whitespace-pre-wrap">{queryResult.answer}</p>
                </div>

                {/* Retrieved Vector Chunks */}
                <div className="space-y-2.5">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Retrieved Document Source Evidence ({queryResult.retrieved_chunks.length})
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {queryResult.retrieved_chunks.map((chunk, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1.5 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-200 text-[11px] truncate max-w-[150px]">
                            {chunk.filename}
                          </span>
                          <span className="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-1.5 py-0.5 rounded border border-cyan-500/20">
                            Sim: {(chunk.similarity_score * 100).toFixed(1)}%
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-300 leading-snug line-clamp-4 bg-slate-900/80 p-2 rounded border border-slate-800/60 font-mono">
                          "{chunk.chunk_text}"
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
