from django.contrib.auth.models import update_last_login

from rest_framework import serializers
from accounts.models import User, Profile


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model=User
        fields="__all__"
        extra_kwargs = {
            'groups': {'read_only': True},
            'user_permissions': {'read_only': True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
    

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            user_by_email = User.objects.get(email=data['email'])

            if user_by_email.check_password(data['password']):
                update_last_login(None, user_by_email)
                return user_by_email
            else:
                raise serializers.ValidationError("회원 정보가 잘못되었습니다.")
        except User.DoesNotExist:
            raise serializers.ValidationError("회원 정보가 잘못되었습니다.")
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields=['id', 'email', 'name', 'phone_number', 'birthday', 'created_at', 'updated_at', 'last_login']


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model=Profile
        fields='__all__'

    def __init__(self, *args, **kwargs):
        super(ProfileSerializer, self).__init__(*args, **kwargs)
        
        request = self.context.get('request', None)
        if request and request.method == 'POST':
            self.fields.pop('user')


class AuthorSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    
    class Meta:
        model = Profile
        fields = ['id', 'email', 'phone_number', 'image', 'nickname', 'role']