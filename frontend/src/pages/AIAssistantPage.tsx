import React, { useState, useRef, useEffect } from 'react';
import {
  Bot,
  Send,
  Sparkles,
  Zap,
  Layers,
  AlertTriangle,
  CheckCircle2,
  TrendingDown,
  ArrowRight,
  ShieldCheck,
  FileText,
  Clock,
  Cpu,
} from 'lucide-react';
import { aiService } from '../services/ai.service';
import { ChatResponse, CitationItem } from '../types';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  agentsInvolved?: string[];
  toolsExecuted?: string[];
  evidenceCards?: Array<{
    title: string;
    value: string;
    detail: string;
    type: 'savings' | 'warning' | 'anomaly' | 'forecast';
  }>;
  suggestedActions?: Array<{
    action: string;
    label: string;
    savings?: number;
    severity?: string;
  }>;
  citations?: CitationItem[];
}

export const AIAssistantPage: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: `Hello **${user?.name || 'there'}**! I am your **Money Analysis Multi-Agent Financial Controller**.\n\nI continuously monitor your live enterprise ledgers, department burn rates, SaaS seat utilization, and supplier contracts using specialized autonomous agents.\n\nAsk me anything or select a prompt below to run live multi-agent financial analytics:`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const samplePrompts = [
    'How can we save $50,000 next quarter?',
    'Which transactions look abnormal or high-risk?',
    'Forecast our operating expenses for the next 90 days.',
    'Find unnecessary SaaS licenses and wasted seats.',
    'Which department is burning budget fastest?',
    'What if we decrease marketing spending by 15%?',
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = textToSend || inputPrompt.trim();
    if (!query || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputPrompt('');
    setIsLoading(true);

    try {
      const res: ChatResponse = await aiService.sendMessage(query);
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: res.message,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        agentsInvolved: res.agents_involved,
        toolsExecuted: res.tools_executed,
        evidenceCards: res.evidence_cards,
        suggestedActions: res.suggested_actions,
        citations: res.citations,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error('Chat error:', err);
      showToast('error', 'Copilot Error', err.response?.data?.detail || 'Failed to reach AI Controller');
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: '⚠️ I encountered an error coordinating the multi-agent analysis. Please try again.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleActionTrigger = async (action: any) => {
    try {
      await aiService.createApproval({
        request_type: action.action,
        title: `Approval: ${action.label}`,
        details: `Automated optimization action triggered via Money Analysis AI Copilot conversation.`,
        impact_savings_monthly: action.savings || 0,
        risk_level: 'LOW',
      });
      showToast('success', 'Approval Request Submitted', 'Action routed to Human-in-the-Loop governance queue.');
    } catch (err) {
      showToast('error', 'Error', 'Failed to submit approval request.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            Money Analysis AI Financial Controller
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-semibold flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              12 Multi-Agents Active
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Autonomous LangGraph supervisor routing queries across Isolation Forest, ML Forecasting, SaaS optimization, and What-If simulation engines
          </p>
        </div>
      </div>

      {/* Main Chat Workspace */}
      <Card className="border-slate-800 flex flex-col h-[650px] shadow-2xl bg-slate-950/60 backdrop-blur-xl">
        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6 text-xs">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex items-start gap-3.5 ${
                m.role === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 border ${
                  m.role === 'user'
                    ? 'bg-indigo-600/30 text-indigo-300 border-indigo-500/40'
                    : 'bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 text-cyan-300 border-cyan-500/30'
                }`}
              >
                {m.role === 'user' ? (
                  <span className="font-bold text-xs">{user?.name.charAt(0)}</span>
                ) : (
                  <Bot className="w-4 h-4" />
                )}
              </div>

              {/* Message Content Bubble */}
              <div
                className={`max-w-2xl p-4 rounded-2xl space-y-3.5 leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-indigo-600/20 text-slate-100 border border-indigo-500/30 rounded-tr-none'
                    : 'bg-slate-900/90 text-slate-200 border border-slate-800/90 rounded-tl-none shadow-lg'
                }`}
              >
                {/* Agent & Tool Execution Pills */}
                {m.agentsInvolved && m.agentsInvolved.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 pb-2 border-b border-slate-800/80">
                    <span className="text-[10px] text-slate-400 font-semibold uppercase flex items-center gap-1">
                      <Cpu className="w-3 h-3 text-indigo-400" /> Agents:
                    </span>
                    {m.agentsInvolved.map((agent) => (
                      <span
                        key={agent}
                        className="text-[10px] px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-mono"
                      >
                        {agent}
                      </span>
                    ))}
                  </div>
                )}

                {/* Markdown text rendered */}
                <div className="whitespace-pre-wrap space-y-2 text-slate-200">
                  {m.content}
                </div>

                {/* Evidence Cards */}
                {m.evidenceCards && m.evidenceCards.length > 0 && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2">
                    {m.evidenceCards.map((card, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 flex items-start justify-between gap-2"
                      >
                        <div>
                          <div className="text-[10px] text-slate-400 font-semibold">{card.title}</div>
                          <div className="font-bold text-slate-100 text-sm mt-0.5">{card.value}</div>
                          <div className="text-[10px] text-slate-400 mt-0.5 leading-snug">{card.detail}</div>
                        </div>
                        <span className="p-1 rounded bg-indigo-500/10 text-indigo-400 shrink-0">
                          <Zap className="w-3.5 h-3.5" />
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Suggested Action Buttons */}
                {m.suggestedActions && m.suggestedActions.length > 0 && (
                  <div className="pt-2 border-t border-slate-800/80 space-y-2">
                    <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3 text-emerald-400" /> Suggested Optimization Actions (HITL Protected):
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {m.suggestedActions.map((act, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleActionTrigger(act)}
                          className="px-3 py-1.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[11px] font-semibold transition-all flex items-center gap-1.5 shadow-sm"
                        >
                          <Zap className="w-3 h-3 text-emerald-400" />
                          {act.label}
                          <ArrowRight className="w-3 h-3" />
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Citations */}
                {m.citations && m.citations.length > 0 && (
                  <div className="pt-2 border-t border-slate-800/60 text-[10px] text-slate-400 flex flex-wrap gap-3">
                    {m.citations.map((c, i) => (
                      <span key={i} className="flex items-center gap-1">
                        <FileText className="w-3 h-3 text-cyan-400" />
                        <strong>{c.source}</strong> ({c.detail})
                      </span>
                    ))}
                  </div>
                )}

                <div className="text-[9px] text-slate-400/80 text-right">{m.timestamp}</div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex items-start gap-3.5">
              <div className="w-8 h-8 rounded-xl bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 animate-spin" />
              </div>
              <div className="p-4 rounded-2xl rounded-tl-none bg-slate-900/80 border border-slate-800 text-slate-300 space-y-2">
                <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400">
                  <Sparkles className="w-3.5 h-3.5 animate-pulse" />
                  LangGraph Supervisor coordinating agents...
                </div>
                <div className="text-[11px] text-slate-400">
                  Analyzing ledgers, running Isolation Forest scans, and computing deterministic optimization metrics.
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Dynamic Prompt Suggestions */}
        <div className="px-4 py-2.5 border-t border-slate-800/80 bg-slate-950/40 flex items-center gap-2 overflow-x-auto">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider shrink-0 flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-indigo-400" /> Prompts:
          </span>
          {samplePrompts.map((promptText) => (
            <button
              key={promptText}
              onClick={() => handleSendMessage(promptText)}
              className="text-[11px] px-3 py-1 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 whitespace-nowrap transition-colors"
            >
              {promptText}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800 bg-slate-950 flex items-center gap-3">
          <Input
            placeholder="Ask anything about budgets, SaaS waste, anomalies, vendor SLAs, or target savings..."
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            className="text-xs bg-slate-900 border-slate-800 focus:border-indigo-500"
          />
          <Button
            variant="primary"
            size="sm"
            onClick={() => handleSendMessage()}
            isLoading={isLoading}
            disabled={!inputPrompt.trim() || isLoading}
            leftIcon={<Send className="w-4 h-4" />}
          >
            Send
          </Button>
        </div>
      </Card>
    </div>
  );
};
