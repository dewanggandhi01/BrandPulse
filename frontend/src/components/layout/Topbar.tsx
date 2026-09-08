import React, { useEffect, useState } from 'react';
import { Search as SearchIcon, Settings, Bell, Building2, ChevronDown, Plus } from 'lucide-react';
import { Input } from '../ui/Input';
import { useGetBrands } from '../../api/queries/useBrands';
import { useAppStore } from '../../stores/appStore';
import { AddBrandModal } from '../brands/AddBrandModal';

export const Topbar: React.FC = () => {
  const { currentBrandId, setCurrentBrandId } = useAppStore();
  const { data: brands = [] } = useGetBrands();
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // Automatically select first brand if none selected
  useEffect(() => {
    if (!currentBrandId && brands.length > 0) {
      setCurrentBrandId(brands[0].id);
    }
  }, [currentBrandId, brands, setCurrentBrandId]);

  return (
    <header className="h-16 bg-surface border-b border-border flex items-center justify-between px-6 sticky top-0 z-10 shrink-0">
      {/* Search Input */}
      <div className="flex items-center flex-1 max-w-md">
        <div className="relative w-full">
          <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" size={18} />
          <Input 
            placeholder="Search brands, products, keywords..." 
            className="pl-10 h-9"
          />
        </div>
      </div>

      {/* Right Controls: Brand Selector + Icons + User Avatar */}
      <div className="flex items-center gap-4">
        {/* Brand Selector Dropdown */}
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 shadow-xs">
          <Building2 size={16} className="text-blue-600 shrink-0" />
          <div className="relative flex items-center">
            <select
              value={currentBrandId || ''}
              onChange={(e) => setCurrentBrandId(e.target.value || null)}
              className="text-xs font-semibold text-slate-800 bg-transparent pr-6 focus:outline-none cursor-pointer appearance-none"
              aria-label="Select active brand"
            >
              {brands.length === 0 ? (
                <option value="">No Brands Registered</option>
              ) : (
                brands.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name} ({b.domain})
                  </option>
                ))
              )}
            </select>
            <ChevronDown size={14} className="absolute right-0 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          </div>
        </div>

        {/* Prominent Add Brand Button */}
        <button
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center gap-1.5 text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 rounded-lg px-3 py-1.5 transition-all shadow-xs cursor-pointer"
          title="Add New Brand"
        >
          <Plus size={15} className="text-blue-600" />
          <span>Add Brand</span>
        </button>

        <button className="text-slate-500 hover:text-slate-900 relative p-1.5 rounded-lg hover:bg-slate-100 transition-colors" aria-label="Notifications">
          <Bell size={18} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-600 rounded-full border-2 border-surface"></span>
        </button>
        <button className="text-slate-500 hover:text-slate-900 p-1.5 rounded-lg hover:bg-slate-100 transition-colors" aria-label="Settings">
          <Settings size={18} />
        </button>
        <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs border border-blue-200 shadow-xs">
          BP
        </div>
      </div>
      
      <AddBrandModal 
        isOpen={isAddModalOpen} 
        onClose={() => setIsAddModalOpen(false)} 
      />
    </header>
  );
};
