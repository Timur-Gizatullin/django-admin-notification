from django.db.models.signals import post_delete, post_save, pre_save
from django.apps.registry import Apps
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render
from django.conf import settings
from django.shortcuts import HttpResponse, redirect
from django.apps import apps as django_apps
from admin_notification.models import Notification
from django.dispatch import receiver
from notification_consumer import NotificationConsumer
import asyncio

try:
    model = django_apps.get_model(settings.NOTIFICATION_MODEL, require_ready=False)
except ValueError:
    raise ImproperlyConfigured(
        "NOTIFICATION_MODEL must be of the form 'app_label.model_name'"
    )


@receiver(post_save, sender=model)
def post_save_handler(sender, **kwargs):
    if kwargs['created']:
        notification = Notification.objects.all().first()
        notification.count += 1
        notification.save()

        async def send_message_to_consumer(notification_count: str):
            notification_consumer = NotificationConsumer()
            await notification_consumer.connect()

            event = {
                "type": "create_notification",
                "message": notification_count
            }

            await notification_consumer.send_message(event=event)
            await notification_consumer.disconnect(code="0")

        asyncio.get_event_loop().run_until_complete(send_message_to_consumer(notification_count=notification.count))

