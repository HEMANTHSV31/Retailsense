import { useState, useEffect } from 'react';
import { inventoryService } from '../services/index';
import KpiCard from '../components/common/KpiCard';
import { LoadingSpinner, ErrorState } from '../components/common/LoadingState';
import { formatNumber } from '../utils/helpers';
import { Package, AlertTriangle, TrendingUp, ShoppingCart, Rocket, AlertCircle, Boxes, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, PieChart, Pie, Cell, Legend } from 'recharts';

const STATUS_COLORS = {
  OK: '#10B981',       // Emerald
  LOW: '#F59E0B',      // Amber
  CRITICAL: '#EF4444', // Red
  EXCESS: '#3B82F6',   // Blue
};

const tooltipStyle = {
  contentStyle: {
    borderRadius: '10px',
    border: '1px solid #e5e5df',
    background: '#ffffff',
    color: '#292925',
    fontSize: '12px',
    boxShadow: '0 8px 24px -8px rgb(0 0 0 / 0.15)',
  },
};

function StatusBadge({ status }) {
  const styles = {
    CRITICAL: 'bg-red-100 text-red-800 border-red-200',
    LOW: 'bg-amber-100 text-amber-800 border-amber-200',
    OK: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    EXCESS: 'bg-blue-100 text-blue-800 border-blue-200',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${styles[status] || 'bg-neutral-100 text-neutral-800'}`}>
      {status}
    </span>
  );
}

function ChartCard({ title, subtitle, children }) {
  return (
    <div className="content-section">
      <div className="content-section-title">{title}</div>
      {subtitle && <div className="text-xs text-neutral-500 -mt-3 mb-4">{subtitle}</div>}
      {children}
    </div>
  );
}

export default function Inventory() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [config, setConfig] = useState({ serviceLevel: 0.95, leadTime: 7, excessThreshold: 60, sampleSize: 2000 });

  const runOptimizer = async (overrides = {}) => {
    setLoading(true);
    setError(null);
    try {
      const activeConfig = { ...config, ...overrides };
      const res = await inventoryService.generateRecommendations({
        service_level: activeConfig.serviceLevel,
        lead_time_days: activeConfig.leadTime,
        excess_threshold_days: activeConfig.excessThreshold,
        sample_size: activeConfig.sampleSize,
      });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to generate recommendations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runOptimizer();
  }, []);

  const metrics = result?.metrics;
  const statusData = metrics ? [
    { name: 'OK', value: metrics.items_ok },
    { name: 'LOW', value: metrics.items_low },
    { name: 'CRITICAL', value: metrics.items_critical },
    { name: 'EXCESS', value: metrics.items_excess },
  ].filter(d => d.value > 0) : [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Inventory Optimization Engine</h1>
          <p className="page-subtitle">Multi-echelon safety stock, reorder point (ROP), EOQ, and stockout risk calculations</p>
        </div>
      </div>

      {/* Config */}
      <div className="content-section">
        <div className="content-section-title">Safety Stock & Replenishment Parameters</div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label className="field-label">Service Level (Z-Score)</label>
            <select
              value={config.serviceLevel}
              onChange={e => setConfig({ ...config, serviceLevel: parseFloat(e.target.value) })}
              className="select w-full"
            >
              <option value={0.90}>90% (Z = 1.28)</option>
              <option value={0.95}>95% (Z = 1.65 - Standard)</option>
              <option value={0.98}>98% (Z = 2.05)</option>
              <option value={0.99}>99% (Z = 2.33 - High Availability)</option>
            </select>
          </div>
          <div>
            <label className="field-label">Supplier Lead Time (days)</label>
            <input
              type="number"
              min="1"
              max="60"
              value={config.leadTime}
              onChange={e => setConfig({ ...config, leadTime: parseInt(e.target.value) || 7 })}
              className="input w-full"
            />
          </div>
          <div>
            <label className="field-label">Excess Threshold (days)</label>
            <input
              type="number"
              min="30"
              max="365"
              value={config.excessThreshold}
              onChange={e => setConfig({ ...config, excessThreshold: parseInt(e.target.value) || 60 })}
              className="input w-full"
            />
          </div>
          <div>
            <label className="field-label">Demand Horizon</label>
            <input
              type="text"
              readOnly
              value="Recent 28 Days"
              className="input w-full bg-neutral-50 text-neutral-600 cursor-not-allowed"
            />
          </div>
          <div className="flex items-end">
            <button onClick={() => runOptimizer()} disabled={loading} className="btn-gradient w-full flex items-center justify-center gap-2">
              {loading ? (
                <>
                  <svg className="animate-spin w-4 h-4 text-white" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Optimizing...</span>
                </>
              ) : (
                <>
                  <Rocket className="w-4 h-4" />
                  <span>Recompute Engine</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {error && <ErrorState message={error} />}
      {loading && !result && <LoadingSpinner message="Calculating optimal safety stocks and economic order quantities..." />}

      {result && (
        <>
          {/* KPI Row */}
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            <KpiCard
              label="SKU-Store Combos"
              value={formatNumber(metrics.total_items)}
              icon={Package}
              sub="Monitored nodes"
              color="blue"
            />
            <KpiCard
              label="Healthy Stock"
              value={formatNumber(metrics.items_ok)}
              sub={`${metrics.total_items > 0 ? ((metrics.items_ok / metrics.total_items) * 100).toFixed(0) : 0}% in safety band`}
              icon={TrendingUp}
              color="green"
            />
            <KpiCard
              label="Stockout Risk"
              value={formatNumber(metrics.items_low + metrics.items_critical)}
              sub={`${metrics.items_critical} critical · ${metrics.items_low} low`}
              icon={AlertTriangle}
              color="red"
            />
            <KpiCard
              label="Need Reorder"
              value={formatNumber(metrics.items_need_reorder)}
              sub={`${formatNumber(Math.round(metrics.total_recommended_orders))} total units`}
              icon={ShoppingCart}
              color="orange"
            />
            <KpiCard
              label="Avg Days of Stock"
              value={metrics.avg_days_of_stock.toFixed(1)}
              sub={`${metrics.items_excess} excess items`}
              icon={Boxes}
              color="purple"
            />
          </div>

          {/* Charts Row */}
          <div className="grid lg:grid-cols-2 gap-6">
            <ChartCard title="Health Distribution" subtitle="Share of SKU-store inventory states">
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie
                    data={statusData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={4}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {statusData.map((d, i) => (
                      <Cell key={i} fill={STATUS_COLORS[d.name] || '#999'} />
                    ))}
                  </Pie>
                  <Tooltip {...tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Items by Risk Tier" subtitle="Number of items across inventory statuses">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={statusData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e9e9e4" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#52525b' }} tickLine={false} axisLine={{ stroke: '#d4d4d8' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#52525b' }} tickLine={false} axisLine={false} />
                  <Tooltip {...tooltipStyle} />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]} name="Item Count">
                    {statusData.map((d, i) => (
                      <Cell key={i} fill={STATUS_COLORS[d.name] || '#999'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {/* Main Inventory Optimization Table */}
          <div className="content-section">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="content-section-title mb-0">Inventory Optimization Recommendations</div>
                <p className="text-xs text-neutral-500 mt-0.5">Calculated based on demand volatility ($\sigma$), supplier lead time, and target service levels</p>
              </div>
              <span className="text-xs bg-neutral-100 text-neutral-700 px-3 py-1 rounded-full font-medium">
                {result.recommendations?.length || 0} items evaluated
              </span>
            </div>

            <div className="scroll-thin max-h-96 overflow-y-auto">
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Product SKU</th>
                      <th>Store</th>
                      <th className="text-right">On-Hand Stock</th>
                      <th className="text-right">Avg Daily Demand</th>
                      <th className="text-right">Safety Stock</th>
                      <th className="text-right">Reorder Point (ROP)</th>
                      <th className="text-right">EOQ</th>
                      <th className="text-right">Recommended Order</th>
                      <th className="text-right">Days of Stock</th>
                      <th className="text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.recommendations?.map((r, i) => (
                      <tr key={i} className="hover:bg-neutral-50/70 transition-colors">
                        <td className="font-semibold text-neutral-900">{r.item_id}</td>
                        <td className="text-neutral-700">{r.store_id}</td>
                        <td className="num font-semibold text-neutral-900">{formatNumber(Math.round(r.current_stock))}</td>
                        <td className="num text-neutral-700">{r.avg_daily_demand.toFixed(1)} / day</td>
                        <td className="num text-neutral-700">{Math.round(r.safety_stock)}</td>
                        <td className="num text-neutral-700">{Math.round(r.reorder_point)}</td>
                        <td className="num text-neutral-700">{Math.round(r.eoq)}</td>
                        <td className="num">
                          {r.recommended_order_qty > 0 ? (
                            <span className="font-bold text-amber-700">+{Math.round(r.recommended_order_qty)}</span>
                          ) : (
                            <span className="text-neutral-400">0</span>
                          )}
                        </td>
                        <td className="num text-neutral-700">{r.days_of_stock.toFixed(1)} d</td>
                        <td className="text-center">
                          <StatusBadge status={r.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Stockout predictions */}
          {result.stockout_predictions?.length > 0 && (
            <div className="content-section">
              <div className="flex items-center gap-2 content-section-title">
                <AlertCircle className="w-4 h-4 text-red-600" />
                Stockout Risk Predictions (&lt; 90 Days Runway)
              </div>
              <div className="scroll-thin max-h-64 overflow-y-auto">
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Product SKU</th>
                        <th>Store</th>
                        <th className="text-right">Current Stock</th>
                        <th className="text-right">Days Remaining</th>
                        <th className="text-right">Estimated Depletion Date</th>
                        <th className="text-center">Risk Tier</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.stockout_predictions.map((s, i) => (
                        <tr key={i}>
                          <td className="font-semibold text-neutral-900">{s.item_id}</td>
                          <td className="text-neutral-700">{s.store_id}</td>
                          <td className="num">{formatNumber(Math.round(s.current_stock))}</td>
                          <td className="num font-bold text-red-600">{s.days_remaining.toFixed(0)} days</td>
                          <td className="num text-neutral-700">{s.predicted_stockout_date}</td>
                          <td className="text-center">
                            {s.is_critical ? (
                              <span className="badge-critical">Critical Runway</span>
                            ) : (
                              <span className="badge-low">Warning</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Overstock */}
          {result.overstock_items?.length > 0 && (
            <div className="content-section">
              <div className="flex items-center gap-2 content-section-title">
                <Boxes className="w-4 h-4 text-blue-600" />
                Overstock & Surplus Inventory Detection
              </div>
              <p className="text-xs text-neutral-500 mb-3">{result.overstock_items.length} items holding capital above the excess threshold</p>
              <div className="scroll-thin max-h-64 overflow-y-auto">
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Product SKU</th>
                        <th>Store</th>
                        <th className="text-right">Current Stock</th>
                        <th className="text-right">Days of Stock</th>
                        <th className="text-right">Excess Units</th>
                        <th>Strategic Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.overstock_items.map((o, i) => (
                        <tr key={i}>
                          <td className="font-semibold text-neutral-900">{o.item_id}</td>
                          <td className="text-neutral-700">{o.store_id}</td>
                          <td className="num">{formatNumber(Math.round(o.current_stock))}</td>
                          <td className="num font-bold text-blue-600">{o.days_of_stock.toFixed(0)} d</td>
                          <td className="num font-semibold text-amber-700">{formatNumber(Math.round(o.excess_units))}</td>
                          <td className="text-xs text-neutral-600">{o.reason || 'Eligible for Lateral Transfer or Markdown'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
