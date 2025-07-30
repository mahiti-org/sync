from rest_framework import serializers
from django.contrib.auth.models import User

class PushDataSerializer(serializers.Serializer):
    data = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
        help_text="List of objects to synchronize"
    )

class PullRequestSerializer(serializers.Serializer):
    models = serializers.DictField(
        child=serializers.DateTimeField(required=False, allow_null=True),
        help_text="Dictionary of model names and their last sync timestamps"
    )
    batch_size = serializers.IntegerField(
        default=100,
        min_value=1,
        max_value=1000,
        help_text="Number of records per batch"
    )

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

