import { Routes, Route } from 'react-router-dom';
import { DashboardPage } from './pages/DashboardPage';
import { BrandDetailPage } from './pages/BrandDetailPage';
import { SeoAuditPage } from './pages/SeoAuditPage';
import { ProductsPage } from './pages/ProductsPage';
import { CompetitorsPage } from './pages/CompetitorsPage';
import { ChangesPage } from './pages/ChangesPage';
import { MentionsPage } from './pages/MentionsPage';
import { AdsPage } from './pages/AdsPage';
import { ReportsPage } from './pages/ReportsPage';

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/brands/:id" element={<BrandDetailPage />} />
      <Route path="/seo" element={<SeoAuditPage />} />
      <Route path="/products" element={<ProductsPage />} />
      <Route path="/competitors" element={<CompetitorsPage />} />
      <Route path="/changes" element={<ChangesPage />} />
      <Route path="/mentions" element={<MentionsPage />} />
      <Route path="/ads" element={<AdsPage />} />
      <Route path="/reports" element={<ReportsPage />} />
    </Routes>
  );
}
