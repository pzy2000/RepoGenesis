from rest_framework import serializers
from .models import Movie


class MovieSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source="creator.username")

    class Meta:
        model = Movie
        fields = ["id", "title", "genre", "year", "creator"]


