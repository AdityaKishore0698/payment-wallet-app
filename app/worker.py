import os
import asyncio
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("wallet_tasks", broker=REDIS_URL, backend=REDIS_URL)

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
