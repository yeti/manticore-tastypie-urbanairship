from django.contrib.auth import get_user_model
from manticore_tastypie_core.manticore_tastypie_core.test import ManticomResourceTestCase
from manticore_tastypie_urbanairship.manticore_tastypie_urbanairship.models import NotificationSetting

User = get_user_model()


class SettingsTests(ManticomResourceTestCase):
    def setUp(self):
        super(SettingsTests, self).setUp()

        user_data = {'email': 'testuser@gmail.com', User.USERNAME_FIELD: 'testuser@gmail.com'}
        self.user = User.objects.create_user(**user_data)

    def test_notification_settings_get_manticom(self):
        self.assertManticomGETResponse('notification_setting', 'notification_setting', '$notificationSetting',
                                       self.user)

    def test_notification_settings_patch_manticom(self):
        notification_setting = self.user.notification_settings.all()[0]
        data = {
            'allow_push': False,
            'allow_email': False
        }
        self.assertManticomPATCHResponse('notification_setting/{}'.format(notification_setting.pk),
                                         '$notificationPatchRequest', '$notificationSetting', data, self.user)
        updated_notification_setting = NotificationSetting.objects.get(pk=notification_setting.pk)
        self.assertFalse(updated_notification_setting.allow_push)
        self.assertFalse(updated_notification_setting.allow_email)
