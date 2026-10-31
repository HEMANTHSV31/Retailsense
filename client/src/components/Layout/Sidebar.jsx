import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { LayoutDashboard, BarChart3, TrendingUp, Package, Upload, LogOut, ChevronLeft, ChevronRight, Bot, Activity, Zap, ShieldCheck } from 'lucide-react';
import { useState } from 'react';

const NAV_GROUPS = [
  {
    label: 'Decision Intelligence',
    items: [
      { to: '/decisions', label: 'Decision Center', icon: Zap },
      { to: '/advisor', label: 'AI Advisor (Groq)', icon: Bot },
      { to: '/what-if', label: 'What-If Simulation', icon: Activity },
    ]
  },
  {
    label: 'Operations & Demand',
    items: [
      { to: '/', label: 'Executive Dashboard', icon: LayoutDashboard, end: true },
      { to: '/forecast', label: 'ML Forecast', icon: TrendingUp },
      { to: '/inventory', label: 'Inventory Engine', icon: Package },
      { to: '/analytics', label: 'Store Analytics', icon: BarChart3 },
    ]
  },
  {
    label: 'Data Management',
    items: [
      { to: '/upload', label: 'Upload Data', icon: Upload },
    ]
  }
];

function BrandMark({ collapsed }) {
  return (
    <div className={`flex items-center gap-3 px-4 h-20 border-b border-stone-100 ${collapsed ? 'justify-center' : ''}`}>
      <div className="w-9 h-9 rounded-xl bg-stone-900 flex items-center justify-center text-white shadow-sm flex-shrink-0">
        <svg width="18" height="18" viewBox="0 0 64 64" fill="none" aria-hidden="true">
          <path d="M16 44 V20 M32 44 V12 M48 44 V28" stroke="currentColor" strokeWidth="9" strokeLinecap="round" />
          <circle cx="32" cy="44" r="6" fill="currentColor" />
        </svg>
      </div>
      {!collapsed && (
        <div className="min-w-0">
          <div className="font-semibold text-lg text-stone-900 leading-tight tracking-[-0.04em]">RetailIQ</div>
          <div className="text-[10px] font-medium text-stone-400 uppercase tracking-widest">Intelligence Suite</div>
        </div>
      )}
    </div>
  );
}

function UserCard({ user, collapsed }) {
  if (!user || collapsed) return null;
  return (
    <div className="mx-3 mt-4 p-3 rounded-xl bg-stone-50 border border-stone-100">
      <div className="flex items-center gap-2.5">
        <div className="w-9 h-9 rounded-lg bg-[#E4E4E7] flex items-center justify-center text-[#18181B] text-sm font-bold flex-shrink-0">
          {user.username?.[0]?.toUpperCase() || 'U'}
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-semibold text-stone-800 truncate">{user.username}</div>
          <div className="text-[11px] text-stone-400 capitalize">{user.role}</div>
        </div>
        <span className="w-2 h-2 rounded-full bg-[#18181B] shadow-[0_0_0_3px_rgba(24,24,27,0.12)] flex-shrink-0" title="Online" />
      </div>
    </div>
  );
}

function NavItem({ item, collapsed, isActive }) {
  const Icon = item.icon;
  return (
    <NavLink
      key={item.to}
      to={item.to}
      end={item.end}
      title={collapsed ? item.label : undefined}
      className={({ isActive: active }) =>
        `group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${collapsed ? 'justify-center' : ''} ${active || isActive ? 'bg-stone-900 text-white shadow-sm' : 'text-stone-500 hover:text-stone-900 hover:bg-stone-100'}`
      }
    >
      <Icon className={`w-5 h-5 flex-shrink-0 transition-colors ${collapsed ? 'mx-auto' : ''}`} />
      {!collapsed && item.label}
    </NavLink>
  );
}

export default function Sidebar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside className={`${collapsed ? 'w-[68px]' : 'w-60'} transition-all duration-300 bg-white border-r border-stone-100 flex flex-col h-screen sticky top-0 z-30 flex-shrink-0`}>
      <BrandMark collapsed={collapsed} />
      <UserCard user={user} collapsed={collapsed} />

      <nav className="flex-1 px-3 py-4 space-y-5 overflow-y-auto scroll-thin">
        {NAV_GROUPS.map((group) => (
          <div key={group.label}>
            {!collapsed && (
              <div className="px-3 mb-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-500">
                {group.label}
              </div>
            )}
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const isActive = item.end ? location.pathname === '/' : location.pathname.startsWith(item.to);
                return <NavItem key={item.to} item={item} collapsed={collapsed} isActive={isActive} />;
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-slate-800 p-3 space-y-1 ${collapsed ? 'text-center' : ''}">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-[11px] text-slate-500 ${collapsed ? 'justify-center' : ''}">
          <ShieldCheck className="w-3.5 h-3.5 flex-shrink-0" />
          {!collapsed && <span>Secure session</span>}
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all w-full ${collapsed ? 'justify-center' : ''}"
          title="Logout"
        >
          <LogOut className="w-5 h-5 flex-shrink-0" />
          {!collapsed && 'Logout'}
        </button>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-slate-600 hover:text-slate-300 transition-colors w-full flex justify-center pt-1"
          title="${collapsed ? 'Expand sidebar' : 'Collapse sidebar'}"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>
    </aside>
  );
}


