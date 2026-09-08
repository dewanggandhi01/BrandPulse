export interface Brand {
  id: string;
  name: string;
  domain: string;
  industry?: string;
  metadata_info?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface BrandUrl {
  id: string;
  brand_id: string;
  url: string;
  url_type?: string;
  is_active: boolean;
}

export interface ScrapeJob {
  id: string;
  brand_id: string;
  job_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  config?: Record<string, any>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface Snapshot {
  id: string;
  brand_url_id: string;
  scrape_job_id?: string;
  content_hash: string;
  html_size: number;
  status_code: number;
  headers?: Record<string, string>;
  captured_at: string;
  html_content?: string;
}

export interface SeoAudit {
  id: string;
  snapshot_id: string;
  total_score: number;
  technical_scores?: Record<string, any>;
  content_scores?: Record<string, any>;
  structured_data_scores?: Record<string, any>;
  link_scores?: Record<string, any>;
  issues?: Record<string, any>;
  audited_at: string;
}

export interface Product {
  id: string;
  snapshot_id?: string | null;
  brand_id: string;
  name: string;
  sku?: string | null;
  current_price?: number | null;
  currency?: string;
  availability?: string;
  image_url?: string | null;
  attributes?: Record<string, any>;
  data_source_tag?: string;
}

export interface PriceHistory {
  id: string;
  product_id: string;
  price: number;
  currency: string;
  captured_at: string;
}

export interface ProductDetail extends Product {
  price_history: PriceHistory[];
}

export interface ProductAnalyticsSummary {
  total_products: number;
  in_stock_count: number;
  out_of_stock_count: number;
  avg_price?: number | null;
  min_price?: number | null;
  max_price?: number | null;
  currency: string;
  price_changes_count: number;
}

export interface ChangeChunk {
  type: 'unchanged' | 'added' | 'removed' | 'modified';
  content?: string;
  old_content?: string;
  new_content?: string;
}

export interface DiffDetails {
  additions_count: number;
  deletions_count: number;
  modifications_count: number;
  total_changes: number;
  word_delta: number;
  diff_chunks: ChangeChunk[];
  unified_diff: string;
}

export interface ChangeEvent {
  id: string;
  snapshot_id: string;
  previous_snapshot_id?: string;
  change_type: string;
  similarity_ratio?: number;
  diff_details?: DiffDetails;
  ai_summary?: string;
  created_at: string;
  additions_count?: number;
  deletions_count?: number;
  total_changes?: number;
}

export interface ChangeAnalyticsSummary {
  total_changes: number;
  pricing_changes_count: number;
  messaging_pivots_count: number;
  layout_overhauls_count: number;
  seo_changes_count: number;
  minor_copy_count: number;
  avg_similarity?: number | null;
}

export interface ChangeScanResponse {
  message: string;
  urls_scanned: number;
  snapshots_evaluated: number;
  changes_detected: number;
  total_events: number;
}


export interface Mention {
  id: string;
  brand_id: string;
  source: string;
  source_url?: string;
  content: string;
  author?: string;
  published_at?: string;
  created_at: string;
  sentiment?: Sentiment | null;
}

export interface Sentiment {
  id: string;
  mention_id: string;
  label: 'positive' | 'neutral' | 'negative';
  positive_score?: number;
  negative_score?: number;
  neutral_score?: number;
  compound_score?: number;
  model_version?: string;
  created_at: string;
}

export interface TopicStat {
  topic: string;
  frequency: number;
  sentiment_label: 'positive' | 'neutral' | 'negative';
  average_compound: number;
}

export interface SourceStat {
  source: string;
  count: number;
  positive: number;
  negative: number;
  neutral: number;
  avg_compound: number;
}

export interface ReputationAnalytics {
  brand_id: string;
  total_mentions: number;
  net_sentiment_score: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  positive_pct: number;
  negative_pct: number;
  neutral_pct: number;
  sources_breakdown: SourceStat[];
  top_topics: TopicStat[];
}

export interface AdIntel {
  id: string;
  brand_id: string;
  platform: string;
  ad_text?: string;
  ad_format?: string;
  target_url?: string;
  first_seen?: string;
  last_seen?: string;
  targeting_info?: Record<string, any>;
  data_source_tag?: string;
  created_at: string;
  longevity_days?: number;
  spend_tier?: string;
  is_evergreen?: boolean;
  headline?: string;
  cta?: string;
}

export interface PlatformShare {
  platform: string;
  count: number;
  percentage: number;
}

export interface FormatShare {
  format: string;
  count: number;
  percentage: number;
}

export interface SpendTierShare {
  tier: string;
  count: number;
  percentage: number;
}

export interface TopItem {
  name: string;
  count: number;
}

export interface AdIntelAnalytics {
  brand_id: string;
  total_ads: number;
  evergreen_count: number;
  platform_distribution: PlatformShare[];
  format_distribution: FormatShare[];
  spend_tier_distribution: SpendTierShare[];
  top_ctas: TopItem[];
  top_landing_domains: TopItem[];
  estimated_monthly_spend_range: string;
}

export interface SwotItem {
  category: 'strength' | 'weakness' | 'opportunity' | 'threat';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
}

export interface ExecutivePillarScores {
  seo: number;
  pricing: number;
  sentiment: number;
  agility: number;
  advertising: number;
}

export interface ReportContent {
  health_score: number;
  risk_level: string;
  pillar_scores: ExecutivePillarScores;
  kpi_highlights: Record<string, any>;
  swot: SwotItem[];
  recommendations: string[];
}

export interface Report {
  id: string;
  brand_id: string;
  report_type: string;
  content?: ReportContent;
  ai_narrative?: string;
  generated_at?: string;
  created_at?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface CompetitorItem {
  id: string;
  brand_id: string;
  competitor_brand_id: string;
  competitor_name: string;
  competitor_domain: string;
  industry?: string | null;
  created_at: string;
}

export interface BrandBenchmarkProfile {
  brand_id: string;
  brand_name: string;
  domain: string;
  seo_total_score?: number | null;
  technical_score?: number | null;
  content_score?: number | null;
  structured_data_score?: number | null;
  link_score?: number | null;
  product_count: number;
  avg_price?: number | null;
  min_price?: number | null;
  max_price?: number | null;
  currency?: string | null;
  in_stock_rate?: number | null;
}

export interface CompetitorComparisonMatrix {
  target_brand: BrandBenchmarkProfile;
  competitors: BrandBenchmarkProfile[];
  price_index?: number | null;
  radar_data: Array<{
    pillar: string;
    [brandName: string]: any;
  }>;
}

export interface CompetitorSyncResponse {
  message: string;
  synced_brands: number;
  jobs_dispatched: number;
  job_ids: string[];
}

