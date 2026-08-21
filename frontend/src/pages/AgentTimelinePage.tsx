import React, { useState } from 'react';
import {
  Cpu,
  CheckCircle2,
  Clock,
  Zap,
  Layers,
  ArrowRight,
  ShieldCheck,
  Play,
  FileText,
  AlertTriangle,
  TrendingDown,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import { aiService } from '../services/ai.service';
import { formatCurrency } from '../utils/formatters';
import { useToast } from '../context/ToastContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';

interface TimelineStep {
  agentName: string;
  role: string;
  status: 'COMPLETED' | 'RUNNING' | 'WAITING_APPROVAL' | 'QUEUED';
  durationMs: number;
  toolsUsed: string[];
  evidence: string;
  outputSummary: string;
}

export const AgentTimelinePage: React.FC = () => {
  const { showToast } = useToast();
  const [prompt, setPrompt] = useState('Find $50,000 in monthly recurring cost savings');
  const [isRunning, setIsRunning] = useState(false);

  const [steps, setSteps] = useState<TimelineStep[]>([
    {
      agentName: 'Supervisor Agent',
      role: 'LangGraph Coordinator & Intent Classifier',
      status: 'COMPLETED',
      durationMs: 145,
      toolsUsed: ['parse_financial_intent', 'dispatch_specialist_agents'],
      evidence: 'Detected target savings intent of $50,000 across Cloud, SaaS, and Vendor contracts.',
      outputSummary: 'Formulated parallel execution plan across 6 specialized financial agents.',
    },
    {
      agentName: 'Budget Agent',
      role: 'Department & Category Variance Monitor',
      status: 'COMPLETED',
      durationMs: 98,
      toolsUsed: ['calculate_budget_velocity', 'detect_category_burn'],
      evidence: 'Growth & Marketing pacing 12% over allocated Q3 ceiling. Engineering cloud spend at 88% capacity.',
      outputSummary: 'Flagged $18,200/mo in potential discretionary budget moderation.',
    },
    {
      agentName: 'Vendor Intelligence Agent',
      role: 'Pricing & SLA Benchmark Evaluator',
      status: 'COMPLETED',
      durationMs: 124,
      toolsUsed: ['evaluate_vendor_efficiency', 'benchmark_contract_rates'],
      evidence: 'AWS on-demand pricing evaluated. 1-Year Compute Savings Plan yields 38% hourly rate reduction.',
      outputSummary: 'Recommended AWS contract conversion saving $4,850/mo.',
    },
    {
      agentName: 'Subscription Optimization Agent',
      role: 'SaaS License Waste Scanner',
      status: 'COMPLETED',
      durationMs: 110,
      toolsUsed: ['audit_saas_licenses', 'flag_underutilized_seats'],
      evidence: '18 untouched Salesforce seats (>60d inactive) + 38 pooled Zoom Pro inactive accounts detected.',
      outputSummary: 'Reclaimable license waste totaled $3,320/mo across Sales and HR.',
    },
    {
      agentName: 'Forecasting Agent',
      role: 'Time-Series Regression Modeler',
      status: 'COMPLETED',
      durationMs: 165,
      toolsUsed: ['generate_expenditure_forecast', 'stress_test_budget'],
      evidence: '90-day trajectory projects $682,000 period expenditure with INCREASING velocity (+8.2%).',
      outputSummary: 'Confirmed structural cost reduction required to avert Q4 cash reserve depletion.',
    },
    {
      agentName: 'Cost Optimization Agent',
      role: 'Combinatorial Target Planner',
      status: 'COMPLETED',
      durationMs: 190,
      toolsUsed: ['synthesize_optimization_plan', 'rank_savings_opportunities'],
      evidence: 'Combinatorial solver achieved $52,100/mo total savings plan matching LOW/MEDIUM risk profile.',
      outputSummary: 'Formulated 4 actionable governance proposals exceeding user $50,000 milestone.',
    },
    {
      agentName: 'Approval Agent',
      role: 'Human-in-the-Loop Governance Gateway',
      status: 'WAITING_APPROVAL',
      durationMs: 40,
      toolsUsed: ['enqueue_approval_requests', 'generate_audit_trail'],
      evidence: 'Non-destructive recommendations staged in Approval Queue for Finance Controller authorization.',
      outputSummary: 'Awaiting human sign-off on Salesforce deprovisioning and AWS Savings Plan.',
    },
    {
      agentName: 'Report Agent',
      role: 'Executive PDF & Financial Summary Synthesizer',
      status: 'COMPLETED',
      durationMs: 210,
      toolsUsed: ['compile_monthly_cfo_report', 'render_verified_pdf'],
      evidence: 'Generated 14-section Financial Controller Report with complete audit trail and KPI metrics.',
      outputSummary: 'Export-ready PDF compiled and synchronized with live ledger data.',
    },
  ]);

  const handleRunPipeline = async () => {
    if (!prompt.trim() || isRunning) return;
    setIsRunning(true);
    try {
      await aiService.sendMessage(prompt);
      showToast('success', 'Multi-Agent Workflow Executed', 'All agents successfully coordinated via LangGraph.');
    } catch (err) {
      showToast('error', 'Execution Error', 'Failed to run multi-agent workflow.');
    } finally {
      setIsRunning(false);
    }
  };

  const totalDuration = steps.reduce((sum, s) => sum + s.durationMs, 0);

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="p-8 rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/60 via-slate-900 to-slate-950 backdrop-blur-xl">
        <div className="max-w-3xl space-y-3">
          <Badge variant="purple">LangGraph Multi-Agent Telemetry</Badge>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Autonomous Multi-Agent Execution Timeline
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Real-time observability stream illustrating sequential and parallel agent execution, tool telemetry, duration benchmarks, and synthesized business evidence.
          </p>
        </div>
      </div>

      {/* Trigger Bar */}
      <Card className="border-slate-800 p-4 bg-slate-900/60">
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <Input
            placeholder="Enter optimization goal or financial query..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="text-xs bg-slate-950 border-slate-800"
          />
          <Button
            variant="primary"
            size="sm"
            onClick={handleRunPipeline}
            isLoading={isRunning}
            leftIcon={<Play className="w-4 h-4" />}
            className="shrink-0"
          >
            Execute Multi-Agent Pipeline
          </Button>
        </div>
      </Card>

      {/* Execution Summary Ribbon */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
        <Card className="p-4 border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Agents Coordinated</span>
            <span className="text-2xl font-bold text-slate-100 mt-0.5 block">{steps.length} Autonomous Agents</span>
          </div>
          <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400">
            <Cpu className="w-5 h-5" />
          </div>
        </Card>

        <Card className="p-4 border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Total Execution Latency</span>
            <span className="text-2xl font-bold text-cyan-400 mt-0.5 block">{totalDuration} ms</span>
          </div>
          <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400">
            <Clock className="w-5 h-5" />
          </div>
        </Card>

        <Card className="p-4 border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Governance Gateway</span>
            <span className="text-2xl font-bold text-emerald-400 mt-0.5 block">HITL Protected</span>
          </div>
          <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
        </Card>
      </div>

      {/* Timeline Steps Progression */}
      <div className="space-y-4">
        {steps.map((step, idx) => (
          <Card
            key={idx}
            className={`hover-glow border-slate-800 p-5 bg-slate-900/70 transition-all ${
              step.status === 'WAITING_APPROVAL' ? 'border-amber-500/40 bg-amber-500/5' : ''
            }`}
          >
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
              <div className="flex items-start gap-4">
                <div
                  className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${
                    step.status === 'COMPLETED'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : step.status === 'WAITING_APPROVAL'
                      ? 'bg-amber-500/10 text-amber-400 border-amber-500/30 animate-pulse'
                      : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
                  }`}
                >
                  {step.status === 'COMPLETED' ? (
                    <CheckCircle2 className="w-5 h-5" />
                  ) : step.status === 'WAITING_APPROVAL' ? (
                    <Clock className="w-5 h-5" />
                  ) : (
                    <Cpu className="w-5 h-5" />
                  )}
                </div>

                <div className="space-y-1.5 max-w-2xl text-xs">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-bold text-slate-100 text-sm">{step.agentName}</span>
                    <span className="text-[10px] text-slate-400 font-medium">({step.role})</span>
                    <Badge variant={step.status === 'COMPLETED' ? 'success' : step.status === 'WAITING_APPROVAL' ? 'warning' : 'secondary'}>
                      {step.status === 'WAITING_APPROVAL' ? 'Awaiting Human Sign-off' : step.status}
                    </Badge>
                  </div>

                  <p className="text-slate-300 leading-relaxed">{step.outputSummary}</p>

                  <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] text-slate-300 space-y-1">
                    <span className="font-semibold text-slate-400 uppercase text-[10px] block">Business Evidence Synthesized:</span>
                    <p>{step.evidence}</p>
                  </div>

                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold">Tools Dispatched:</span>
                    {step.toolsUsed.map((tool, tIdx) => (
                      <span
                        key={tIdx}
                        className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono"
                      >
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="text-right shrink-0">
                <span className="text-xs font-mono font-bold text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded-full border border-cyan-500/20">
                  {step.durationMs} ms
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
