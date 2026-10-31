import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Package, Store, DollarSign } from 'lucide-react';
import { analyticsService } from '../services/index';
import KpiCard from '../components/common/KpiCard';
import { LoadingSpinner, ErrorState } from '../components/common/LoadingState';
import { formatNumber } from '../utils/helpers';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid, PieChart, Pie, Cell, Legend } from 'recharts';

// Monochrome charcoal palette for multi-category charts (grayscale scale)
const COLORS = ['#18181b', '#52525b', '#a1a1aa', '#71717a'];

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

function ChartCard({ title, subtitle, children, right }) {
  return (
    <div className="content-section">
      <div className="flex items-start justify-between mb-4 gap-4">
        <div>
          <div className="content-section-title mb-0">{title}</div>
          {subtitle && <div className="text-xs text-neutral-500 mt-0.5">{subtitle}</div>}
        </div>
        {right}
      </div>
      {children}
    </div>
  );
}

export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [days, setDays] = useState(90);

  useEffect(() => {
    Promise.all([
      analyticsService.overview(),
      analyticsService.salesTrend(days),
      analyticsService.topProducts(10),
      analyticsService.storePerformance(),
      analyticsService.seasonal(),
      analyticsService.dayOfWeek(),
    ])
      .then(([ov, trend, top, stores, seasonal, dow]) => {
        setData({
          overview: ov.data,
          trend: trend.data,
          topProducts: top.data,
          stores: stores.data,
          seasonal: seasonal.data,
          dayOfWeek: dow.data,
        });
      })
      .catch(e => setError(e.response?.data?.detail || 'Failed to load analytics'))
      .finally(() => setLoading(false));
  }, [days]);

  if (loading) return <LoadingSpinner message="Loading analytics dashboard..." />;
  if (error) return <ErrorState message={error} />;
  if (!data) return null;

  const { overview, trend, topProducts, stores, seasonal, dayOfWeek } = data;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Store & Sales Analytics</h1>
          <p className="page-subtitle">Commercial performance, unit velocity, and channel distribution across stores</p>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <KpiCard
          label="Total Revenue"
          value={`$${formatNumber(Math.round(overview?.total_revenue || 0))}`}
          sub="Gross sales value"
          icon={DollarSign}
          color="green"
        />
        <KpiCard
          label="Total Units Sold"
          value={formatNumber(overview?.total_sales)}
          sub="Volume across network"
          icon={BarChart3}
          color="blue"
        />
        <KpiCard
          label="Avg Daily Velocity"
          value={formatNumber(Math.round(overview?.avg_daily_sales || 0))}
          sub="Units / day average"
          icon={TrendingUp}
          color="purple"
        />
        <KpiCard
          label="Active SKUs"
          value={formatNumber(overview?.total_products)}
          sub={`${overview?.total_categories || 1} categories`}
          icon={Package}
          color="orange"
        />
        <KpiCard
          label="Store Locations"
          value={formatNumber(overview?.total_stores)}
          sub="Operational nodes"
          icon={Store}
          color="slate"
        />
      </div>

      {/* Sales Trend */}
      <ChartCard
        title="Sales Velocity Trend"
        subtitle={`Daily sales volume over the last ${days} days`}
        right={
          <select value={days} onChange={e => setDays(Number(e.target.value))} className="select w-auto">
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={180}>Last 180 days</option>
          </select>
        }
      >
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={trend}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e9e9e4" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: '#52525b' }}
              tickLine={false}
              axisLine={{ stroke: '#d4d4d8' }}
              tickFormatter={v => {
                if (!v) return '';
                const parts = String(v).split('-');
                if (parts.length === 3) {
                  const m = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][parseInt(parts[1], 10)-1];
                  return `${m} ${parseInt(parts[2], 10)}`;
                }
                return v;
              }}
            />
            <YAxis tick={{ fontSize: 11, fill: '#52525b' }} tickLine={false} axisLine={false} tickFormatter={v => formatNumber(v)} />
            <Tooltip {...tooltipStyle} />
            <Line
              type="monotone"
              dataKey="sales"
              stroke="#18181b"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 4, fill: '#18181b' }}
              name="Units Sold"
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Top Products */}
        <ChartCard title="Top Performing SKUs" subtitle="Unit volume & gross revenue contribution">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={topProducts.slice(0, 8)} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e9e9e4" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: '#52525b' }} tickLine={false} axisLine={false} tickFormatter={v => formatNumber(v)} />
              <YAxis dataKey="item_id" type="category" width={90} tick={{ fontSize: 11, fill: '#18181b', fontWeight: 600 }} tickLine={false} axisLine={false} />
              <Tooltip
                {...tooltipStyle}
                formatter={(val, name, item) => [
                  `${formatNumber(val)} units ($${formatNumber(Math.round(item.payload.total_revenue || 0))})`,
                  'Sales',
                ]}
              />
              <Bar dataKey="total_sales" fill="#18181b" radius={[0, 6, 6, 0]} name="Units Sold" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Day of Week */}
        <ChartCard title="Demand by Day of Week" subtitle="Weekly shopping patterns and weekend lifts">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={dayOfWeek}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e9e9e4" vertical={false} />
              <XAxis dataKey="day" tick={{ fontSize: 11, fill: '#52525b' }} tickLine={false} axisLine={{ stroke: '#d4d4d8' }} />
              <YAxis tick={{ fontSize: 11, fill: '#52525b' }} tickLine={false} axisLine={false} tickFormatter={v => formatNumber(v)} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="avg_sales" radius={[6, 6, 0, 0]} name="Avg Daily Units">
                {dayOfWeek?.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Store Performance */}
      <ChartCard title="Store Network Performance" subtitle="Cross-channel comparison of revenue and units">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Store Code</th>
                <th className="text-right">Total Revenue ($)</th>
                <th className="text-right">Total Units Sold</th>
                <th className="text-right">Avg Daily Velocity</th>
                <th className="text-right">Active SKUs</th>
              </tr>
            </thead>
            <tbody>
              {stores?.map((s, i) => (
                <tr key={i} className="hover:bg-neutral-50/70 transition-colors">
                  <td className="font-semibold text-neutral-900">
                    <span className="inline-flex items-center gap-2">
                      <span className="w-6 h-6 rounded bg-neutral-200 text-neutral-800 text-[11px] font-bold flex items-center justify-center">
                        {i + 1}
                      </span>
                      {s.store_id}
                    </span>
                  </td>
                  <td className="num font-bold text-emerald-700">
                    ${formatNumber(Math.round(s.total_revenue || 0))}
                  </td>
                  <td className="num font-semibold text-neutral-900">
                    {formatNumber(s.total_sales)} units
                  </td>
                  <td className="num text-neutral-700">
                    {formatNumber(Math.round(s.avg_daily_sales))} / day
                  </td>
                  <td className="num text-neutral-700">
                    {formatNumber(s.item_count)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </ChartCard>

      {/* Seasonal */}
      {seasonal?.length > 0 && (
        <ChartCard title="Seasonal Breakdown" subtitle="Sales distribution across meteorological seasons">
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={seasonal}
                dataKey="total_sales"
                nameKey="season"
                cx="50%"
                cy="50%"
                innerRadius={52}
                outerRadius={88}
                paddingAngle={3}
                label={({ season, percent }) => `${season} ${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {seasonal.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip {...tooltipStyle} />
              <Legend iconType="circle" iconSize={9} wrapperStyle={{ fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      )}
    </div>
  );
}
