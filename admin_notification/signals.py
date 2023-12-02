from django.db.models.signals import post_delete, post_save, pre_save
from django.apps.registry import Apps
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render
from django.conf import settings
from django.shortcuts import HttpResponse, redirect
from django.apps import apps as django_apps
from admin_notification.models import Notification
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from admin_notification.notification_consumer import NotificationConsumer
from channels.layers import get_channel_layer
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

        channel_layer = get_channel_layer()

        group_name = "notification"
        content = {
            "type": "create_notification",
            "message": str(notification.count)
        }

        res = async_to_sync(channel_layer.group_send)(group_name, content)

        print(f"ws result is {res}")
