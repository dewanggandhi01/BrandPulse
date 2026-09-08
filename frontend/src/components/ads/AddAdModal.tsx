import React, { useState } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Badge } from '../ui/Badge';
import { Spinner } from '../ui/Spinner';
import { useCreateAd, useParseAdPreview, type AdParsePreviewResult } from '../../api/queries/useAds';
import { Megaphone, Sparkles, AlertCircle } from 'lucide-react';

interface AddAdModalProps {
  isOpen: boolean;
  onClose: () => void;
  brandId: string;
}

export const AddAdModal: React.FC<AddAdModalProps> = ({
  isOpen,
  onClose,
  brandId,
}) => {
  const [platform, setPlatform] = useState('google');
  const [adFormat, setAdFormat] = useState('search');
  const [targetUrl, setTargetUrl] = useState('');
  const [firstSeen, setFirstSeen] = useState(
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [lastSeen, setLastSeen] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [adText, setAdText] = useState('');
  const [previewResult, setPreviewResult] = useState<AdParsePreviewResult | null>(null);

  const createMutation = useCreateAd(brandId);
  const parseMutation = useParseAdPreview();

  const handlePreview = async () => {
    if (!adText.trim()) return;
    try {
      const res = await parseMutation.mutateAsync({
        raw_text: adText.trim(),
        target_url: targetUrl.trim() || undefined,
        suggested_format: adFormat,
      });
      setPreviewResult(res);
    } catch {
      // Handled by react-query error state
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adText.trim()) return;

    await createMutation.mutateAsync({
      platform,
      ad_format: adFormat,
      target_url: targetUrl.trim() || undefined,
      first_seen: firstSeen || undefined,
      last_seen: lastSeen || undefined,
      ad_text: adText.trim(),
      data_source_tag: 'manual_ingest',
    });

    handleClose();
  };

  const handleClose = () => {
    setAdText('');
    setTargetUrl('');
    setPreviewResult(null);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Ingest Competitor Ad Creative"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Ad Network
            </label>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
            >
              <option value="google">Google Ads</option>
              <option value="meta">Meta (Facebook / IG)</option>
              <option value="linkedin">LinkedIn Ads</option>
              <option value="twitter">X / Twitter</option>
              <option value="tiktok">TikTok Ads</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Ad Format
            </label>
            <select
              value={adFormat}
              onChange={(e) => setAdFormat(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
            >
              <option value="search">Search Text Ad</option>
              <option value="display">Display Banner Ad</option>
              <option value="video">Video Ad</option>
              <option value="sponsored_feed">Sponsored Feed Post</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Input
            label="First Seen Date"
            type="date"
            value={firstSeen}
            onChange={(e) => setFirstSeen(e.target.value)}
          />
          <Input
            label="Last Seen Date"
            type="date"
            value={lastSeen}
            onChange={(e) => setLastSeen(e.target.value)}
          />
        </div>

        <Input
          label="Destination Landing Page URL"
          placeholder="https://competitor.com/landing?utm_source=google&utm_campaign=q3"
          value={targetUrl}
          onChange={(e) => setTargetUrl(e.target.value)}
        />

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
            Ad Copy & Headlines *
          </label>
          <textarea
            rows={4}
            required
            value={adText}
            onChange={(e) => {
              setAdText(e.target.value);
              setPreviewResult(null);
            }}
            placeholder="Headline - Subheadline&#10;Body copy highlighting value prop and CTA..."
            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Live Preview Button */}
        <div className="flex items-center justify-between pt-1">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handlePreview}
            disabled={!adText.trim() || parseMutation.isPending}
          >
            {parseMutation.isPending ? (
              <Spinner size="sm" className="mr-1.5" />
            ) : (
              <Sparkles className="w-3.5 h-3.5 mr-1.5 text-blue-400" />
            )}
            Preview Creative & Spend Tier
          </Button>

          {previewResult && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400">Estimated Tier:</span>
              <Badge variant={previewResult.is_evergreen ? 'success' : 'default'}>
                {previewResult.spend_tier}
              </Badge>
            </div>
          )}
        </div>

        {previewResult && (
          <div className="p-3 bg-slate-800/60 border border-slate-700 rounded-lg text-xs space-y-1 text-slate-300">
            <div>
              <span className="text-slate-500">Extracted Headline: </span>
              <span className="font-semibold text-slate-200">{previewResult.headline || 'None'}</span>
            </div>
            {previewResult.cta && (
              <div>
                <span className="text-slate-500">Detected CTA: </span>
                <span className="text-blue-400 font-medium">{previewResult.cta}</span>
              </div>
            )}
            {previewResult.landing_page_domain && (
              <div>
                <span className="text-slate-500">Domain: </span>
                <span>{previewResult.landing_page_domain}</span>
              </div>
            )}
          </div>
        )}

        {createMutation.isError && (
          <div className="p-3 bg-red-950/40 border border-red-800 rounded-lg text-xs text-red-300 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
            Failed to save ad creative. Please verify the input details.
          </div>
        )}

        <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
          <Button type="button" variant="ghost" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={!adText.trim() || createMutation.isPending}
          >
            {createMutation.isPending ? (
              <Spinner size="sm" className="mr-1.5" />
            ) : (
              <Megaphone className="w-4 h-4 mr-1.5" />
            )}
            Ingest Creative
          </Button>
        </div>
      </form>
    </Modal>
  );
};
