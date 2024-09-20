# api/serializers.py

from rest_framework import serializers
from colony.models import Strain, Cage, Mouse, Rack
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

class StrainSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Strain
        fields = ['id', 'name', 'owner', 'owner_name']
        read_only_fields = ['owner']

class CageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cage
        fields = '__all__'

class MouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mouse
        fields = '__all__'

class RackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rack
        fields = '__all__'
