"""
Celery Beat task: scans for workflows with trigger_type='schedule' every minute
and fires those whose cron expression is due.
"""
import json
import logging
import uuid
from datetime import datetime

from croniter import croniter

from app.workers.celery_app import celery_app
from app.workers.execution_tasks import _get_sync_db, run_workflow_task

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
