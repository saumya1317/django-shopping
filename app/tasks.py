from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import PriceAlert, Cart

@shared_task
def process_price_alert(alert_id, current_price):
    """Send email (and auto-buy if requested) for a fulfilled PriceAlert."""
    try:
        alert = PriceAlert.objects.select_related('user', 'product').get(pk=alert_id)
    except PriceAlert.DoesNotExist:
        return

    # If it was already processed or price not yet good, bail.
    if alert.fulfilled or current_price > alert.target_price:
        return

    # Mark fulfilled
    alert.fulfilled = True
    alert.fulfilled_at = timezone.now()
    alert.save(update_fields=['fulfilled', 'fulfilled_at'])

    # Auto-buy
    if alert.buy_when_drop:
        Cart.objects.get_or_create(
            user=alert.user,
            product=alert.product,
            defaults={'quantity': 1},
        )

    # Email body
    subject = f"Price alert – {alert.product.title} now at ₹{current_price}"
    if alert.buy_when_drop:
        message = (
            f"Hi {alert.user.get_full_name() or alert.user.username},\n\n"
            f"Great news! The price of '{alert.product.title}' has dropped to ₹{current_price}.\n"
            "We've automatically added it to your cart as requested.\n\n"
            "Complete checkout whenever you're ready."
        )
    else:
        message = (
            f"Hi {alert.user.get_full_name() or alert.user.username},\n\n"
            f"The price of '{alert.product.title}' has dropped to ₹{current_price}.\n\n"
            "Visit the store to purchase it now!"
        )

    send_mail(
        subject,
        message,
        getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
        [alert.user.email],
        fail_silently=True,
    ) 