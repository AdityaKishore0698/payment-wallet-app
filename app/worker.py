import os
import ssl

from celery import Celery

# Local Docker Compose default. Hosted deployments set REDIS_URL to a managed
# broker (Upstash), which uses TLS and therefore the ``rediss://`` scheme.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("wallet_tasks", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.broker_connection_retry_on_startup = True

if REDIS_URL.startswith("rediss://"):
    # Upstash presents a valid public certificate; require verification unless
    # the URL explicitly opts out via ?ssl_cert_reqs=CERT_NONE.
    cert_reqs = ssl.CERT_REQUIRED
    if "ssl_cert_reqs=CERT_NONE" in REDIS_URL or "ssl_cert_reqs=none" in REDIS_URL:
        cert_reqs = ssl.CERT_NONE
    celery_app.conf.broker_use_ssl = {"ssl_cert_reqs": cert_reqs}
    celery_app.conf.redis_backend_use_ssl = {"ssl_cert_reqs": cert_reqs}


@celery_app.task(name="send_recovery_email_task")
def send_recovery_email_task(email: str, token: str):
    """
    Mock background task for sending emails.
    In a real app, this would use SMTP or an API like SendGrid.
    """
    import time
    # Simulate network delay
    time.sleep(2)
    print(f"========== EMAIL SENT ==========")
    print(f"To: {email}")
    print(f"Subject: Password Recovery")
    print(f"Body: Your password reset token is: {token}")
    print(f"================================")
    return True
