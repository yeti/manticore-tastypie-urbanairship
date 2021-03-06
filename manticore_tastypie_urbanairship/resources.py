from datetime import timedelta
from django.conf import settings
from tastypie import fields
from tastypie.exceptions import BadRequest
from tastypie.utils import now
from manticore_tastypie_core.manticore_tastypie_core.resources import ManticoreModelResource
from .models import AirshipToken, NotificationSetting, Notification
from manticore_tastypie_user.manticore_tastypie_user.authentication import ExpireApiKeyAuthentication
from manticore_tastypie_user.manticore_tastypie_user.authorization import UserObjectsOnlyAuthorization
from manticore_tastypie_user.manticore_tastypie_user.resources import UserResource
import urbanairship


class AirshipTokenResource(ManticoreModelResource):

    class Meta:
        queryset = AirshipToken.objects.all()
        allowed_methods = ['get', 'post']
        authorization = UserObjectsOnlyAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "airship_token"
        always_return_data = True
        object_name = "airship_token"

    def obj_create(self, bundle, **kwargs):
        if 'token' in bundle.data:
            airship = urbanairship.Airship(settings.AIRSHIP_APP_KEY, settings.AIRSHIP_APP_MASTER_SECRET)
            try:
                airship.register(bundle.data['token'], alias="{0}:{1}".format(bundle.request.user.pk,
                                                                              bundle.request.user.get_username()))

                # Delete other usages of this token (i.e. multiple accounts on one device)
                AirshipToken.objects.filter(token=bundle.data['token']).delete()

                bundle.obj = AirshipToken(user=bundle.request.user, token=bundle.data['token'])
                bundle.obj.save()
            except urbanairship.AirshipFailure:
                raise BadRequest("Failed Authentication")

            return bundle
        else:
            raise BadRequest("Missing token")


class NotificationSettingResource(ManticoreModelResource):
    name = fields.CharField(attribute='name', blank=True)

    class Meta:
        queryset = NotificationSetting.objects.all()
        allowed_methods = ['get', 'patch']
        authorization = UserObjectsOnlyAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "notification_setting"
        always_return_data = True
        object_name = "notification_setting"
        fields = ['id', 'allow_push', 'allow_email', 'name']


class NotificationResource(ManticoreModelResource):
    name = fields.CharField(attribute='name')
    message = fields.CharField()
    reporter = fields.ToOneField(UserResource, 'reporter', null=True, full=True)

    def dehydrate_message(self, bundle):
        return bundle.obj.message(Notification.PUSH)

    class Meta:
        queryset = Notification.objects.all()
        allowed_methods = ['get']
        authorization = UserObjectsOnlyAuthorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "notification"
        object_name = "notification"
        fields = ['id', 'created', 'name', 'message', 'reporter']

    def get_object_list(self, request=None, **kwargs):
        obj_list = super(NotificationResource, self).get_object_list(request)

        # Limit the list of notifications if we have the setting defined to the past x hours
        if hasattr(settings, 'NOTIFICATION_WINDOW_HOURS'):
            date = now() - timedelta(days=settings.NOTIFICATION_WINDOW_HOURS)
            obj_list = obj_list.filter(created__gte=date)

        return obj_list
