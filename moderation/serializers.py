from rest_framework import serializers
from .models import ModerationStatus, ModerationLog

class ModerationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModerationStatus
        fields = ['id', 'name']

class ModerationLogSerializer(serializers.ModelSerializer):
    photo_info = serializers.StringRelatedField(source='photo')
    moderator_name = serializers.StringRelatedField(source='moderator')

    class Meta:
        model = ModerationLog
        fields = ['id', 'photo', 'photo_info', 'moderator', 'moderator_name', 'review_date', 'action', 'comment']
        read_only_fields = ['id', 'review_date']
