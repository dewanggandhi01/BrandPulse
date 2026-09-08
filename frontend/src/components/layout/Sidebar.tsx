import React from 'react';
import { NavLink } from 'react-router-dom';
import clsx from 'clsx';
import { 
  LayoutDashboard, 
  Search, 
  Package, 
  Users, 
  Activity, 
  MessageSquare, 
  Megaphone, 
  FileText,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { useAppStore } from '@/stores/appStore';

export const Sidebar: React.FC = () => {
  const { sidebarCollapsed, setSidebarCollapsed } = useAppStore();

  const navItems = [
    { to: '/', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
    { to: '/seo', icon: <Search size={20} />, label: 'SEO Audit' },
    { to: '/products', icon: <Package size={20} />, label: 'Products' },
    { to: '/competitors', icon: <Users size={20} />, label: 'Competitors' },
    { to: '/changes', icon: <Activity size={20} />, label: 'Changes' },
    { to: '/mentions', icon: <MessageSquare size={20} />, label: 'Mentions' },
    { to: '/ads', icon: <Megaphone size={20} />, label: 'Ads Intel' },
    { to: '/reports', icon: <FileText size={20} />, label: 'Reports' },
  ];

  return (
    <aside
      className={clsx(
        'bg-surface border-r border-border h-screen sticky top-0 flex flex-col transition-all duration-300',
        sidebarCollapsed ? 'w-16' : 'w-64'
      )}
    >
      <div className="h-16 flex items-center px-4 border-b border-border justify-between shrink-0">
        {!sidebarCollapsed && <span className="font-bold text-lg text-brand-600 truncate">BrandPulse</span>}
        {sidebarCollapsed && <span className="font-bold text-xl text-brand-600 mx-auto">BP</span>}
      </div>
      
      <div className="flex-1 overflow-y-auto py-4 flex flex-col gap-1 px-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => clsx(
              'flex items-center gap-3 px-3 py-2 rounded transition-colors group',
              isActive 
                ? 'bg-brand-50 text-brand-600 font-medium' 
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
              sidebarCollapsed && 'justify-center px-0'
            )}
            title={sidebarCollapsed ? item.label : undefined}
          >
            <span className="shrink-0">{item.icon}</span>
            {!sidebarCollapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </div>

      <div className="p-2 border-t border-border shrink-0">
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="flex w-full items-center justify-center p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900 rounded transition-colors"
        >
          {sidebarCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>
    </aside>
  );
};
