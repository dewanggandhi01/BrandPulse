import React from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { TrendingDown, TrendingUp, Calendar, Tag } from 'lucide-react';
import { useGetProductDetail } from '@/api/queries/useProducts';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { Modal } from '@/components/ui/Modal';

interface ProductPriceHistoryModalProps {
  productId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

export const ProductPriceHistoryModal: React.FC<ProductPriceHistoryModalProps> = ({
  productId,
  isOpen,
  onClose,
}) => {
  const { data: product, isLoading, error } = useGetProductDetail(productId || undefined);

  if (!isOpen || !productId) return null;

  const history = product?.price_history || [];

  // Format data for Recharts
  const chartData = history.map((item) => ({
    rawDate: item.captured_at,
    date: new Date(item.captured_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
    price: Number(item.price),
    currency: item.currency,
  }));

  const getSymbol = (c?: string) => (c === 'INR' ? '₹' : c === 'EUR' ? '€' : c === 'GBP' ? '£' : c === 'USD' ? '$' : (c ? `${c} ` : '$'));
  const sym = getSymbol(product?.currency);

  const minPrice = chartData.length > 0 ? Math.min(...chartData.map((d) => d.price)) : 0;
  const maxPrice = chartData.length > 0 ? Math.max(...chartData.map((d) => d.price)) : 0;

  const modalTitle = (
    <div>
      <div className="flex items-center gap-2 mb-0.5">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Price Intelligence</span>
        {product?.sku && (
          <span className="text-xs font-mono bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
            SKU: {product.sku}
          </span>
        )}
      </div>
      <span className="text-lg font-bold text-slate-900">
        {product?.name || 'Loading product...'}
      </span>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={modalTitle}
      size="3xl"
      isLoading={isLoading && !product}
    >
      <div className="space-y-6">
          {isLoading && (
            <div className="py-16 flex flex-col items-center justify-center text-slate-400">
              <Spinner size="lg" />
              <p className="mt-3 text-sm">Loading price history...</p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
              Failed to load price history for this product.
            </div>
          )}

          {product && (
            <>
              {/* Snapshot Metric Strip */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                  <div className="text-xs text-slate-500 font-medium">Current Price</div>
                  <div className="text-xl font-bold text-slate-900 tnum mt-0.5">
                    {product.current_price != null ? `${sym}${Number(product.current_price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : 'N/A'}
                  </div>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                  <div className="text-xs text-slate-500 font-medium">Historical Low</div>
                  <div className="text-xl font-bold text-emerald-600 tnum mt-0.5">
                    {minPrice > 0 ? `${sym}${minPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : 'N/A'}
                  </div>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                  <div className="text-xs text-slate-500 font-medium">Historical High</div>
                  <div className="text-xl font-bold text-slate-700 tnum mt-0.5">
                    {maxPrice > 0 ? `${sym}${maxPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : 'N/A'}
                  </div>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                  <div className="text-xs text-slate-500 font-medium">Availability</div>
                  <div className="mt-1">
                    <Badge variant={product.availability === 'InStock' ? 'success' : 'critical'}>
                      {product.availability || 'InStock'}
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Price Timeline Chart */}
              <div className="border border-slate-200 rounded-xl p-4 bg-slate-50/50">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-1.5">
                    <Calendar size={16} className="text-slate-400" />
                    Price Trend Over Time
                  </h3>
                  <span className="text-xs text-slate-500">
                    {history.length} price point{history.length === 1 ? '' : 's'} recorded
                  </span>
                </div>

                {chartData.length > 1 ? (
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 25 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                        <XAxis
                          dataKey="date"
                          stroke="#94A3B8"
                          fontSize={11}
                          tickLine={false}
                          angle={-20}
                          textAnchor="end"
                        />
                        <YAxis
                          stroke="#94A3B8"
                          fontSize={11}
                          tickLine={false}
                          domain={['auto', 'auto']}
                          tickFormatter={(val) => `${sym}${val}`}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#0F172A',
                            borderColor: '#1E293B',
                            borderRadius: '8px',
                            color: '#F8FAFC',
                            fontSize: '12px',
                          }}
                          formatter={(value: any) => [`${sym}${Number(value).toFixed(2)}`, 'Price']}
                        />
                        <Line
                          type="monotone"
                          dataKey="price"
                          stroke="#2563EB"
                          strokeWidth={2.5}
                          dot={{ r: 4, fill: '#2563EB' }}
                          activeDot={{ r: 6, fill: '#1D4ED8' }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="py-12 text-center text-slate-400 text-sm">
                    <Tag size={28} className="mx-auto mb-2 opacity-50" />
                    <p className="font-medium text-slate-600">Single historical price captured</p>
                    <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                      Initial price recorded at {sym}{Number(product.current_price).toFixed(2)} ({product.currency}). Future crawl runs will generate time-series trend lines automatically.
                    </p>
                  </div>
                )}
              </div>

              {/* Price Change Audit Log Table */}
              <div>
                <h3 className="text-sm font-semibold text-slate-800 mb-3">Price Point History</h3>
                <div className="border border-slate-200 rounded-lg overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-100 text-slate-600 font-semibold uppercase tracking-wider">
                      <tr>
                        <th className="px-3 py-2.5">Captured At</th>
                        <th className="px-3 py-2.5">Recorded Price</th>
                        <th className="px-3 py-2.5">Delta vs Previous</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {history.map((hist, idx) => {
                        const prev = idx > 0 ? Number(history[idx - 1].price) : null;
                        const current = Number(hist.price);
                        const diff = prev != null ? current - prev : 0;
                        const diffPct = prev != null && prev > 0 ? (diff / prev) * 100 : 0;
                        const rowSym = getSymbol(hist.currency);

                        return (
                          <tr key={hist.id} className="hover:bg-slate-50">
                            <td className="px-3 py-2.5 text-slate-700 font-mono">
                              {new Date(hist.captured_at).toLocaleString()}
                            </td>
                            <td className="px-3 py-2.5 font-semibold text-slate-900 tnum">
                              {rowSym}{current.toFixed(2)}
                            </td>
                            <td className="px-3 py-2.5 tnum">
                              {prev == null ? (
                                <span className="text-slate-400">Baseline Price</span>
                              ) : diff > 0 ? (
                                <span className="text-red-600 font-medium flex items-center gap-1">
                                  <TrendingUp size={12} /> +{rowSym}{diff.toFixed(2)} (+{diffPct.toFixed(1)}%)
                                </span>
                              ) : diff < 0 ? (
                                <span className="text-emerald-600 font-medium flex items-center gap-1">
                                  <TrendingDown size={12} /> -{rowSym}{Math.abs(diff).toFixed(2)} ({diffPct.toFixed(1)}%)
                                </span>
                              ) : (
                                <span className="text-slate-400">Unchanged</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Provenance Footer */}
              <div className="text-xs text-slate-400 flex items-center justify-between pt-2">
                <span>Data Source: <code className="text-slate-600 font-mono">{product.data_source_tag || 'scraped'}</code></span>
                <span>Product ID: <code className="text-slate-600 font-mono">{product.id.slice(0, 8)}...</code></span>
              </div>
            </>
          )}
      </div>
    </Modal>
  );
};
