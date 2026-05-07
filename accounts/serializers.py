from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Role

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.ReadOnlyField(source='role.name', allow_null=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'role_name']

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']

from django.contrib.auth.models import Group as DjangoGroup

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = DjangoGroup
        fields = ['id', 'name']