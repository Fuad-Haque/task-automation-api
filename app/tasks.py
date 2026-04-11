import asyncio
import random
from datetime import datetime, timezone

from app.storage import update_task


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Send Report ────────────────────────────────────────────────────────────────
async def run_send_report(task_id: str, params: dict) -> None:
    try:
        # Step 1 – mark as processing
        update_task(task_id, {
            "status": "processing",
            "progress": 0,
            "started_at": _now(),
        })

        # Step 2 – fetch data
        await asyncio.sleep(2)
        update_task(task_id, {"progress": 25})

        # Step 3 – generate report
        await asyncio.sleep(3)
        update_task(task_id, {"progress": 50})

        # Step 4 – format output
        await asyncio.sleep(2)
        update_task(task_id, {"progress": 75})

        # Step 5 – send email
        await asyncio.sleep(1)
        update_task(task_id, {"progress": 100})

        # Step 6 – complete
        update_task(task_id, {
            "status": "complete",
            "completed_at": _now(),
            "result": {
                "report_type": params["report_type"],
                "recipient": params["recipient_email"],
                "rows_processed": random.randint(500, 5000),
                "email_sent": True,
                "report_url": f"https://reports.example.com/report_{task_id}.pdf",
            },
        })

    except Exception as exc:
        update_task(task_id, {"status": "failed", "error": str(exc)})


# ── Process Data ───────────────────────────────────────────────────────────────
async def run_process_data(task_id: str, params: dict) -> None:
    try:
        # Step 1 – mark as processing
        update_task(task_id, {
            "status": "processing",
            "progress": 0,
            "started_at": _now(),
        })

        # Step 2 – validate
        items = len(params["data"])
        await asyncio.sleep(1)
        update_task(task_id, {"progress": 20})

        # Step 3 – run operation
        await asyncio.sleep(2)
        update_task(task_id, {"progress": 60})

        # Step 4 – format output
        await asyncio.sleep(1)
        update_task(task_id, {"progress": 90})

        # Step 5 – complete
        update_task(task_id, {
            "status": "complete",
            "progress": 100,
            "completed_at": _now(),
            "result": {
                "operation": params["operation"],
                "items_processed": items,
                "output_format": params["output_format"],
                "output_size_kb": round(items * 0.5, 2),
                "issues_found": random.randint(0, 5),
            },
        })

    except Exception as exc:
        update_task(task_id, {"status": "failed", "error": str(exc)})


# ── Sync Integration ───────────────────────────────────────────────────────────
async def run_sync_integration(task_id: str, params: dict) -> None:
    try:
        # Step 1 – mark as processing
        update_task(task_id, {
            "status": "processing",
            "progress": 0,
            "started_at": _now(),
        })

        # Step 2 – connect to source
        await asyncio.sleep(2)
        update_task(task_id, {"progress": 15})

        # Step 3 – fetch records
        await asyncio.sleep(3)
        update_task(task_id, {"progress": 40})

        # Step 4 – compare with local data
        await asyncio.sleep(2)
        update_task(task_id, {"progress": 65})

        # Step 5 – write updates
        await asyncio.sleep(2)
        update_task(task_id, {"progress": 85})

        # Step 6 – finalize
        await asyncio.sleep(1)
        update_task(task_id, {"progress": 100})

        # Step 7 – complete
        update_task(task_id, {
            "status": "complete",
            "completed_at": _now(),
            "result": {
                "source": params["source"],
                "sync_type": params["sync_type"],
                "records_fetched": random.randint(100, 10000),
                "records_updated": random.randint(10, 500),
                "records_created": random.randint(5, 100),
                "duration_seconds": 10,
            },
        })

    except Exception as exc:
        update_task(task_id, {"status": "failed", "error": str(exc)})