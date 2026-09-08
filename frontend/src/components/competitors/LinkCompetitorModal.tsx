import React, { useState } from 'react';
import { Plus, Building2, Globe, Tag, CheckCircle2 } from 'lucide-react';
import { useGetBrands, useCreateBrand } from '@/api/queries/useBrands';
import { useGetLinkedCompetitors, useLinkCompetitor } from '@/api/queries/useCompetitors';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';

interface LinkCompetitorModalProps {
  brandId: string;
  isOpen: boolean;
  onClose: () => void;
}

export const LinkCompetitorModal: React.FC<LinkCompetitorModalProps> = ({
  brandId,
  isOpen,
  onClose,
}) => {
  const { data: allBrands = [] } = useGetBrands();
  const { data: linked = [] } = useGetLinkedCompetitors(brandId);
  const linkMutation = useLinkCompetitor();
  const createBrandMutation = useCreateBrand();

  const [mode, setMode] = useState<'existing' | 'new'>('existing');
  const [selectedCompetitorId, setSelectedCompetitorId] = useState('');
  
  // New brand state
  const [newName, setNewName] = useState('');
  const [newDomain, setNewDomain] = useState('');
  const [newIndustry, setNewIndustry] = useState('');

  const [errorMsg, setErrorMsg] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);

  // Filter out current brand and already linked competitors
  const linkedIds = new Set(linked.map((l) => l.competitor_brand_id));
  const availableBrands = allBrands.filter(
    (b) => b.id !== brandId && !linkedIds.has(b.id)
  );

  const handleDomainChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value.trim();
    val = val.replace(/^https?:\/\//i, '').replace(/\/.*$/, '');
    setNewDomain(val);
  };

  const handleClose = () => {
    setSelectedCompetitorId('');
    setNewName('');
    setNewDomain('');
    setNewIndustry('');
    setErrorMsg('');
    setIsSuccess(false);
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (mode === 'existing') {
      if (!selectedCompetitorId) {
        setErrorMsg('Please select an existing brand to link as a competitor.');
        return;
      }

      linkMutation.mutate(
        { brandId, competitorBrandId: selectedCompetitorId },
        {
          onSuccess: () => {
            setIsSuccess(true);
            setTimeout(handleClose, 600);
          },
          onError: (err: any) => {
            setErrorMsg(err.response?.data?.detail || 'Failed to link competitor.');
          },
        }
      );
    } else {
      // Create new brand and link
      const cleanName = newName.trim();
      let cleanDomain = newDomain.trim().replace(/^https?:\/\//i, '').replace(/\/.*$/, '');
      if (!cleanName || !cleanDomain) {
        setErrorMsg('Please enter both competitor brand name and valid domain.');
        return;
      }

      try {
        const createdBrand = await createBrandMutation.mutateAsync({
          name: cleanName,
          domain: cleanDomain,
          industry: newIndustry.trim() || undefined,
        });

        await linkMutation.mutateAsync({
          brandId,
          competitorBrandId: createdBrand.id,
        });

        setIsSuccess(true);
        setTimeout(handleClose, 600);
      } catch (err: any) {
        setErrorMsg(err.response?.data?.detail || err.message || 'Failed to create and link competitor.');
      }
    }
  };

  const isPending = linkMutation.isPending || createBrandMutation.isPending;

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Link Competitor Brand" size="md">
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-xs text-slate-500">
          Add a market rival to activate side-by-side benchmarking, multi-brand radar overlays, and price parity tracking.
        </p>

        {/* Tab switch */}
        <div className="flex rounded-lg bg-slate-100 p-1 text-xs font-semibold">
          <button
            type="button"
            onClick={() => setMode('existing')}
            className={`flex-1 py-1.5 rounded-md transition-all ${
              mode === 'existing'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Select Existing Brand ({availableBrands.length})
          </button>
          <button
            type="button"
            onClick={() => setMode('new')}
            className={`flex-1 py-1.5 rounded-md transition-all ${
              mode === 'new'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            + Create & Link New Brand
          </button>
        </div>

        {errorMsg && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs">
            {errorMsg}
          </div>
        )}

        {isSuccess && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-700 text-xs flex items-center gap-2">
            <CheckCircle2 size={16} />
            Competitor linked successfully! Updating benchmark radar...
          </div>
        )}

        {mode === 'existing' ? (
          availableBrands.length === 0 ? (
            <div className="py-6 text-center text-slate-500 text-sm">
              <p className="font-medium">No other existing brands available.</p>
              <p className="text-xs text-slate-400 mt-1">
                Switch to "+ Create & Link New Brand" above to register and track a new rival directly.
              </p>
            </div>
          ) : (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5 uppercase tracking-wider">
                Select Existing Brand
              </label>
              <select
                value={selectedCompetitorId}
                onChange={(e) => setSelectedCompetitorId(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 bg-white text-slate-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="">-- Choose a rival brand --</option>
                {availableBrands.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name} ({b.domain}) {b.industry ? `• ${b.industry}` : ''}
                  </option>
                ))}
              </select>
            </div>
          )
        ) : (
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1 uppercase tracking-wider">
                Competitor Name *
              </label>
              <div className="relative">
                <Building2 size={16} className="absolute left-3 top-3 text-slate-400" />
                <input
                  type="text"
                  required
                  placeholder="e.g., Puma, Reeboks, Sony"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1 uppercase tracking-wider">
                Website Domain *
              </label>
              <div className="relative">
                <Globe size={16} className="absolute left-3 top-3 text-slate-400" />
                <input
                  type="text"
                  required
                  placeholder="e.g., puma.com"
                  value={newDomain}
                  onChange={handleDomainChange}
                  className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 font-mono"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1 uppercase tracking-wider">
                Industry / Category (Optional)
              </label>
              <div className="relative">
                <Tag size={16} className="absolute left-3 top-3 text-slate-400" />
                <input
                  type="text"
                  placeholder="e.g., Footwear, Consumer Electronics"
                  value={newIndustry}
                  onChange={(e) => setNewIndustry(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>
          </div>
        )}

        <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
          <Button variant="secondary" size="sm" type="button" onClick={handleClose} disabled={isPending}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            type="submit"
            disabled={
              isPending ||
              (mode === 'existing' && (!selectedCompetitorId || availableBrands.length === 0)) ||
              (mode === 'new' && (!newName.trim() || !newDomain.trim()))
            }
            className="flex items-center gap-1.5"
          >
            {isPending ? <Spinner size="sm" /> : <Plus size={16} />}
            {mode === 'existing' ? 'Link Competitor' : 'Create & Link'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
