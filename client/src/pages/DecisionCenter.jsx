import { useState, useEffect } from 'react';
import {
  Sparkles,
  ArrowRightLeft,
  ShoppingCart,
  TrendingUp,
  Tag,
  Percent,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Clock,
  Layers,
  ChevronDown,
  ChevronUp,
  Brain,
  Sliders,
  DollarSign,
  ShieldCheck,
  Check,
  Play,
} from 'lucide-react';
import { decisionService } from '../services';

const ACTION_COLORS = {
  REPLENISH: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  TRANSFER_INVENTORY: 'bg-blue-50 text-blue-700 border-blue-200',
  INCREASE_ALLOCATION: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  MARKDOWN: 'bg-amber-50 text-amber-700 border-amber-200',
  ADJUST_PROMOTION: 'bg-purple-50 text-purple-700 border-purple-200',
  SUBSTITUTE_PRODUCT: 'bg-cyan-50 text-cyan-700 border-cyan-200',
  TAKE_NO_ACTION: 'bg-stone-50 text-stone-700 border-stone-200',
};

const ACTION_ICONS = {
  REPLENISH: ShoppingCart,
  TRANSFER_INVENTORY: ArrowRightLeft,
  INCREASE_ALLOCATION: TrendingUp,
  MARKDOWN: Tag,
  ADJUST_PROMOTION: Percent,
  SUBSTITUTE_PRODUCT: RefreshCw,
  TAKE_NO_ACTION: CheckCircle,
};

const URGENCY_COLORS = {
  CRITICAL: 'bg-rose-100 text-rose-800 border-rose-300',
  HIGH: 'bg-orange-100 text-orange-800 border-orange-300',
  MEDIUM: 'bg-amber-100 text-amber-800 border-amber-300',
  LOW: 'bg-stone-100 text-stone-600 border-stone-200',
};

function CleanRationale({ text }) {
  if (!text) return null;
  const clean = text
    .replace(/^\*\*Executive Rationale\*\*:?\s*/i, '')
    .replace(/^Executive Rationale:?\s*/i, '')
    .replace(/^\*\*Rationale\*\*:?\s*/i, '')
    .replace(/^Rationale:?\s*/i, '')
    .trim();

  return (
    <p className="text-xs text-stone-700 mt-2 leading-relaxed font-normal">
      {clean}
    </p>
  );
}

function formatActionPlan(action, params = {}) {
  switch (action) {
    case 'TRANSFER_INVENTORY':
      return (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <span className="font-bold text-stone-900">Inter-Store Shuttle:</span>{' '}
            Transfer <strong className="text-blue-700">{params.transfer_qty} units</strong> from{' '}
            <strong className="text-stone-800">Store {params.source_store_id}</strong> to{' '}
            <strong className="text-stone-800">Store {params.target_store_id}</strong>
          </div>
          <div className="text-[11px] text-stone-500 font-medium">
            Transit: ~{params.estimated_transit_days || 2} days &bull; Freight: ${params.freight_cost || 15}
          </div>
        </div>
      );
    case 'REPLENISH':
      return (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <span className="font-bold text-stone-900">Supplier Purchase Order:</span>{' '}
            Issue PO for <strong className="text-emerald-700">+{params.recommended_order_qty} units</strong> to primary supplier
          </div>
          <div className="text-[11px] text-stone-500 font-medium">
            Lead Time: {params.supplier_lead_time_days || 7} days &bull; Reorder Point: {params.reorder_point}
          </div>
        </div>
      );
    case 'MARKDOWN':
      return (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <span className="font-bold text-stone-900">Price Liquidation:</span>{' '}
            Apply <strong className="text-amber-700">{params.markdown_pct}% Markdown</strong> (from ${params.original_price} down to ${params.discounted_price}) on <strong className="text-stone-800">{params.excess_units} surplus units</strong>
          </div>
          <div className="text-[11px] text-stone-500 font-medium">
            Goal: Liquidate overstock before holding costs erode gross margin
          </div>
        </div>
      );
    case 'INCREASE_ALLOCATION':
      return (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <span className="font-bold text-stone-900">Distribution Priority:</span>{' '}
            Increase regional DC allocation priority by <strong className="text-indigo-700">+{params.allocation_increase_pct || 40}%</strong>
          </div>
          <div className="text-[11px] text-stone-500 font-medium">
            Protect against high-velocity seasonal demand surge
          </div>
        </div>
      );
    case 'ADJUST_PROMOTION':
      return (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <span className="font-bold text-stone-900">Merchandising Bundle:</span>{' '}
            Feature in cross-merchandising circular to stimulate demand velocity without permanent discount
          </div>
          <div className="text-[11px] text-stone-500 font-medium">
            Target: Normalize stock runway back to optimal 28-day target
          </div>
        </div>
      );
    case 'SUBSTITUTE_PRODUCT':
      return (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <span className="font-bold text-stone-900">Shelf Facing Switch:</span>{' '}
            Direct shelf space to alternative active SKU <strong className="text-cyan-700">{params.substitute_sku || 'substitute item'}</strong>
          </div>
          <div className="text-[11px] text-stone-500 font-medium">
            Avoid lost consumer basket revenue during supply disruption
          </div>
        </div>
      );
    case 'TAKE_NO_ACTION':
    default:
      return (
        <div className="text-stone-700">
          <span className="font-bold text-stone-900">Optimal Equilibrium:</span>{' '}
          Inventory matches predicted velocity within the optimal safety band. No ordering or discounting required.
        </div>
      );
  }
}

export default function DecisionCenter() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [selectedActionFilter, setSelectedActionFilter] = useState('ALL');
  const [expandedDecisions, setExpandedDecisions] = useState({});
  const [enrichingId, setEnrichingId] = useState(null);
  const [executingId, setExecutingId] = useState(null);
  const [leadTimeDays, setLeadTimeDays] = useState(7);
  const [serviceLevel, setServiceLevel] = useState(0.95);
  const [showBaselineModal, setShowBaselineModal] = useState(false);
  const [runningPipeline, setRunningPipeline] = useState(false);
  const [activeStep, setActiveStep] = useState(0);

  const PIPELINE_STEPS = [
    { num: 1, title: 'Observer Agent', desc: 'Classifying store-SKU risk profiles' },
    { num: 2, title: 'Predictor Agent', desc: 'Projecting runway & transfer surplus' },
    { num: 3, title: 'Decider Agent', desc: 'Arbitrating 7 action levers' },
    { num: 4, title: 'Groq Reasoner', desc: 'Evaluating connected trade-offs' },
    { num: 5, title: 'Measurer Agent', desc: 'Quantifying Before vs After Baseline' },
  ];

  const handleRunPipeline = async () => {
    setRunningPipeline(true);
    for (let i = 1; i <= 5; i++) {
      setActiveStep(i);
      await new Promise((r) => setTimeout(r, 650));
    }
    await fetchDecisions();
    setRunningPipeline(false);
    setActiveStep(0);
  };

  const fetchDecisions = async () => {
    setLoading(true);
    try {
      const res = await decisionService.getDecisions({
        lead_time_days: leadTimeDays,
        service_level: serviceLevel,
      });
      setData(res.data);
    } catch (err) {
      console.error('Failed to load decisions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDecisions();
  }, [leadTimeDays, serviceLevel]);

  const toggleExpand = (id) => {
    setExpandedDecisions((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleEnrichReasoning = async (decision) => {
    setEnrichingId(decision.id);
    try {
      const res = await decisionService.enrichReasoning(decision);
      if (res.data?.ai_rationale) {
        setData((prev) => ({
          ...prev,
          decisions: prev.decisions.map((d) =>
            d.id === decision.id ? { ...d, rationale: res.data.ai_rationale, is_enriched: true } : d
          ),
        }));
      }
    } catch (err) {
      console.error('Enrichment failed:', err);
    } finally {
      setEnrichingId(null);
    }
  };

  const handleExecuteAction = async (decisionId) => {
    setExecutingId(decisionId);
    try {
      await decisionService.executeAction(decisionId, 'Approved by inventory planner.');
      setData((prev) => ({
        ...prev,
        decisions: prev.decisions.map((d) =>
          d.id === decisionId ? { ...d, is_executed: true, executed_at: new Date().toISOString() } : d
        ),
      }));
    } catch (err) {
      console.error('Execution failed:', err);
    } finally {
      setExecutingId(null);
    }
  };

  const filteredDecisions =
    data?.decisions?.filter(
      (d) => selectedActionFilter === 'ALL' || d.action === selectedActionFilter
    ) || [];

  const breakdown = data?.action_breakdown || {};
  const benchmark = data?.baseline_comparison || {};

  return (
    <div className="space-y-6">
      {/* ── Top Header ────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white p-6 rounded-2xl border border-stone-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-stone-900 to-stone-700 text-white shadow-sm">
              <Brain className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-stone-900">
                Autonomous Decision Intelligence
              </h1>
              <p className="text-sm text-stone-500 font-medium">
                Observe → Predict → Reason → Decide → Act → Measure
              </p>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 font-semibold border border-emerald-200">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Groq LLM Active: openai/gpt-oss-20b
            </span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-stone-100 text-stone-700 font-medium">
              Multi-Store Network Sync: Real-Time
            </span>
          </div>
        </div>

        {/* Sliders & Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 bg-stone-50 border border-stone-200 px-3 py-1.5 rounded-xl text-xs">
            <Sliders className="w-3.5 h-3.5 text-stone-500" />
            <span className="text-stone-600 font-medium">Lead Time:</span>
            <select
              value={leadTimeDays}
              onChange={(e) => setLeadTimeDays(Number(e.target.value))}
              className="bg-transparent font-semibold text-stone-800 outline-none cursor-pointer"
            >
              <option value={3}>3 Days (Fast)</option>
              <option value={7}>7 Days (Standard)</option>
              <option value={14}>14 Days (Extended)</option>
            </select>
          </div>

          <div className="flex items-center gap-2 bg-stone-50 border border-stone-200 px-3 py-1.5 rounded-xl text-xs">
            <ShieldCheck className="w-3.5 h-3.5 text-stone-500" />
            <span className="text-stone-600 font-medium">Target Service:</span>
            <select
              value={serviceLevel}
              onChange={(e) => setServiceLevel(Number(e.target.value))}
              className="bg-transparent font-semibold text-stone-800 outline-none cursor-pointer"
            >
              <option value={0.9}>90% SLA</option>
              <option value={0.95}>95% SLA (Recommended)</option>
              <option value={0.99}>99% SLA (Aggressive)</option>
            </select>
          </div>

          <button
            onClick={handleRunPipeline}
            disabled={runningPipeline || loading}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl shadow-sm transition-all"
          >
            <Play className={`w-3.5 h-3.5 fill-current ${runningPipeline ? 'animate-pulse' : ''}`} />
            {runningPipeline ? 'Running Agents...' : 'Run Agentic Pipeline'}
          </button>

          <button
            onClick={fetchDecisions}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3.5 py-2 bg-stone-900 hover:bg-stone-800 text-white text-xs font-semibold rounded-xl shadow-sm transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* ── Agentic Execution Stepper ───────────────────────────── */}
      {runningPipeline && (
        <div className="bg-stone-900 border border-stone-800 rounded-2xl p-5 text-white shadow-lg animate-fade-in">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs uppercase tracking-widest text-emerald-400 font-bold flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              Multi-Agent Orchestrator Active
            </span>
            <span className="text-xs text-stone-400">Step {activeStep} of 5</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
            {PIPELINE_STEPS.map((step) => {
              const isPast = activeStep > step.num;
              const isCurrent = activeStep === step.num;
              return (
                <div
                  key={step.num}
                  className={`p-3 rounded-xl border transition-all ${
                    isCurrent
                      ? 'bg-stone-800 border-emerald-400/80 shadow-md scale-[1.02]'
                      : isPast
                      ? 'bg-stone-800/40 border-stone-700 text-stone-300'
                      : 'bg-stone-900/60 border-stone-800 text-stone-500'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                        isCurrent
                          ? 'bg-emerald-500 text-stone-950 animate-pulse'
                          : isPast
                          ? 'bg-emerald-700 text-white'
                          : 'bg-stone-800 text-stone-500'
                      }`}
                    >
                      {isPast ? '✓' : step.num}
                    </span>
                    <span className="text-xs font-bold truncate">{step.title}</span>
                  </div>
                  <div className="text-[10px] text-stone-400 leading-snug">{step.desc}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Baseline Comparison & Performance Lift ─────────────────── */}
      <div className="bg-gradient-to-br from-stone-900 to-stone-800 rounded-2xl p-6 text-white shadow-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-stone-700/60 gap-3">
          <div>
            <div className="text-xs uppercase tracking-widest text-emerald-400 font-bold">
              Business Impact Benchmark
            </div>
            <h2 className="text-lg font-semibold text-white mt-0.5">
              Autonomous AI Decision Engine vs. Traditional Min-Max Baseline
            </h2>
          </div>
          <div className="text-xs text-stone-300 max-w-md">
            {benchmark.summary || 'Comparing connected agentic decisions against isolated single-store thresholds.'}
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-5">
          {benchmark.metrics?.map((m, idx) => (
            <div key={idx} className="bg-stone-800/60 border border-stone-700 rounded-xl p-3.5">
              <div className="text-xs text-stone-400 truncate">{m.metric}</div>
              <div className="text-xl font-bold text-white mt-1">{m.ai_system}</div>
              <div className="mt-1 flex items-center gap-1.5 text-xs">
                <span className="font-semibold text-emerald-400">{m.delta}</span>
                <span className="text-stone-400 text-[10px]">vs {m.baseline}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Action Filter Tabs ─────────────────────────────────────── */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        <button
          onClick={() => setSelectedActionFilter('ALL')}
          className={`px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
            selectedActionFilter === 'ALL'
              ? 'bg-stone-900 text-white shadow-sm'
              : 'bg-white border border-stone-200 text-stone-600 hover:bg-stone-50'
          }`}
        >
          All Decisions ({data?.total_decisions || 0})
        </button>

        {Object.entries(ACTION_COLORS).map(([action, colorClass]) => {
          const count = breakdown[action] || 0;
          if (count === 0 && selectedActionFilter !== action) return null;
          const Icon = ACTION_ICONS[action] || Layers;
          const isSelected = selectedActionFilter === action;

          return (
            <button
              key={action}
              onClick={() => setSelectedActionFilter(action)}
              className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                isSelected
                  ? 'bg-stone-900 text-white shadow-sm'
                  : 'bg-white border border-stone-200 text-stone-700 hover:bg-stone-50'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{action.replace('_', ' ')}</span>
              <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${isSelected ? 'bg-stone-800 text-stone-200' : 'bg-stone-100 text-stone-600'}`}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* ── Decision Action Cards ──────────────────────────────────── */}
      {loading ? (
        <div className="flex flex-col items-center justify-center p-16 bg-white rounded-2xl border border-stone-200">
          <RefreshCw className="w-8 h-8 text-stone-400 animate-spin" />
          <div className="mt-3 text-sm font-semibold text-stone-700">Evaluating Multi-Store Supply Chain Signals...</div>
          <div className="text-xs text-stone-400 mt-1">Simulating interconnected tradeoffs across Demand, Logistics, and Margins</div>
        </div>
      ) : filteredDecisions.length === 0 ? (
        <div className="text-center p-12 bg-white rounded-2xl border border-stone-200">
          <CheckCircle className="w-10 h-10 text-emerald-500 mx-auto" />
          <h3 className="text-base font-semibold text-stone-800 mt-3">No decisions required under this filter</h3>
          <p className="text-xs text-stone-500 mt-1">All store and SKU signals are operating within target equilibrium parameters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredDecisions.map((decision) => {
            const Icon = ACTION_ICONS[decision.action] || Layers;
            const actionStyle = ACTION_COLORS[decision.action] || 'bg-stone-50 text-stone-700 border-stone-200';
            const urgencyStyle = URGENCY_COLORS[decision.urgency] || 'bg-stone-100 text-stone-600 border-stone-200';
            const isExpanded = expandedDecisions[decision.id];
            const isEnriching = enrichingId === decision.id;
            const isExecuting = executingId === decision.id;

            return (
              <div
                key={decision.id}
                className={`bg-white rounded-2xl border transition-all ${
                  decision.is_executed
                    ? 'border-emerald-200 bg-emerald-50/20 shadow-none'
                    : 'border-stone-200 shadow-sm hover:border-stone-300'
                }`}
              >
                {/* Main Card Header */}
                <div className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-start gap-3.5">
                    <div className={`p-2.5 rounded-xl border ${actionStyle} flex-shrink-0`}>
                      <Icon className="w-5 h-5" />
                    </div>

                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-bold text-sm text-stone-900 tracking-tight">
                          {decision.store_id} &bull; {decision.item_id}
                        </span>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border uppercase ${actionStyle}`}>
                          {decision.action.replace('_', ' ')}
                        </span>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border uppercase ${urgencyStyle}`}>
                          {decision.urgency}
                        </span>
                        {decision.is_executed && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
                            <Check className="w-3 h-3" /> Executed
                          </span>
                        )}
                      </div>

                      <CleanRationale text={decision.rationale} />

                      {/* Signals & Indicators */}
                      <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-stone-500">
                        <div className="bg-stone-50 px-2 py-1 rounded-md border border-stone-100">
                          Stock: <strong className="text-stone-800">{decision.signals?.current_stock}</strong>
                        </div>
                        <div className="bg-stone-50 px-2 py-1 rounded-md border border-stone-100">
                          Runway: <strong className="text-stone-800">{decision.signals?.days_of_stock}d</strong>
                        </div>
                        <div className="bg-stone-50 px-2 py-1 rounded-md border border-stone-100">
                          Velocity: <strong className="text-stone-800">{decision.signals?.daily_velocity}/day</strong>
                        </div>
                        <div className="bg-stone-50 px-2 py-1 rounded-md border border-stone-100">
                          Price: <strong className="text-stone-800">${decision.signals?.unit_price}</strong>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Actions & Buttons */}
                  <div className="flex items-center gap-2.5 md:flex-col md:items-end flex-shrink-0">
                    {!decision.is_executed ? (
                      <button
                        onClick={() => handleExecuteAction(decision.id)}
                        disabled={isExecuting}
                        className="inline-flex items-center gap-1.5 px-4 py-2 bg-stone-900 hover:bg-stone-800 text-white text-xs font-semibold rounded-xl shadow-sm transition-all"
                      >
                        {isExecuting ? (
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                        )}
                        Execute Action
                      </button>
                    ) : (
                      <div className="text-[11px] text-emerald-700 font-medium">
                        Audited &bull; {new Date(decision.executed_at).toLocaleTimeString()}
                      </div>
                    )}

                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => handleEnrichReasoning(decision)}
                        disabled={isEnriching}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-stone-200 hover:bg-stone-50 text-[11px] font-semibold text-stone-700 transition-all"
                        title="Run Groq LLM reasoning analysis"
                      >
                        <Sparkles className={`w-3 h-3 text-purple-600 ${isEnriching ? 'animate-spin' : ''}`} />
                        {decision.is_enriched ? 'Reasoned' : 'Groq Reason'}
                      </button>

                      <button
                        onClick={() => toggleExpand(decision.id)}
                        className="p-1.5 rounded-lg border border-stone-200 hover:bg-stone-50 text-stone-600 transition-all"
                        title="Toggle Value Chain Breakdown"
                      >
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Expanded Value Chain Breakdown */}
                {isExpanded && (
                  <div className="px-5 pb-5 pt-2 border-t border-stone-100 bg-stone-50/50 rounded-b-2xl">
                    <div className="text-[11px] uppercase tracking-wider font-bold text-stone-500 mb-3">
                      Connected Retail Value-Chain Tradeoffs
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                      <div className="p-3 bg-white rounded-xl border border-stone-200">
                        <div className="font-semibold text-stone-700">Demand & Customers</div>
                        <div className="text-stone-500 mt-1">{decision.tradeoff_chain?.demand}</div>
                        <div className="text-stone-400 text-[11px] mt-1 italic">{decision.tradeoff_chain?.customer_experience}</div>
                      </div>

                      <div className="p-3 bg-white rounded-xl border border-stone-200">
                        <div className="font-semibold text-stone-700">Replenishment & Logistics</div>
                        <div className="text-stone-500 mt-1">{decision.tradeoff_chain?.replenishment}</div>
                        <div className="text-stone-400 text-[11px] mt-1">{decision.tradeoff_chain?.logistics}</div>
                      </div>

                      <div className="p-3 bg-white rounded-xl border border-stone-200">
                        <div className="font-semibold text-stone-700">Financial Margin & Capital</div>
                        <div className="text-stone-500 mt-1">{decision.tradeoff_chain?.margin}</div>
                        <div className="text-emerald-600 font-semibold text-[11px] mt-1">
                          Protected Value: ${decision.expected_impact?.financial_gain || decision.expected_impact?.working_capital_freed || '0.00'}
                        </div>
                      </div>
                    </div>

                    <div className="mt-3 p-3 bg-white rounded-xl border border-stone-200 text-xs">
                      <div className="text-[10px] uppercase tracking-wider font-bold text-stone-400 mb-1">
                        Operational Execution Directive
                      </div>
                      {formatActionPlan(decision.action, decision.parameters)}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

