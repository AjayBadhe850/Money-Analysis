import React, { useState, useEffect } from 'react';
import {
  Zap,
  Sparkles,
  Sliders,
  TrendingDown,
  ShieldAlert,
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
  PieChart,
  Percent,
  Play,
  RotateCcw,
} from 'lucide-react';
import { aiService } from '../services/ai.service';
import {
  SavingsOpportunitiesResponse,
  SavingsOpportunityItem,
  CostOptimizationPlanResponse,
  WhatIfResponse,
} from '../types';
import { formatCurrency, formatPercent } from '../utils/formatters';
import { useToast } from '../context/ToastContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Skeleton } from '../components/ui/Skeleton';

export const OptimizationPage: React.FC = () => {
  const { showToast } = useToast();

  const [opportunitiesData, setOpportunitiesData] = useState<SavingsOpportunitiesResponse | null>(null);
  const [optimizationPlan, setOptimizationPlan] = useState<CostOptimizationPlanResponse | null>(null);
  const [whatIfResult, setWhatIfResult] = useState<WhatIfResponse | null>(null);

  const [isLoadingOpps, setIsLoadingOpps] = useState(true);
  const [isPlanning, setIsPlanning] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);

  // Target Planner inputs
  const [targetAmount, setTargetAmount] = useState('50000');
  const [timeframeMonths, setTimeframeMonths] = useState('3');
  const [riskTolerance, setRiskTolerance] = useState('MEDIUM');

  // What-If inputs
  const [engAdj, setEngAdj] = useState('-15');
  const [mktgAdj, setMktgAdj] = useState('-10');
  const [awsAdj, setAwsAdj] = useState('0');
  const [licenseCut, setLicenseCut] = useState('20');
  const [revGrowth, setRevGrowth] = useState('5');

  const fetchOpportunities = async () => {
    setIsLoadingOpps(true);
    try {
      const data = await aiService.getRecommendations();
      setOpportunitiesData(data);
    } catch (err) {
      console.error('Failed to load opportunities:', err);
    } finally {
      setIsLoadingOpps(false);
    }
  };

  useEffect(() => {
    fetchOpportunities();
    handleRunWhatIf();
  }, []);

  const handleGeneratePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsPlanning(true);
    try {
      const plan = await aiService.generateOptimizationPlan(
        Number(targetAmount),
        Number(timeframeMonths),
        riskTolerance
      );
      setOptimizationPlan(plan);
      showToast('success', 'Optimization Plan Ready', `Synthesized ${plan.recommended_actions.length} strategic actions.`);
    } catch (err) {
      showToast('error', 'Planning Error', 'Could not generate optimization plan.');
    } finally {
      setIsPlanning(false);
    }
  };

  const handleRunWhatIf = async () => {
    setIsSimulating(true);
    try {
      const res = await aiService.simulateWhatIf({
        department_spend_adjustments: {
          Engineering: Number(engAdj) / 100,
          Marketing: Number(mktgAdj) / 100,
        },
        vendor_price_adjustments: {
          'Amazon Web Services': Number(awsAdj) / 100,
        },
        license_utilization_threshold_cut: Number(licenseCut) / 100,
        revenue_growth_adjustment: Number(revGrowth) / 100,
      });
      setWhatIfResult(res);
    } catch (err) {
      console.error('What-if error:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleCreateApproval = async (action: any) => {
    try {
      await aiService.createApproval({
        request_type: action.action_type || 'BUDGET_MODERATION',
        title: `Approval: ${action.title}`,
        details: `${action.rationale} (Projected Monthly Savings: ${formatCurrency(action.projected_monthly_savings)})`,
        impact_savings_monthly: action.projected_monthly_savings,
        risk_level: action.risk_level || 'LOW',
        action_payload: action.approval_payload,
      });
      showToast('success', 'Approval Created', `Action "${action.title}" submitted to governance queue.`);
    } catch (err) {
      showToast('error', 'Error', 'Failed to create approval request.');
    }
  };

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="p-8 rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/50 via-slate-900 to-slate-950 backdrop-blur-xl relative overflow-hidden">
        <div className="max-w-3xl space-y-3 relative z-10">
          <Badge variant="purple">Autonomous Cost Intelligence</Badge>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            AI Cost Optimization & Strategic Planning Studio
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Run goal-seeking combinatorial cost reduction plans, explore deterministic What-If financial simulations, and route vetted actions directly to Human-in-the-Loop approval workflows.
          </p>
        </div>
      </div>

      {/* Target Savings Planner Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="border-slate-800 p-5 space-y-4 bg-slate-900/60">
          <CardHeader className="p-0 pb-3 border-b border-slate-800">
            <CardTitle className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              Goal-Seeking Target Planner
            </CardTitle>
            <CardDescription>
              Define your financial savings milestone and let the agent calculate the optimal combination
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleGeneratePlan} className="space-y-3.5 text-xs">
            <Input
              label="Target Savings ($)"
              type="number"
              value={targetAmount}
              onChange={(e) => setTargetAmount(e.target.value)}
              placeholder="e.g. 50000"
              required
            />

            <Select
              label="Execution Timeframe"
              value={timeframeMonths}
              onChange={(e) => setTimeframeMonths(e.target.value)}
              options={[
                { label: '1 Month (Immediate)', value: 1 },
                { label: '3 Months (Next Quarter)', value: 3 },
                { label: '6 Months (Half Year)', value: 6 },
                { label: '12 Months (Fiscal Year)', value: 12 },
              ]}
            />

            <Select
              label="Risk Tolerance"
              value={riskTolerance}
              onChange={(e) => setRiskTolerance(e.target.value)}
              options={[
                { label: 'LOW (Zero operational impact)', value: 'LOW' },
                { label: 'MEDIUM (Recommended standard)', value: 'MEDIUM' },
                { label: 'HIGH (Aggressive restructuring)', value: 'HIGH' },
              ]}
            />

            <Button
              variant="primary"
              size="sm"
              type="submit"
              isLoading={isPlanning}
              className="w-full mt-2"
              leftIcon={<Sparkles className="w-4 h-4" />}
            >
              Generate Combinatorial Plan
            </Button>
          </form>
        </Card>

        {/* Plan Results Area */}
        <div className="lg:col-span-2 space-y-4">
          {optimizationPlan ? (
            <Card className="border-slate-800 p-6 space-y-5 bg-slate-900/60">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <span className="text-[10px] uppercase font-bold text-indigo-400">Target Plan Summary</span>
                  <h3 className="text-lg font-bold text-slate-100">
                    Achievable: {formatCurrency(optimizationPlan.achievable_total_period_savings)} over {optimizationPlan.timeframe_months} mo
                  </h3>
                </div>
                <Badge variant={optimizationPlan.target_achieved ? 'success' : 'warning'}>
                  {optimizationPlan.target_achieved ? '100% Target Met' : 'Partial Feasibility'}
                </Badge>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3.5 rounded-xl border border-slate-800">
                {optimizationPlan.executive_summary}
              </p>

              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Recommended Action Steps ({optimizationPlan.recommended_actions.length})
                </h4>
                <div className="space-y-2.5">
                  {optimizationPlan.recommended_actions.map((act, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                    >
                      <div className="space-y-1 max-w-lg">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-100 text-xs">{act.title}</span>
                          <span className="text-[10px] font-semibold px-2 py-0.2 rounded bg-indigo-500/10 text-indigo-400">
                            {act.target_entity}
                          </span>
                          <span className="text-[10px] font-bold text-emerald-400">
                            +{formatCurrency(act.projected_monthly_savings)}/mo
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400">{act.rationale}</p>
                      </div>

                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleCreateApproval(act)}
                        leftIcon={<ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />}
                        className="shrink-0"
                      >
                        Submit Approval
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          ) : (
            <Card className="border-slate-800 p-8 text-center text-slate-400 space-y-3">
              <div className="p-3 rounded-2xl bg-slate-950 w-12 h-12 mx-auto flex items-center justify-center text-indigo-400 border border-slate-800">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-slate-200 text-sm">Strategic Planner Ready</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                Set a target savings goal on the left to synthesize multi-agent cost optimization proposals.
              </p>
            </Card>
          )}
        </div>
      </div>

      {/* Deterministic What-If Scenario Simulator */}
      <div className="space-y-4 pt-4 border-t border-slate-800">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Sliders className="w-5 h-5 text-cyan-400" />
              Deterministic What-If Financial Simulation Engine
            </h2>
            <p className="text-xs text-slate-400">
              Model hypothetical operational adjustments with live mathematical feedback on cash flow and operating margins
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Controls */}
          <Card className="border-slate-800 p-5 space-y-4 bg-slate-900/60 text-xs">
            <div className="font-bold text-slate-200 border-b border-slate-800 pb-2">Simulation Parameters</div>

            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Engineering Spend Shift</span>
                <span className="font-bold text-indigo-400">{engAdj}%</span>
              </div>
              <input
                type="range"
                min="-50"
                max="50"
                step="5"
                value={engAdj}
                onChange={(e) => setEngAdj(e.target.value)}
                className="w-full accent-indigo-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Marketing Spend Shift</span>
                <span className="font-bold text-indigo-400">{mktgAdj}%</span>
              </div>
              <input
                type="range"
                min="-50"
                max="50"
                step="5"
                value={mktgAdj}
                onChange={(e) => setMktgAdj(e.target.value)}
                className="w-full accent-indigo-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>AWS Cloud Price Shift</span>
                <span className="font-bold text-indigo-400">{awsAdj}%</span>
              </div>
              <input
                type="range"
                min="-30"
                max="50"
                step="5"
                value={awsAdj}
                onChange={(e) => setAwsAdj(e.target.value)}
                className="w-full accent-indigo-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Cancel SaaS Licenses with Utilization &lt;</span>
                <span className="font-bold text-amber-400">{licenseCut}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="60"
                step="10"
                value={licenseCut}
                onChange={(e) => setLicenseCut(e.target.value)}
                className="w-full accent-amber-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Revenue Growth Shift</span>
                <span className="font-bold text-emerald-400">+{revGrowth}%</span>
              </div>
              <input
                type="range"
                min="-20"
                max="50"
                step="5"
                value={revGrowth}
                onChange={(e) => setRevGrowth(e.target.value)}
                className="w-full accent-emerald-500"
              />
            </div>

            <Button
              variant="primary"
              size="sm"
              onClick={handleRunWhatIf}
              isLoading={isSimulating}
              className="w-full mt-2"
              leftIcon={<Play className="w-3.5 h-3.5" />}
            >
              Re-Calculate Simulation
            </Button>
          </Card>

          {/* Simulation Output Dashboard */}
          <div className="lg:col-span-2 space-y-4">
            {whatIfResult ? (
              <Card className="border-slate-800 p-6 space-y-5 bg-slate-900/60">
                {/* Metric Summary Ribbon */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                    <span className="text-slate-400 block text-[10px]">Simulated Monthly OPEX</span>
                    <span className="text-base font-bold text-slate-100 mt-0.5 block">
                      {formatCurrency(whatIfResult.simulated_monthly_expense)}
                    </span>
                    <span className="text-[10px] text-emerald-400">
                      Save {formatCurrency(whatIfResult.monthly_expense_savings)}/mo
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                    <span className="text-slate-400 block text-[10px]">Annual Cash Impact</span>
                    <span className="text-base font-bold text-emerald-400 mt-0.5 block">
                      {formatCurrency(whatIfResult.annual_expense_savings)}
                    </span>
                    <span className="text-[10px] text-slate-400">Recurring Annual</span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                    <span className="text-slate-400 block text-[10px]">Simulated Net Profit</span>
                    <span className="text-base font-bold text-slate-100 mt-0.5 block">
                      {formatCurrency(whatIfResult.simulated_net_profit)}
                    </span>
                    <span className="text-[10px] text-emerald-400">
                      vs {formatCurrency(whatIfResult.baseline_net_profit)}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                    <span className="text-slate-400 block text-[10px]">Operating Margin Shift</span>
                    <span className="text-base font-bold text-cyan-400 mt-0.5 block">
                      {whatIfResult.profit_margin_change_pct > 0 ? '+' : ''}{whatIfResult.profit_margin_change_pct}%
                    </span>
                    <span className="text-[10px] text-slate-400">Margin Expansion</span>
                  </div>
                </div>

                {/* Narrative */}
                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3.5 rounded-xl border border-slate-800">
                  {whatIfResult.ai_narrative}
                </p>

                {/* Impact Delta Table */}
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Detailed Variable Breakdown ({whatIfResult.detailed_impacts.length})
                  </h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs text-slate-300">
                      <thead className="bg-slate-950 text-[10px] font-semibold uppercase text-slate-400 border-b border-slate-800">
                        <tr>
                          <th className="px-3 py-2">Variable / Metric</th>
                          <th className="px-3 py-2 text-right">Baseline</th>
                          <th className="px-3 py-2 text-right">Simulated</th>
                          <th className="px-3 py-2 text-right">Delta ($)</th>
                          <th className="px-3 py-2 text-right">Delta (%)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {whatIfResult.detailed_impacts.map((item, idx) => (
                          <tr key={idx} className="hover:bg-slate-800/30">
                            <td className="px-3 py-2 font-medium text-slate-200">{item.metric}</td>
                            <td className="px-3 py-2 text-right text-slate-400">{formatCurrency(item.baseline_value)}</td>
                            <td className="px-3 py-2 text-right font-bold text-slate-100">{formatCurrency(item.simulated_value)}</td>
                            <td className={`px-3 py-2 text-right font-semibold ${item.delta_amount <= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                              {item.delta_amount > 0 ? '+' : ''}{formatCurrency(item.delta_amount)}
                            </td>
                            <td className={`px-3 py-2 text-right ${item.delta_percentage <= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                              {item.delta_percentage > 0 ? '+' : ''}{item.delta_percentage}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </Card>
            ) : (
              <Skeleton className="h-64 rounded-xl" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
