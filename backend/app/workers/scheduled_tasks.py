"""
Celery Beat tasks:
- check_scheduled_workflows: fires cron-scheduled workflows every minute.
- check_approval_timeouts: fails executions stuck in awaiting_approval past APPROVAL_TIMEOUT_MINUTES.
"""
import json
import logging
import uuid
from datetime import datetime, timedelta

try:
    from croniter import croniter
except ImportError:
    croniter = None  # type: ignore

from app.workers.celery_app import celery_app
from app.workers.execution_tasks import _get_sync_db, run_workflow_task
from app.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(name="check_scheduled_workflows")
def check_scheduled_workflows():
    now = datetime.utcnow()
    conn = _get_sync_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, trigger_config FROM workflows "
            "WHERE trigger_type='schedule' AND is_active=1"
        )
        rows = cur.fetchall()

        for wf_id, wf_name, config_str in rows:
            try:
                cfg = json.loads(config_str) if config_str else {}
                cron_expr = cfg.get("cron", "")
                if not cron_expr:
                    logger.debug("Workflow %s has no cron expression, skipping", wf_id)
                    continue

                if croniter is None:
                    logger.warning("croniter not installed; skipping scheduled workflow %s", wf_id)
                    continue

                # Find the most recent tick that should have fired
                it = croniter(cron_expr, now)
                prev_fire = it.get_prev(datetime)
                seconds_ago = (now - prev_fire).total_seconds()

                # Only act if this tick is within the last 60 s (our polling window)
                if seconds_ago > 60:
                    continue

                # Skip if we already created an execution for this tick
                cur.execute(
                    "SELECT id FROM executions "
                    "WHERE workflow_id=? AND trigger_type='schedule' AND created_at >= ? "
                    "ORDER BY created_at DESC LIMIT 1",
                    (wf_id, prev_fire.isoformat()),
                )
                if cur.fetchone():
                    continue

                prompt = cfg.get("prompt", f"Scheduled run: {wf_name}")
                execution_id = str(uuid.uuid4())
                cur.execute(
                    "INSERT INTO executions "
                    "(id, workflow_id, status, trigger_type, trigger_payload, created_at) "
                    "VALUES (?,?,?,?,?,?)",
                    (execution_id, wf_id, "pending", "schedule",
                     json.dumps({"prompt": prompt}), now.isoformat()),
                )
                conn.commit()

                run_workflow_task.delay(wf_id, execution_id, {"prompt": prompt})
                logger.info("Fired scheduled execution %s for workflow %s (%s)", execution_id, wf_id, wf_name)

            except Exception:
                logger.exception("Failed to process scheduled workflow %s (%s)", wf_id, wf_name)
    finally:
        conn.close()


@celery_app.task(name="check_approval_timeouts")
def check_approval_timeouts():
    """Fail executions that have been waiting for approval longer than APPROVAL_TIMEOUT_MINUTES."""
    timeout_minutes = settings.APPROVAL_TIMEOUT_MINUTES
    if timeout_minutes <= 0:
        return

    cutoff = (datetime.utcnow() - timedelta(minutes=timeout_minutes)).isoformat()
    conn = _get_sync_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM executions WHERE status='awaiting_approval' AND created_at < ?",
            (cutoff,),
        )
        rows = cur.fetchall()
        for (execution_id,) in rows:
            now = datetime.utcnow().isoformat()
            cur.execute(
                "UPDATE executions SET status='failed', completed_at=?, error_message=? WHERE id=?",
                (now, f"Approval timed out after {timeout_minutes} minutes", execution_id),
            )
            logger.warning("Approval timeout: execution %s failed after %d minutes", execution_id, timeout_minutes)
        if rows:
            conn.commit()
    except Exception:
        logger.exception("Error checking approval timeouts")
    finally:
        conn.close()
