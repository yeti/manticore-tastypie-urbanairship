from django.conf import settings
import urbanairship
from .models import AirshipToken
from .resources import AirshipTokenResource, NotificationSettingResource


# Registers this library's resources
def register_api(api):
    api.register(AirshipTokenResource())
    api.register(NotificationSettingResource())
    return api


def send_push_notification(receiver, message):
    if AirshipToken.objects.filter(user=receiver, expired=False).exists():
        try:
            device_tokens = list(AirshipToken.objects.filter(user=receiver, expired=False).values_list('token', flat=True))
            airship = urbanairship.Airship(settings.AIRSHIP_APP_KEY, settings.AIRSHIP_APP_MASTER_SECRET)

            for device_token in device_tokens:
                push = airship.create_push()
                push.audience = urbanairship.device_token(device_token)
                push.notification = urbanairship.notification(ios=urbanairship.ios(alert=message, badge='+1'))
                push.device_types = urbanairship.device_types('ios')
                push.send()
        except urbanairship.AirshipFailure:
            pass