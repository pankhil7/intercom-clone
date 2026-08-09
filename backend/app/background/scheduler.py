from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = AsyncIOScheduler()


def start_scheduler():
    from app.background.sla_checker import check_sla_breaches
    from app.background.snooze_waker import wake_snoozed_conversations
    from app.background.webhook_retrier import retry_webhooks
    from app.background.domain_checker import check_domains

    scheduler.add_job(check_sla_breaches, IntervalTrigger(minutes=5), id='sla_checker')
    scheduler.add_job(
        wake_snoozed_conversations, IntervalTrigger(minutes=1), id='snooze_waker'
    )
    scheduler.add_job(retry_webhooks, IntervalTrigger(minutes=1), id='webhook_retrier')
    scheduler.add_job(check_domains, IntervalTrigger(hours=24), id='domain_checker')

    scheduler.start()


def stop_scheduler():
    scheduler.shutdown(wait=False)
