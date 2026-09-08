import React, { useState } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Building2, Globe, Tag, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useCreateBrand } from '../../api/queries/useBrands';
import { useAppStore } from '../../stores/appStore';

interface AddBrandModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AddBrandModal: React.FC<AddBrandModalProps> = ({ isOpen, onClose }) => {
  const [name, setName] = useState('');
  const [domain, setDomain] = useState('');
  const [industry, setIndustry] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);
  
  const createMutation = useCreateBrand();
  const { setCurrentBrandId } = useAppStore();

  const handleDomainChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value.trim();
    // Auto-clean http(s) if user pasted full URL
    val = val.replace(/^https?:\/\//i, '').replace(/\/.*$/, '');
    setDomain(val);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanName = name.trim();
    let cleanDomain = domain.trim().replace(/^https?:\/\//i, '').replace(/\/.*$/, '');
    if (!cleanName || !cleanDomain) return;

    try {
      const newBrand = await createMutation.mutateAsync({
        name: cleanName,
        domain: cleanDomain,
        industry: industry.trim() || undefined,
      });
      
      setCurrentBrandId(newBrand.id);
      setIsSuccess(true);
      setTimeout(() => {
        handleClose();
      }, 700);
    } catch (error) {
      // Error handled by react-query state
    }
  };

  const handleClose = () => {
    setName('');
    setDomain('');
    setIndustry('');
    setIsSuccess(false);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Add Monitored Brand">
      {isSuccess ? (
        <div className="py-8 flex flex-col items-center justify-center text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center">
            <CheckCircle2 size={28} />
          </div>
          <h3 className="text-base font-bold text-slate-900">Brand Added Successfully!</h3>
          <p className="text-sm text-slate-500">Setting as current active brand...</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5 flex items-center gap-1.5">
              <Building2 size={14} className="text-blue-600" /> Brand / Company Name *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Nike, Apple, Tesla"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full h-10 px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5 flex items-center gap-1.5">
              <Globe size={14} className="text-blue-600" /> Website Domain *
            </label>
            <div className="flex rounded-lg border border-slate-300 overflow-hidden bg-slate-50 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent focus-within:bg-white transition-all">
              <span className="inline-flex items-center px-3 text-xs font-mono text-slate-500 bg-slate-100 border-r border-slate-200 select-none">
                https://
              </span>
              <input
                type="text"
                required
                placeholder="nike.com"
                value={domain}
                onChange={handleDomainChange}
                className="flex-1 h-10 px-3 text-sm font-mono bg-transparent text-slate-900 placeholder-slate-400 focus:outline-none"
              />
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Enter root domain name (e.g. brand.com without path).</p>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5 flex items-center gap-1.5">
              <Tag size={14} className="text-blue-600" /> Industry / Sector (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. E-commerce, SaaS, Footwear"
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              className="w-full h-10 px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>

          {createMutation.isError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-start gap-2">
              <AlertCircle size={16} className="shrink-0 text-red-500 mt-0.5" />
              <span>Could not register brand. Please verify your domain and ensure your connection is active.</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
            <Button type="button" variant="ghost" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={!name.trim() || !domain.trim() || createMutation.isPending}
              isLoading={createMutation.isPending}
              className="gap-1.5 shadow-sm"
            >
              <Building2 size={16} />
              {createMutation.isPending ? 'Registering...' : 'Add Brand'}
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
};
