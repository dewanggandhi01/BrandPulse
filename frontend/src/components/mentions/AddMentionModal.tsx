import React, { useState } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Badge } from '../ui/Badge';
import { Spinner } from '../ui/Spinner';
import { useCreateMention, useAnalyzeText, type AnalyzeTextResult } from '../../api/queries/useMentions';
import { MessageSquare, Sparkles, AlertCircle } from 'lucide-react';

interface AddMentionModalProps {
  isOpen: boolean;
  onClose: () => void;
  brandId: string;
}

export const AddMentionModal: React.FC<AddMentionModalProps> = ({
  isOpen,
  onClose,
  brandId,
}) => {
  const [source, setSource] = useState('twitter');
  const [author, setAuthor] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [content, setContent] = useState('');
  const [adhocResult, setAdhocResult] = useState<AnalyzeTextResult | null>(null);

  const createMutation = useCreateMention(brandId);
  const analyzeMutation = useAnalyzeText();

  const handleAnalyzePreview = async () => {
    if (!content.trim()) return;
    try {
      const result = await analyzeMutation.mutateAsync({ text: content.trim() });
      setAdhocResult(result);
    } catch {
      // Handled by react-query error state
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    await createMutation.mutateAsync({
      source,
      author: author.trim() || undefined,
      source_url: sourceUrl.trim() || undefined,
      content: content.trim(),
    });

    handleClose();
  };

  const handleClose = () => {
    setContent('');
    setAuthor('');
    setSourceUrl('');
    setAdhocResult(null);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Add Brand Mention or Customer Review"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
            Platform / Source
          </label>
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
          >
            <option value="twitter">Twitter / X</option>
            <option value="reddit">Reddit</option>
            <option value="g2">G2 Reviews</option>
            <option value="trustpilot">Trustpilot</option>
            <option value="news">News Article</option>
            <option value="blog">Blog Post</option>
            <option value="web">Web Forum</option>
          </select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Input
            label="Author / Handle"
            placeholder="@techuser or John D."
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
          />
          <Input
            label="Source URL (Optional)"
            placeholder="https://twitter.com/..."
            value={sourceUrl}
            onChange={(e) => setSourceUrl(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
            Mention Content / Review Text *
          </label>
          <textarea
            rows={4}
            required
            value={content}
            onChange={(e) => {
              setContent(e.target.value);
              setAdhocResult(null);
            }}
            placeholder="Paste the tweet, Reddit comment, or customer review text here..."
            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Live Sentiment Analysis Preview */}
        <div className="flex items-center justify-between pt-1">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleAnalyzePreview}
            disabled={!content.trim() || analyzeMutation.isPending}
          >
            {analyzeMutation.isPending ? (
              <Spinner size="sm" className="mr-1.5" />
            ) : (
              <Sparkles className="w-3.5 h-3.5 mr-1.5 text-blue-400" />
            )}
            Preview NLP Sentiment
          </Button>

          {adhocResult && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400">Detected:</span>
              <Badge
                variant={
                  adhocResult.label === 'positive'
                    ? 'success'
                    : adhocResult.label === 'negative'
                    ? 'critical'
                    : 'default'
                }
              >
                {adhocResult.label.toUpperCase()} ({(adhocResult.compound_score * 100).toFixed(0)}% score)
              </Badge>
            </div>
          )}
        </div>

        {createMutation.isError && (
          <div className="p-3 bg-red-950/40 border border-red-800 rounded-lg text-xs text-red-300 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
            Failed to save mention. Please check your input and try again.
          </div>
        )}

        <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
          <Button type="button" variant="ghost" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={!content.trim() || createMutation.isPending}
          >
            {createMutation.isPending ? (
              <Spinner size="sm" className="mr-1.5" />
            ) : (
              <MessageSquare className="w-4 h-4 mr-1.5" />
            )}
            Ingest & Analyze
          </Button>
        </div>
      </form>
    </Modal>
  );
};
