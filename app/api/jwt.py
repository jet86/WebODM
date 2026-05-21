from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.views import JSONWebTokenAPIView
from rest_framework_jwt.compat import Serializer, get_username_field, PasswordField
from rest_framework import serializers

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

class JSONWebTokenSerializer(Serializer):
    """
    Serializer class used to validate a username and password.

    'username' is identified by the custom UserModel.USERNAME_FIELD.

    Returns a JSON Web Token that can be used to authenticate later calls.
    """
    def __init__(self, *args, **kwargs):
        """
        Dynamically add the USERNAME_FIELD to self.fields.
        """
        super(JSONWebTokenSerializer, self).__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField()
        self.fields['password'] = PasswordField(write_only=True)
        self.fields['impersonate'] = serializers.CharField(required=False)

    @property
    def username_field(self):
        return get_username_field()

    def validate(self, attrs):
        credentials = {
            self.username_field: attrs.get(self.username_field),
            'password': attrs.get('password')
        }

        if all(credentials.values()):
            user = authenticate(**credentials)
            if user:
                if not user.is_active:
                    msg = _('User account is disabled.')
                    raise serializers.ValidationError(msg)

                if attrs.get('impersonate'):
                    if not user.is_superuser:
                        raise serializers.ValidationError(_('Cannot impersonate, user is not superuser.'))
                    try:
                        impersonated = User.objects.get(username=attrs.get('impersonate'))
                        return {
                            'token': jwt_encode_handler(jwt_payload_handler(impersonated)),
                            'user': impersonated
                        }
                    except:
                        raise serializers.ValidationError(_('Unable to log in with provided credentials.'))
                else:
                    return {
                        'token': jwt_encode_handler(jwt_payload_handler(user)),
                        'user': user
                    }
            else:
                raise serializers.ValidationError(_('Unable to log in with provided credentials.'))
        else:
            msg = _('Must include "{username_field}" and "password".')
            msg = msg.format(username_field=self.username_field)
            raise serializers.ValidationError(msg)

class ObtainJSONWebToken(JSONWebTokenAPIView):
    """
    API View that receives a POST with a user's username and password
    and an optional impersonate parameter (admin only)

    Returns a JSON Web Token that can be used for authenticated requests.
    """
    serializer_class = JSONWebTokenSerializer

obtain_jwt_token = ObtainJSONWebToken.as_view()