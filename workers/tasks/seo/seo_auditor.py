from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID
import structlog
from sqlalchemy import select

from workers.celery_app import app
from workers.seo import SeoAuditEngine
from app.database import async_session_maker
from app.models.snapshot import Snapshot
from app.models.seo_audit import SeoAudit
from app.models.brand import BrandUrl

logger = structlog.get_logger()

async def _async_audit_snapshot(snapshot_id_str: str, target_url: Optional[str] = None) -> Dict[str, Any]:
    snapshot_id = UUID(snapshot_id_str)
    logger.info("Executing SEO audit for snapshot", snapshot_id=str(snapshot_id))

    async with async_session_maker() as session:
        snapshot = await session.get(Snapshot, snapshot_id)
        if not snapshot:
            logger.error("Snapshot not found for SEO audit", snapshot_id=str(snapshot_id))
            raise ValueError(f"Snapshot {snapshot_id} not found")

        # Resolve URL
        url = target_url
        if not url and snapshot.brand_url_id:
            brand_url = await session.get(BrandUrl, snapshot.brand_url_id)
            if brand_url:
                url = brand_url.url
        url = url or "https://unknown.com"

        # Execute 4-pillar audit
        html_content = snapshot.html_path or ""
        audit_result = SeoAuditEngine.audit(html_content, url)

        # Create SeoAudit record
        seo_audit = SeoAudit(
            snapshot_id=snapshot.id,
            total_score=audit_result["total_score"],
            technical_scores=audit_result["technical_scores"],
            content_scores=audit_result["content_scores"],
            structured_data_scores=audit_result["structured_data_scores"],
            link_scores=audit_result["link_scores"],
            issues=audit_result["issues"],
            audited_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        session.add(seo_audit)
        await session.commit()
        await session.refresh(seo_audit)

        logger.info(
            "SEO audit completed successfully",
            snapshot_id=str(snapshot_id),
            audit_id=str(seo_audit.id),
            total_score=seo_audit.total_score,
            issues=len(audit_result["issues"])
        )

        return {
            "audit_id": str(seo_audit.id),
            "snapshot_id": str(snapshot.id),
            "total_score": seo_audit.total_score,
            "technical_score": audit_result["technical_scores"]["score"],
            "content_score": audit_result["content_scores"]["score"],
            "structured_data_score": audit_result["structured_data_scores"]["score"],
            "link_score": audit_result["link_scores"]["score"],
            "issues_count": len(audit_result["issues"]),
            "audited_at": seo_audit.audited_at.isoformat()
        }

@app.task(name="workers.tasks.seo.audit_snapshot_seo", bind=True)
def audit_snapshot_seo(self, snapshot_id: str, target_url: Optional[str] = None) -> Dict[str, Any]:
    """Celery task running 4-pillar SEO audit on a captured HTML snapshot."""
    try:
        return asyncio.run(_async_audit_snapshot(snapshot_id, target_url))
    except Exception as exc:
        logger.exception("SEO audit task failed", snapshot_id=snapshot_id, exc=str(exc))
        raise self.retry(exc=exc, countdown=5, max_retries=2)
