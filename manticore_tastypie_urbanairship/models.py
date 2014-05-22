from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save
from model_utils import Choices
from manticore_django.manticore_django.models import CoreModel
from manticore_tastypie_urbanairship.manticore_tastypie_urbanairship.utils import send_push_notification

__author__ = 'rudy'


# Stores user tokens from Urban Airship
class AirshipToken(CoreModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    token = models.CharField(max_length=100)
    expired = models.BooleanField(default=False)


class Notification(CoreModel):
    TYPES = Choices(*settings.SOCIAL_NOTIFICATION_TYPES)
    notification_type = models.PositiveSmallIntegerField(choices=TYPES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="receiver", null=True)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="reporter", null=True, blank=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = generic.GenericForeignKey()

    def message(self):
        return unicode(Notification.TYPES._triples[self.notification_type][2])

    def push_message(self):
        return "{0} {1}".format(self.reporter, self.message())

    def name(self):
        return u"{0}".format(Notification.TYPES._triples[self.notification_type][1])

    def display_name(self):
        return u"{0}".format(self.get_notification_type_display())

    class Meta:
        ordering = ['-created']


def create_notification(receiver, reporter, content_object, notification_type):
    # If the receiver of this notification is the same as the reporter or
    # if the user has blocked this type, then don't create
    if receiver == reporter or not NotificationSetting.objects.get(notification_type=notification_type, user=receiver).allow:
        return

    notification = Notification.objects.create(user=receiver,
                                               reporter=reporter,
                                               content_object=content_object,
                                               notification_type=notification_type)
    notification.save()

    send_push_notification(receiver, notification.push_message())


class NotificationSetting(CoreModel):
    notification_type = models.PositiveSmallIntegerField(choices=Notification.TYPES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    allow = models.BooleanField(default=True)

    class Meta:
        unique_together = ('notification_type', 'user')

    def name(self):
        return u"{0}".format(Notification.TYPES._triples[self.notification_type][1])

    def display_name(self):
        return u"{0}".format(self.get_notification_type_display())


def create_notifications(sender, **kwargs):
    sender_name = "{0}.{1}".format(sender._meta.app_label, sender._meta.object_name)
    if sender_name.lower() != settings.AUTH_USER_MODEL.lower():
        return

    if kwargs['created']:
        user = kwargs['instance']
        NotificationSetting.objects.bulk_create([NotificationSetting(user=user, notification_type=pk) for pk, name in Notification.TYPES])

post_save.connect(create_notifications)