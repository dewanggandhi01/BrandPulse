from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
import structlog
from sqlalchemy import select, and_

from workers.celery_app import app
from workers.diffing.html_cleaner import HtmlCleaner
from workers.diffing.comparator import SnapshotComparator
from workers.diffing.classifier import ChangeClassifier
from app.database import async_session_maker
from app.models.snapshot import Snapshot
from app.models.change_event import ChangeEvent

logger = structlog.get_logger()

async def _async_detect_changes(snapshot_id_str: str, prev_snapshot_id_str: Optional[str] = None) -> Dict[str, Any]:
    snapshot_id = UUID(snapshot_id_str)
    logger.info("Executing snapshot diff detection", snapshot_id=str(snapshot_id))

    async with async_session_maker() as session:
        current_snap = await session.get(Snapshot, snapshot_id)
        if not current_snap:
            raise ValueError(f"Snapshot {snapshot_id} not found")

        # 1. Resolve previous snapshot
        prev_snap: Optional[Snapshot] = None
        if prev_snapshot_id_str:
            prev_snap = await session.get(Snapshot, UUID(prev_snapshot_id_str))
        elif current_snap.brand_url_id:
            # Query prior snapshot for the same URL captured before this one
            q_prev = (
                select(Snapshot)
                .where(
                    Snapshot.brand_url_id == current_snap.brand_url_id,
                    Snapshot.id != current_snap.id,
                    Snapshot.captured_at <= current_snap.captured_at
                )
                .order_by(Snapshot.captured_at.desc())
                .limit(1)
            )
            res_prev = await session.execute(q_prev)
            prev_snap = res_prev.scalar_one_or_none()

        if not prev_snap:
            logger.info("No prior snapshot found to compare against", snapshot_id=str(snapshot_id))
            return {
                "status": "baseline",
                "message": "Baseline snapshot established. No prior version available for diffing.",
                "snapshot_id": str(snapshot_id)
            }

        # 2. Check content hash identity first (O(1) fast-path)
        if current_snap.content_hash and prev_snap.content_hash and current_snap.content_hash == prev_snap.content_hash:
            logger.info("Content hashes match exactly - no changes detected", snapshot_id=str(snapshot_id))
            return {
                "status": "identical",
                "similarity_ratio": 1.0,
                "change_type": "no_change",
                "summary": "Content hash identical to previous snapshot."
            }

        # 3. Clean and normalize both HTML snapshots
        html_current = current_snap.html_path or ""
        html_prev = prev_snap.html_path or ""

        _, blocks_curr = HtmlCleaner.clean(html_current)
        _, blocks_prev = HtmlCleaner.clean(html_prev)

        # 4. Compare text blocks
        comp_res = SnapshotComparator.compare(blocks_prev, blocks_curr)

        if comp_res["is_identical"]:
            logger.info("Normalized content is identical", snapshot_id=str(snapshot_id))
            return {
                "status": "identical",
                "similarity_ratio": 1.0,
                "change_type": "no_change",
                "summary": "Normalized content is identical after removing ephemeral DOM noise."
            }

        # 5. Classify the nature of the change
        change_type, summary = ChangeClassifier.classify(html_prev, html_current, comp_res)

        # 6. Save ChangeEvent
        event = ChangeEvent(
            id=uuid4(),
            snapshot_id=current_snap.id,
            previous_snapshot_id=prev_snap.id,
            change_type=change_type,
            similarity_ratio=comp_res["similarity_ratio"],
            diff_details={
                "additions_count": comp_res["additions_count"],
                "deletions_count": comp_res["deletions_count"],
                "modifications_count": comp_res["modifications_count"],
                "total_changes": comp_res["total_changes"],
                "word_delta": comp_res["word_delta"],
                "diff_chunks": comp_res["diff_chunks"][:150],  # cap stored chunks
                "unified_diff": comp_res["unified_diff"]
            },
            ai_summary=summary,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)

        logger.info(
            "Change event created successfully",
            change_id=str(event.id),
            change_type=change_type,
            similarity_ratio=comp_res["similarity_ratio"]
        )

        return {
            "status": "detected",
            "change_id": str(event.id),
            "change_type": change_type,
            "similarity_ratio": comp_res["similarity_ratio"],
            "summary": summary,
            "additions_count": comp_res["additions_count"],
            "deletions_count": comp_res["deletions_count"]
        }

@app.task(name="workers.tasks.diffing.detect_snapshot_changes", bind=True)
def detect_snapshot_changes(self, snapshot_id: str, prev_snapshot_id: Optional[str] = None) -> Dict[str, Any]:
    """Celery task to detect and classify changes between website snapshots."""
    try:
        return asyncio.run(_async_detect_changes(snapshot_id, prev_snapshot_id))
    except Exception as exc:
        logger.error("Error executing diff detection", snapshot_id=snapshot_id, error=str(exc))
        raise
