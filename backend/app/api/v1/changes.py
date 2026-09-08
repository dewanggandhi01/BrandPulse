from __future__ import annotations
import uuid
from typing import Any, Optional
from datetime import datetime, timezone
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.api.deps import get_db
from app.models.brand import Brand, BrandUrl
from app.models.snapshot import Snapshot
from app.models.change_event import ChangeEvent
from app.schemas.change_event import (
    ChangeEventRead,
    ChangeEventDetailRead,
    ChangeEventListResponse,
    ChangeComparisonRequest,
    ChangeAnalyticsSummary,
    ChangeScanResponse
)
from workers.diffing.html_cleaner import HtmlCleaner
from workers.diffing.comparator import SnapshotComparator
from workers.diffing.classifier import ChangeClassifier

logger = structlog.get_logger()
router = APIRouter()

def _format_change_event(event: ChangeEvent) -> ChangeEventRead:
    details = event.diff_details or {}
    return ChangeEventRead(
        id=event.id,
        snapshot_id=event.snapshot_id,
        previous_snapshot_id=event.previous_snapshot_id,
        change_type=event.change_type,
        similarity_ratio=event.similarity_ratio,
        ai_summary=event.ai_summary,
        created_at=event.created_at,
        additions_count=details.get("additions_count", 0),
        deletions_count=details.get("deletions_count", 0),
        total_changes=details.get("total_changes", 0)
    )

async def _scan_brand_changes_internal(brand_id: uuid.UUID, db: AsyncSession) -> int:
    """Internal helper to scan snapshots for a brand, run diffing, and create ChangeEvents."""
    q_urls = select(BrandUrl).where(BrandUrl.brand_id == brand_id)
    res_urls = await db.execute(q_urls)
    brand_urls = list(res_urls.scalars().all())

    new_changes = 0
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)

    for b_url in brand_urls:
        q_snaps = (
            select(Snapshot)
            .where(Snapshot.brand_url_id == b_url.id)
            .order_by(Snapshot.captured_at.asc())
        )
        res_snaps = await db.execute(q_snaps)
        snaps = list(res_snaps.scalars().all())

        if len(snaps) < 2:
            continue

        for i in range(1, len(snaps)):
            prev_snap = snaps[i - 1]
            curr_snap = snaps[i]

            # Fast-path check: identical content hash
            if prev_snap.content_hash and curr_snap.content_hash and prev_snap.content_hash == curr_snap.content_hash:
                continue

            # Check if event already exists
            q_exist = select(ChangeEvent.id).where(
                ChangeEvent.snapshot_id == curr_snap.id,
                ChangeEvent.previous_snapshot_id == prev_snap.id
            )
            res_exist = await db.execute(q_exist)
            if res_exist.scalar_one_or_none():
                continue

            # Clean HTML
            html_curr = curr_snap.html_path or ""
            html_prev = prev_snap.html_path or ""
            _, blocks_curr = HtmlCleaner.clean(html_curr)
            _, blocks_prev = HtmlCleaner.clean(html_prev)

            # Compare
            comp = SnapshotComparator.compare(blocks_prev, blocks_curr)
            if comp.get("is_identical"):
                continue

            change_type, summary = ChangeClassifier.classify(html_prev, html_curr, comp)
            if change_type == "no_change":
                continue

            diff_details = {
                "additions_count": comp["additions_count"],
                "deletions_count": comp["deletions_count"],
                "modifications_count": comp["modifications_count"],
                "total_changes": comp["total_changes"],
                "word_delta": comp["word_delta"],
                "diff_chunks": comp["diff_chunks"][:200],
                "unified_diff": comp["unified_diff"]
            }

            event = ChangeEvent(
                id=uuid.uuid4(),
                snapshot_id=curr_snap.id,
                previous_snapshot_id=prev_snap.id,
                change_type=change_type,
                similarity_ratio=comp["similarity_ratio"],
                diff_details=diff_details,
                ai_summary=summary,
                created_at=now_naive
            )
            db.add(event)
            await db.commit()
            new_changes += 1

    return new_changes

@router.get("/brand/{brand_id}", response_model=ChangeEventListResponse)
async def list_brand_changes(
    brand_id: uuid.UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    change_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Lists change events for a brand with pagination and change_type filtering."""
    query = (
        select(ChangeEvent)
        .join(Snapshot, ChangeEvent.snapshot_id == Snapshot.id)
        .join(BrandUrl, Snapshot.brand_url_id == BrandUrl.id)
        .where(BrandUrl.brand_id == brand_id)
    )

    if change_type:
        query = query.where(ChangeEvent.change_type == change_type)

    query = query.order_by(desc(ChangeEvent.created_at))

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    count_res = await db.execute(count_query)
    total = count_res.scalar() or 0

    # If no changes logged yet, auto-evaluate historical snapshots
    if total == 0:
        new_detected = await _scan_brand_changes_internal(brand_id, db)
        if new_detected > 0:
            count_res = await db.execute(count_query)
            total = count_res.scalar() or 0

    # Paginate
    offset = (page - 1) * size
    paginated_q = query.offset(offset).limit(size)
    res = await db.execute(paginated_q)
    events = list(res.scalars().all())

    items = [_format_change_event(e) for e in events]
    pages = (total + size - 1) // size if total > 0 else 1

    return ChangeEventListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.post("/brand/{brand_id}/scan", response_model=ChangeScanResponse)
async def scan_brand_website_changes(
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Scans all historical and consecutive snapshots for a brand, detects changes, and generates ChangeEvents."""
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail=f"Brand {brand_id} not found")

    q_urls = select(BrandUrl).where(BrandUrl.brand_id == brand_id)
    res_urls = await db.execute(q_urls)
    brand_urls = list(res_urls.scalars().all())

    # Count total snapshots evaluated
    q_snap_cnt = select(func.count(Snapshot.id)).join(BrandUrl, Snapshot.brand_url_id == BrandUrl.id).where(BrandUrl.brand_id == brand_id)
    res_snap_cnt = await db.execute(q_snap_cnt)
    snapshots_evaluated = res_snap_cnt.scalar() or 0

    new_detected = await _scan_brand_changes_internal(brand_id, db)

    # Total events after scan
    q_total = (
        select(func.count(ChangeEvent.id))
        .join(Snapshot, ChangeEvent.snapshot_id == Snapshot.id)
        .join(BrandUrl, Snapshot.brand_url_id == BrandUrl.id)
        .where(BrandUrl.brand_id == brand_id)
    )
    res_total = await db.execute(q_total)
    total_events = res_total.scalar() or 0

    msg = (
        f"Scan complete. Evaluated {snapshots_evaluated} snapshot(s) across {len(brand_urls)} URL(s); "
        f"detected {new_detected} new change event(s)."
        if snapshots_evaluated >= 2
        else "Scan complete. Single snapshot available — trigger a new website crawl to capture subsequent versions and detect shifts."
    )

    return ChangeScanResponse(
        message=msg,
        urls_scanned=len(brand_urls),
        snapshots_evaluated=snapshots_evaluated,
        changes_detected=new_detected,
        total_events=total_events
    )

@router.get("/{change_id}", response_model=ChangeEventDetailRead)
async def get_change_event_detail(
    change_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieves full diff details (chunks and unified diff) for a specific change event."""
    event = await db.get(ChangeEvent, change_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"ChangeEvent {change_id} not found")

    details = event.diff_details or {}
    return ChangeEventDetailRead(
        id=event.id,
        snapshot_id=event.snapshot_id,
        previous_snapshot_id=event.previous_snapshot_id,
        change_type=event.change_type,
        similarity_ratio=event.similarity_ratio,
        ai_summary=event.ai_summary,
        created_at=event.created_at,
        additions_count=details.get("additions_count", 0),
        deletions_count=details.get("deletions_count", 0),
        total_changes=details.get("total_changes", 0),
        diff_details=details
    )

@router.get("/brand/{brand_id}/analytics", response_model=ChangeAnalyticsSummary)
async def get_brand_change_analytics(
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Computes distribution of change types and average similarity ratios."""
    base_q = (
        select(ChangeEvent.change_type, func.count(ChangeEvent.id), func.avg(ChangeEvent.similarity_ratio))
        .join(Snapshot, ChangeEvent.snapshot_id == Snapshot.id)
        .join(BrandUrl, Snapshot.brand_url_id == BrandUrl.id)
        .where(BrandUrl.brand_id == brand_id)
        .group_by(ChangeEvent.change_type)
    )
    res = await db.execute(base_q)
    rows = list(res.all())

    total = sum(r[1] for r in rows)

    # If no changes logged yet, auto-evaluate historical snapshots
    if total == 0:
        await _scan_brand_changes_internal(brand_id, db)
        res = await db.execute(base_q)
        rows = list(res.all())
        total = sum(r[1] for r in rows)

    counts = {r[0]: r[1] for r in rows}

    # Compute overall average similarity
    avg_sim = None
    if total > 0:
        sim_sum = sum((r[2] or 1.0) * r[1] for r in rows)
        avg_sim = round(float(sim_sum / total), 4)

    return ChangeAnalyticsSummary(
        total_changes=total,
        pricing_changes_count=counts.get("pricing_change", 0) + counts.get("price_update", 0) + counts.get("stock_status_change", 0),
        messaging_pivots_count=counts.get("messaging_pivot", 0),
        layout_overhauls_count=counts.get("layout_overhaul", 0),
        seo_changes_count=counts.get("seo_change", 0),
        minor_copy_count=counts.get("minor_copy", 0),
        avg_similarity=avg_sim
    )

@router.post("/compare", response_model=ChangeEventDetailRead, status_code=201)
async def compare_snapshots_on_demand(
    req: ChangeComparisonRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Compares two snapshots on demand and persists a ChangeEvent."""
    curr_snap = await db.get(Snapshot, req.snapshot_id)
    if not curr_snap:
        raise HTTPException(status_code=404, detail=f"Snapshot {req.snapshot_id} not found")

    prev_snap: Optional[Snapshot] = None
    if req.previous_snapshot_id:
        prev_snap = await db.get(Snapshot, req.previous_snapshot_id)
        if not prev_snap:
            raise HTTPException(status_code=404, detail=f"Previous Snapshot {req.previous_snapshot_id} not found")
    elif curr_snap.brand_url_id:
        q_prev = (
            select(Snapshot)
            .where(
                Snapshot.brand_url_id == curr_snap.brand_url_id,
                Snapshot.id != curr_snap.id,
                Snapshot.captured_at <= curr_snap.captured_at
            )
            .order_by(Snapshot.captured_at.desc())
            .limit(1)
        )
        res_prev = await db.execute(q_prev)
        prev_snap = res_prev.scalar_one_or_none()

    if not prev_snap:
        raise HTTPException(
            status_code=400,
            detail="No previous snapshot available to compare against. At least two snapshots are required."
        )

    # Clean HTML
    html_curr = curr_snap.html_path or ""
    html_prev = prev_snap.html_path or ""
    _, blocks_curr = HtmlCleaner.clean(html_curr)
    _, blocks_prev = HtmlCleaner.clean(html_prev)

    # Compare
    comp = SnapshotComparator.compare(blocks_prev, blocks_curr)
    change_type, summary = ChangeClassifier.classify(html_prev, html_curr, comp)

    diff_details = {
        "additions_count": comp["additions_count"],
        "deletions_count": comp["deletions_count"],
        "modifications_count": comp["modifications_count"],
        "total_changes": comp["total_changes"],
        "word_delta": comp["word_delta"],
        "diff_chunks": comp["diff_chunks"][:200],
        "unified_diff": comp["unified_diff"]
    }

    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    event = ChangeEvent(
        id=uuid.uuid4(),
        snapshot_id=curr_snap.id,
        previous_snapshot_id=prev_snap.id,
        change_type=change_type,
        similarity_ratio=comp["similarity_ratio"],
        diff_details=diff_details,
        ai_summary=summary,
        created_at=now_naive
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    return ChangeEventDetailRead(
        id=event.id,
        snapshot_id=event.snapshot_id,
        previous_snapshot_id=event.previous_snapshot_id,
        change_type=event.change_type,
        similarity_ratio=event.similarity_ratio,
        ai_summary=event.ai_summary,
        created_at=event.created_at,
        additions_count=comp["additions_count"],
        deletions_count=comp["deletions_count"],
        total_changes=comp["total_changes"],
        diff_details=diff_details
    )
