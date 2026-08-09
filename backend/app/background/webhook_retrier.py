import logging
from app.services.webhook_service import retry_pending_deliveries

logger = logging.getLogger(__name__)


async def retry_webhooks():
    try:
        await retry_pending_deliveries()
    except Exception as e:
        logger.error(f"Webhook retrier error: {e}")
