import { useState, useEffect } from 'react';
import { forecastService } from '../services/index';
import KpiCard from '../components/common/KpiCard';
import { ErrorState, LoadingSpinner } from '../components/common/LoadingState';
import { formatNumber, formatDate } from '../utils/helpers';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { TrendingUp, Calendar, Brain, Rocket, Sparkles, Store, Package } from 'lucide-react';

const tooltipStyle = {
  contentStyle: {
    borderRadius: '12px',
    border: '1px solid #e5e5df',
    background: '#ffffff',
    color: '#292925',
    fontSize: '12px',
    boxShadow: '0 8px 24px -8px rgb(0 0 0 / 0.15)',
  },
};

export default function Forecast() {
  const [options, setOptions] = useState({ products: [], stores: [], models: [] });
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [itemId, setItemId] = useState('');
  const [storeId, setStoreId] = useState('');
  const [modelType, setModelType] = useState('random_forest');
  const [horizon, setHorizon] = useState(30);
  const [forecastResult, setForecastResult] = useState(null);

  useEffect(() => {
    forecastService.options()
      .then(res => {
        const data = res.data;
        setOptions(data);
        const defaultProd = data.products?.[0] || 'SKU001';
        const defaultStore = data.stores?.[0] || 'STORE_A';
        setItemId(defaultProd);
        setStoreId(defaultStore);

        // Auto-generate initial forecast
        if (defaultProd && defaultStore) {
          triggerForecast(defaultProd, defaultStore, 30, 'random_forest');
        }
      })
      .catch(e => setError(e.response?.data?.detail || 'Failed to load forecast options'))
      .finally(() => setLoadingOptions(false));
  }, []);

  const triggerForecast = async (item, store, h, model) => {
    setLoading(true);
    setError(null);
    try {
      const res = await forecastService.generate({
        item_id: item,
        store_id: store,
        horizon_days: h,
        model_type: model,
      });
      setForecastResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to generate forecast');
    } finally {
      setLoading(false);
    }
  };

  const handleManualGenerate = () => {
    if (!itemId || !storeId) {
      setError('Please select both a Product SKU and a Store');
      return;
    }
    triggerForecast(itemId, storeId, horizon, modelType);
  };

  const chartData = forecastResult?.forecast?.map(f => ({
    date: f.forecast_date,
    predicted_sales: f.predicted_sales,
    type: 'Forecast',
  })) || [];

  if (loadingOptions) {
    return <LoadingSpinner message="Loading forecast intelligence engine..." />;
  }

  return (
    <div className="space-y-8 animate-fade-in floating-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">ML Demand Forecast</h1>
          <p className="page-subtitle">Multi-horizon demand predictions powered by trained regression models (XGBoost, Random Forest, LightGBM)</p>
        </div>
      </div>

      {/* Config - Floating Panel */}
      <div className="content-section">
        <div className="flex items-center gap-2 content-section-title">
          <Brain className="w-5 h-5 text-neutral-900" />
          Model & Horizon Configuration
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label className="field-label flex items-center gap-1.5">
              <Package className="w-3.5 h-3.5 text-neutral-500" />
              Product SKU
            </label>
            <select
              value={itemId}
              onChange={e => setItemId(e.target.value)}
              className="select w-full"
            >
              {options.products.map(p => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="field-label flex items-center gap-1.5">
              <Store className="w-3.5 h-3.5 text-neutral-500" />
              Store Location
            </label>
            <select
              value={storeId}
              onChange={e => setStoreId(e.target.value)}
              className="select w-full"
            >
              {options.stores.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="field-label flex items-center gap-1.5">
              <Brain className="w-3.5 h-3.5 text-neutral-500" />
              Algorithm
            </label>
            <select
              value={modelType}
              onChange={e => setModelType(e.target.value)}
              className="select w-full"
            >
              <option value="random_forest">Random Forest</option>
              <option value="xgboost">XGBoost Regressor</option>
              <option value="lightgbm">LightGBM Regressor</option>
              <option value="baseline">Mean Baseline</option>
            </select>
          </div>

          <div>
            <label className="field-label flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-neutral-500" />
              Horizon
            </label>
            <select
              value={horizon}
              onChange={e => setHorizon(Number(e.target.value))}
              className="select w-full"
            >
              <option value={7}>7 Days (Tactical)</option>
              <option value={14}>14 Days (Bi-weekly)</option>
              <option value={30}>30 Days (Monthly)</option>
              <option value={90}>90 Days (Quarterly)</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={handleManualGenerate}
              disabled={loading}
              className="btn-gradient w-full flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin w-4 h-4 text-white" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Predicting...</span>
                </>
              ) : (
                <>
                  <Rocket className="w-4 h-4" />
                  <span>Run Forecast</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {error && <ErrorState message={error} />}

      {/* Results */}
      {forecastResult && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 section-gap">
            <KpiCard
              label="Total Forecast"
              value={formatNumber(Math.round(forecastResult.summary.total_forecast))}
              icon={TrendingUp}
              sub={`${horizon}-day cumulative units`}
              aiInsight
            />
            <KpiCard
              label="Avg Daily Demand"
              value={formatNumber(Math.round(forecastResult.summary.avg_daily))}
              icon={Calendar}
              sub="Projected units/day"
            />
            <KpiCard
              label="Peak Demand Day"
              value={formatDate(forecastResult.summary.peak_day)}
              sub={`${formatNumber(Math.round(forecastResult.summary.peak_value))} units predicted`}
              icon={TrendingUp}
            />
            <KpiCard
              label="Active Model"
              value={forecastResult.header.model_type.replace('_', ' ').toUpperCase()}
              icon={Brain}
              sub="Trained on historical signals"
              aiInsight
            />
          </div>

          {/* Chart */}
          <div className="content-section section-gap">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-2 content-section-title mb-0">
                  <TrendingUp className="w-4 h-4 text-neutral-900" />
                  Forecast Trajectory
                </div>
                <div className="text-xs text-neutral-500 mt-0.5">
                  Predicted daily demand for SKU: <span className="font-semibold text-neutral-800">{itemId}</span> at Store: <span className="font-semibold text-neutral-800">{storeId}</span>
                </div>
              </div>
              <div className="chip-ai flex items-center gap-1.5 px-3 py-1 bg-neutral-900 text-white rounded-full text-xs font-medium">
                <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                ML Regression Active
              </div>
            </div>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={chartData}>
                <defs>
                  <linearGradient id="forecastFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#18181b" stopOpacity={0.08} />
                    <stop offset="100%" stopColor="#18181b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e9e9e4" vertical={false} />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: '#52525b' }}
                  tickLine={false}
                  axisLine={{ stroke: '#d4d4d8' }}
                  tickFormatter={v => new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                />
                <YAxis tick={{ fontSize: 11, fill: '#52525b' }} tickLine={false} axisLine={false} />
                <Tooltip {...tooltipStyle} />
                <Line
                  type="monotone"
                  dataKey="predicted_sales"
                  stroke="#18181b"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#18181b' }}
                  activeDot={{ r: 5, fill: '#000000' }}
                  name="Predicted Sales"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Forecast Table */}
          <div className="content-section">
            <div className="content-section-title">Daily Prediction Breakdown</div>
            <div className="scroll-thin max-h-72 overflow-y-auto">
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Forecast Date</th>
                      <th>Product SKU</th>
                      <th>Store ID</th>
                      <th className="text-right">Predicted Units</th>
                    </tr>
                  </thead>
                  <tbody>
                    {forecastResult.forecast?.map((f, i) => (
                      <tr key={i}>
                        <td className="font-medium text-neutral-800">{formatDate(f.forecast_date)}</td>
                        <td>{f.item_id}</td>
                        <td>{f.store_id}</td>
                        <td className="num font-semibold text-neutral-900">{f.predicted_sales.toFixed(1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
