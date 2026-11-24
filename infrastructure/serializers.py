from rest_framework import serializers

from .models import Terrain, Dwelling, AccessPoint


class TerrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Terrain
        fields = "__all__"


class DwellingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dwelling
        fields = "__all__"


class AccessPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessPoint
        fields = "__all__"