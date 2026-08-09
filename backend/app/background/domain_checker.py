import logging
from datetime import datetime
from app.database import SessionLocal
from app.models.custom_domain import CustomDomain

logger = logging.getLogger(__name__)


async def check_domains():
    """Re-verify DNS for all verified domains daily."""
    db = SessionLocal()
    try:
        domains = db.query(CustomDomain).filter(CustomDomain.is_verified == True).all()
        for domain in domains:
            try:
                import dns.resolver

                answers = dns.resolver.resolve(
                    f"_intercom-verify.{domain.domain}", "TXT"
                )
                txt_values = [str(r).strip('"') for r in answers]
                still_verified = any(
                    domain.verification_token in v for v in txt_values
                )
                domain.last_checked_at = datetime.utcnow()
                if not still_verified:
                    logger.warning(
                        f"Domain {domain.domain} DNS verification failed, marking unverified"
                    )
                    domain.is_verified = False
            except Exception as e:
                logger.warning(f"Domain check failed for {domain.domain}: {e}")
                domain.last_checked_at = datetime.utcnow()
        db.commit()
    except Exception as e:
        logger.error(f"Domain checker error: {e}")
        db.rollback()
    finally:
        db.close()
