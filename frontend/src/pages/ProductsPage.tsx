import React, { useState, useEffect } from 'react';
import {
  Package,
  Search,
  DollarSign,
  TrendingUp,
  CheckCircle2,
  Play,
  ChevronLeft,
  ChevronRight,
  Globe,
  AlertCircle,
  CheckCircle,
  X,
} from 'lucide-react';
import { useGetBrands } from '@/api/queries/useBrands';
import { useGetProducts, useGetProductAnalytics, useExtractProducts } from '@/api/queries/useProducts';
import { useAppStore } from '@/stores/appStore';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/feedback/EmptyState';
import { ProductPriceHistoryModal } from '@/components/products/ProductPriceHistoryModal';
import { ScrapeJobModal } from '@/components/crawling/ScrapeJobModal';

export const ProductsPage: React.FC = () => {
  const { currentBrandId, setCurrentBrandId } = useAppStore();
  const { data: brands = [], isLoading: brandsLoading } = useGetBrands();

  // Synchronize store if not yet selected
  useEffect(() => {
    if (!currentBrandId && brands.length > 0) {
      setCurrentBrandId(brands[0].id);
    }
  }, [currentBrandId, brands, setCurrentBrandId]);

  const effectiveBrandId = currentBrandId || (brands.length > 0 ? brands[0].id : '');
  const selectedBrand = brands.find((b) => b.id === effectiveBrandId);

  // Filter and pagination state
  const [search, setSearch] = useState('');
  const [availability, setAvailability] = useState<string>('');
  const [orderBy, setOrderBy] = useState<'recent' | 'price_asc' | 'price_desc' | 'name_asc'>('recent');
  const [page, setPage] = useState(1);

  // Modals & Banners state
  const [historyProductId, setHistoryProductId] = useState<string | null>(null);
  const [isCrawlModalOpen, setIsCrawlModalOpen] = useState(false);
  const [bannerDismissed, setBannerDismissed] = useState(false);

  // Queries & Mutations
  const { data: productData, isLoading: productsLoading, error: productsError } = useGetProducts(
    effectiveBrandId,
    {
      page,
      size: 15,
      search: search || undefined,
      availability: availability || undefined,
      order_by: orderBy,
    }
  );

  const { data: analytics } = useGetProductAnalytics(effectiveBrandId);
  const extractMutation = useExtractProducts();

  const products = productData?.items || [];
  const totalPages = productData?.pages || 1;

  const handleExtract = () => {
    if (!effectiveBrandId) return;
    setBannerDismissed(false);
    extractMutation.mutate({ brandId: effectiveBrandId });
  };

  const getCurrencySymbol = (c?: string) => (c === 'INR' ? '₹' : c === 'EUR' ? '€' : c === 'GBP' ? '£' : c === 'USD' ? '$' : (c ? `${c} ` : '$'));
  const dominantSym = getCurrencySymbol(analytics?.currency);

  return (
    <div className="space-y-6 flex flex-col min-h-full pb-10">
      {/* Top Header & Brand Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Package className="text-brand-600" size={28} />
            Product & Pricing Intelligence
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Automated SKU discovery, catalog indexing, and time-series price fluctuation tracking.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {brands.length > 0 && (
            <select
              value={effectiveBrandId}
              onChange={(e) => {
                setCurrentBrandId(e.target.value);
                setPage(1);
                setBannerDismissed(false);
              }}
              aria-label="Select Monitored Brand"
              className="text-sm font-medium border border-slate-300 rounded-lg px-3 py-2 bg-white text-slate-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              {brands.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name} ({b.domain})
                </option>
              ))}
            </select>
          )}

          <Button
            variant="secondary"
            onClick={() => setIsCrawlModalOpen(true)}
            className="flex items-center gap-2"
          >
            <Globe size={16} />
            Crawl Website
          </Button>

          <Button
            variant="primary"
            onClick={handleExtract}
            disabled={!effectiveBrandId || extractMutation.isPending}
            className="flex items-center gap-2"
          >
            {extractMutation.isPending ? <Spinner size="sm" /> : <Play size={16} />}
            Extract Products
          </Button>
        </div>
      </div>

      {/* Extraction Notification Banners */}
      {extractMutation.isSuccess && !bannerDismissed && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-sm flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-3">
            <CheckCircle size={20} className="text-emerald-600 shrink-0" />
            <div>
              <div className="font-semibold text-emerald-950">Catalog Extraction Complete!</div>
              <div className="text-emerald-800 text-xs mt-0.5">
                Discovered <strong>{extractMutation.data.total_extracted}</strong> products ({extractMutation.data.new_products} newly added, {extractMutation.data.updated_products} updated, {extractMutation.data.price_changes} price shifts recorded).
              </div>
            </div>
          </div>
          <button
            onClick={() => setBannerDismissed(true)}
            className="text-emerald-600 hover:text-emerald-800 p-1 rounded-md transition-colors"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {extractMutation.isError && !bannerDismissed && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-900 text-sm flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-3">
            <AlertCircle size={20} className="text-red-600 shrink-0" />
            <div>
              <div className="font-semibold text-red-950">Extraction Alert</div>
              <div className="text-red-800 text-xs mt-0.5">
                {(extractMutation.error as any)?.response?.data?.detail || "No crawled snapshots found for this brand. Click 'Crawl Website' to scrape catalog pages first."}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsCrawlModalOpen(true)}
              className="text-xs bg-white text-red-800 border-red-200"
            >
              Crawl Website
            </Button>
            <button
              onClick={() => setBannerDismissed(true)}
              className="text-red-600 hover:text-red-800 p-1 rounded-md transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      {brandsLoading ? (
        <div className="py-20 flex justify-center">
          <Spinner size="lg" />
        </div>
      ) : brands.length === 0 ? (
        <EmptyState
          icon={<Package size={48} />}
          title="No Monitored Brands"
          description="Create your first brand in the Brands section before tracking products and prices."
        />
      ) : (
        <>
          {/* KPI Analytics Strip */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="p-4 bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Catalog Size</span>
                <span className="p-2 rounded-lg bg-blue-50 text-blue-600">
                  <Package size={18} />
                </span>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 tnum">
                  {analytics?.total_products ?? 0}
                </span>
                <span className="text-xs text-slate-500">tracked items</span>
              </div>
            </Card>

            <Card className="p-4 bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Average Price</span>
                <span className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
                  <DollarSign size={18} />
                </span>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 tnum">
                  {analytics?.avg_price != null ? `${dominantSym}${analytics.avg_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
                </span>
                {analytics?.min_price != null && analytics?.max_price != null && (
                  <span className="text-xs text-slate-400 tnum">
                    ({dominantSym}{analytics.min_price.toLocaleString(undefined, { maximumFractionDigits: 0 })} - {dominantSym}{analytics.max_price.toLocaleString(undefined, { maximumFractionDigits: 0 })})
                  </span>
                )}
              </div>
            </Card>

            <Card className="p-4 bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">In-Stock Rate</span>
                <span className="p-2 rounded-lg bg-amber-50 text-amber-600">
                  <CheckCircle2 size={18} />
                </span>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 tnum">
                  {analytics && analytics.total_products > 0
                    ? `${Math.round((analytics.in_stock_count / analytics.total_products) * 100)}%`
                    : '—'}
                </span>
                <span className="text-xs text-slate-500">
                  {analytics?.in_stock_count ?? 0} in stock
                </span>
              </div>
            </Card>

            <Card className="p-4 bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Price Shifts</span>
                <span className="p-2 rounded-lg bg-purple-50 text-purple-600">
                  <TrendingUp size={18} />
                </span>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 tnum">
                  {analytics?.price_changes_count ?? 0}
                </span>
                <span className="text-xs text-slate-500">history events</span>
              </div>
            </Card>
          </div>

          {/* Filter and Search Bar */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
            <div className="relative flex-1 max-w-md">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                placeholder="Search products by title or SKU..."
                className="w-full pl-9 pr-3 py-1.5 text-sm border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <div className="flex bg-slate-100 p-0.5 rounded-lg text-xs font-medium text-slate-600">
                <button
                  onClick={() => {
                    setAvailability('');
                    setPage(1);
                  }}
                  className={`px-3 py-1.5 rounded-md transition-colors ${
                    availability === '' ? 'bg-white shadow text-slate-900 font-semibold' : 'hover:text-slate-900'
                  }`}
                >
                  All Status
                </button>
                <button
                  onClick={() => {
                    setAvailability('InStock');
                    setPage(1);
                  }}
                  className={`px-3 py-1.5 rounded-md transition-colors ${
                    availability === 'InStock' ? 'bg-white shadow text-emerald-700 font-semibold' : 'hover:text-slate-900'
                  }`}
                >
                  In Stock
                </button>
                <button
                  onClick={() => {
                    setAvailability('OutOfStock');
                    setPage(1);
                  }}
                  className={`px-3 py-1.5 rounded-md transition-colors ${
                    availability === 'OutOfStock' ? 'bg-white shadow text-red-700 font-semibold' : 'hover:text-slate-900'
                  }`}
                >
                  Out of Stock
                </button>
              </div>

              <select
                value={orderBy}
                onChange={(e) => {
                  setOrderBy(e.target.value as any);
                  setPage(1);
                }}
                aria-label="Order by"
                className="text-xs font-medium border border-slate-300 rounded-lg px-2.5 py-2 bg-white text-slate-700 shadow-sm focus:outline-none"
              >
                <option value="recent">Recently Added</option>
                <option value="price_asc">Price: Low to High</option>
                <option value="price_desc">Price: High to Low</option>
                <option value="name_asc">Name: A to Z</option>
              </select>
            </div>
          </div>

          {/* Product Catalog List */}
          {productsLoading ? (
            <div className="py-24 flex justify-center">
              <Spinner size="lg" />
            </div>
          ) : productsError ? (
            <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
              Failed to load products for this brand.
            </div>
          ) : products.length === 0 ? (
            <EmptyState
              icon={<Package size={48} />}
              title="No Products Extracted Yet"
              description="Click 'Extract Products' above or run a crawl on this brand to discover products, SKUs, and pricing automatically."
              actionLabel={extractMutation.isPending ? "Extracting..." : "Extract Products Now"}
              onAction={handleExtract}
            />
          ) : (
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    <tr>
                      <th className="px-4 py-3">Product Name & SKU</th>
                      <th className="px-4 py-3">Price</th>
                      <th className="px-4 py-3">Stock Status</th>
                      <th className="px-4 py-3">Strategy</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {products.map((p) => (
                      <tr
                        key={p.id}
                        onClick={() => setHistoryProductId(p.id)}
                        className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            {p.image_url ? (
                              <img
                                src={p.image_url}
                                alt={p.name}
                                className="w-10 h-10 object-cover rounded-md border border-slate-200 shrink-0 bg-slate-50"
                                onError={(e) => {
                                  (e.target as HTMLElement).style.display = 'none';
                                }}
                              />
                            ) : (
                              <div className="w-10 h-10 rounded-md bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-400 shrink-0">
                                <Package size={18} />
                              </div>
                            )}
                            <div>
                              <div className="font-medium text-slate-900 line-clamp-1">{p.name}</div>
                              <div className="text-xs text-slate-400 font-mono mt-0.5">
                                {p.sku ? `SKU: ${p.sku}` : 'SKU: Auto-assigned'}
                              </div>
                            </div>
                          </div>
                        </td>

                        <td className="px-4 py-3 font-semibold text-slate-900 tnum">
                          {p.current_price != null ? `${getCurrencySymbol(p.currency)}${Number(p.current_price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
                        </td>

                        <td className="px-4 py-3">
                          <Badge variant={p.availability === 'InStock' ? 'success' : 'critical'}>
                            {p.availability || 'InStock'}
                          </Badge>
                        </td>

                        <td className="px-4 py-3">
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono bg-slate-100 text-slate-600">
                            {p.data_source_tag || 'scraped'}
                          </span>
                        </td>

                        <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => setHistoryProductId(p.id)}
                            className="text-xs flex items-center gap-1.5"
                          >
                            <TrendingUp size={13} className="text-slate-400" />
                            Price Trend
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200 bg-slate-50 text-xs text-slate-500">
                  <div>
                    Page <span className="font-semibold text-slate-800">{page}</span> of{' '}
                    <span className="font-semibold text-slate-800">{totalPages}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page <= 1}
                    >
                      <ChevronLeft size={14} /> Previous
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page >= totalPages}
                    >
                      Next <ChevronRight size={14} />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Interactive Price History Modal */}
      <ProductPriceHistoryModal
        productId={historyProductId}
        isOpen={!!historyProductId}
        onClose={() => setHistoryProductId(null)}
      />

      {/* Scrape / Crawl Modal */}
      <ScrapeJobModal
        isOpen={isCrawlModalOpen}
        onClose={() => setIsCrawlModalOpen(false)}
        brandId={effectiveBrandId}
        defaultDomain={selectedBrand?.domain || ''}
      />
    </div>
  );
};
