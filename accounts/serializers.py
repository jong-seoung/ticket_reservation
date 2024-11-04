from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login

from rest_framework import serializers
from accounts.models import User, Profile


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model=User
        fields="__all__"

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
    

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            update_last_login(None, user)
            return user
        raise serializers.ValidationError("올바른 회원정보를 입력하세요.")
    

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
        
        if self.context.get('request').method == 'POST':
            self.fields.pop('user')