"""
scheduler.py — Background thread that auto-publishes scheduled posts when their
               scheduled_at time has passed.
"""
import threading
import time
import random
from datetime import datetime, timezone


def _run(app, interval):
    """Infinite loop: check for due scheduled posts every `interval` seconds."""
    while True:
        time.sleep(interval)
        try:
            with app.app_context():
                from database import db
                from models   import Post, Notification

                now  = datetime.now(timezone.utc)
                due  = Post.query.filter(
                    Post.status == "scheduled",
                    Post.scheduled_at <= now,
                ).all()

                if not due:
                    continue

                for post in due:
                    post.status       = "published"
                    post.likes        = random.randint(10, 200)
                    post.comments     = random.randint(2,  60)
                    post.shares       = random.randint(1,  50)
                    post.reach        = random.randint(200, 5000)
                    post.published_at = now
                    post.scheduled_at = None

                    notif = Notification(
                        user_id=post.user_id,
                        text=f'Scheduled post auto-published: "{post.text[:60]}..."',
                        type="success",
                    )
                    db.session.add(notif)
                    print(f"[Scheduler] Auto-published post #{post.id} for user #{post.user_id}")

                db.session.commit()

        except Exception as exc:
            print(f"[Scheduler] Error: {exc}")


def start_scheduler(app):
    """Start the scheduler in a daemon thread so it dies with the main process."""
    interval = app.config.get("SCHEDULER_INTERVAL_SECONDS", 60)
    t = threading.Thread(target=_run, args=(app, interval), daemon=True)
    t.start()
    print(f"⏰  Scheduler started — checking every {interval}s")
