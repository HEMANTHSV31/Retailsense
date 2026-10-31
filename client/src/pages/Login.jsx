import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { TrendingUp, Sparkles, Package, AlertCircle, Loader2, Eye, EyeOff } from 'lucide-react';

const FEATURE_POINTS = [
  { icon: TrendingUp, title: 'AI Demand Forecasting', desc: 'Predict sales 7–90 days ahead with live context.' },
  { icon: Package, title: 'Inventory Optimization', desc: 'Safety stock, reorder points and stockout alerts.' },
  { icon: Sparkles, title: 'Explainable Insights', desc: 'Understand every prediction with SHAP analysis.' },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg || JSON.stringify(d)).join(', '));
      } else if (detail && typeof detail === 'object') {
        setError(JSON.stringify(detail));
      } else {
        setError('Login failed. Check your credentials.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-white">
      {/* Left form panel */}
      <div className="flex-1 flex items-center justify-center p-6 bg-white">
        <div className="w-full max-w-md animate-fade-in">
          {/* Mobile brand */}
          <div className="lg:hidden text-center mb-8">
            <div className="w-11 h-11 rounded-xl bg-black flex items-center justify-center mx-auto mb-4">
              <svg width="22" height="22" viewBox="0 0 64 64" fill="none">
                <path d="M16 44 V20 M32 44 V12 M48 44 V28" stroke="#fff" strokeWidth="9" strokeLinecap="round" />
                <circle cx="32" cy="44" r="6" fill="#fff" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">RetailIQ</h1>
          </div>

          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Login</h1>
          </div>

          {error && (
            <div className="mb-6 p-3.5 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-start gap-2.5 animate-fade-in">
              <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-7">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-transparent border-0 border-b-2 border-slate-300 focus:border-slate-900 focus:ring-0 outline-none text-slate-900 px-0 py-2.5 text-sm placeholder-slate-400 transition-colors"
                placeholder="Enter your username"
                autoComplete="username"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-transparent border-0 border-b-2 border-slate-300 focus:border-slate-900 ring-0 outline-none text-slate-900 px-0 pr-10 py-2.5 text-sm placeholder-slate-400 transition-colors"
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((s) => !s)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  className="absolute right-0 top-1/2 -translate-y-1/2 bg-transparent border-0 cursor-pointer text-[#9CA3AF] hover:text-slate-600 p-1.5 transition-colors focus:outline-none"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl bg-black text-white text-sm font-semibold hover:bg-slate-800 transition-colors disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin inline-block align-[-2px] mr-2" />
                  Logging in...
                </>
              ) : (
                'Login'
              )}
            </button>
          </form>

          <p className="text-center text-xs text-slate-500 mt-8">
            © {new Date().getFullYear()} RetailIQ · Retail Intelligence Platform
          </p>
        </div>
      </div>

      {/* Right hero panel */}
      <div className="hidden lg:flex w-[46%] relative overflow-hidden bg-[#0e0e10] text-white flex-col p-12 border-l border-slate-800">
        {/* Textured background */}
        <div
          className="absolute inset-0 opacity-[0.06]"
          style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, #fff 1px, transparent 0)', backgroundSize: '26px 26px' }}
        />
        <div className="absolute -bottom-32 -right-32 w-[420px] h-[420px] rounded-full bg-brand-600/25 blur-3xl" />
        <div className="absolute -top-24 -left-16 w-[300px] h-[300px] rounded-full bg-brand-500/15 blur-3xl" />

        {/* Centered container holding the whole right-side content block */}
        <div className="relative flex-1 flex items-center justify-center">
          {/* Single left-aligned vertical column */}
          <div className="flex flex-col items-start max-w-md w-full">
          {/* Brand mark — flush left with content below */}
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-black flex items-center justify-center shadow-glow">
              <svg width="22" height="22" viewBox="0 0 64 64" fill="none">
                <path d="M16 44 V20 M32 44 V12 M48 44 V28" stroke="#fff" strokeWidth="9" strokeLinecap="round" />
                <circle cx="32" cy="44" r="6" fill="#fff" />
              </svg>
            </div>
            <div className="font-bold text-xl tracking-tight">RetailIQ</div>
          </div>

          {/* Content section left-aligned below */}
          <div className="mt-10 space-y-10">
            <p className="text-slate-400 text-base leading-relaxed max-w-md">
              A unified platform for demand forecasting, inventory optimization and
              explainable business intelligence.
            </p>

            <div className="space-y-5">
              {FEATURE_POINTS.map((f, i) => (
                <div key={i} className="flex items-start gap-3.5">
                  <div className="w-9 h-9 rounded-lg bg-white/5 ring-1 ring-white/10 flex items-center justify-center flex-shrink-0 backdrop-blur">
                    <f.icon className="w-5 h-5 text-brand-300" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-white">{f.title}</div>
                    <div className="text-sm text-slate-500">{f.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        </div>
      </div>
    </div>
  );
}

