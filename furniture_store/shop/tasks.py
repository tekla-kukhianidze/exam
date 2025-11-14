from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .models import Order

@shared_task
def send_order_confirmation_email(order_id):
    """შეკვეთის დადასტურების email-ის გაგზავნა."""
    try:
        order = Order.objects.select_related('user').get(id=order_id)
        subject = f"შეკვეთის დადასტურება #{order.order_number}"
        message = (
            f"მოგესალმებით {order.user.first_name},\n\n"
            f"თქვენი შეკვეთა #{order.order_number} წარმატებით მივიღეთ.\n"
            f"ჯამური თანხა: {order.total_amount} ლარი. სტატუსი: {order.get_status_display()}"
        )
        send_mail(
            subject,
            message,
            'info@furniturestore.ge',
            [order.user.email],
            fail_silently=False,
        )
        return "Email sent successfully"
    except Order.DoesNotExist:
        return "Order not found"

@shared_task
def update_order_status_to_processing(order_id):
    """
    შეკვეთის სტატუსის ავტომატური განახლება 'PENDING'-დან 'PROCESSING'-ზე
    (გამოიძახება შეკვეთის შექმნიდან გარკვეული დროის შემდეგ).
    """
    try:
        order = Order.objects.get(id=order_id, status='PENDING')
        order.status = 'PROCESSING'
        order.save()
        return f"Order {order.order_number} status updated to PROCESSING."
    except Order.DoesNotExist:
        return f"Order not found or not in PENDING status."