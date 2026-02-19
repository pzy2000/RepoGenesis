from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Movie
from .serializers import MovieSerializer
from .filters import MovieFilter
from .permissions import IsOwnerOrReadOnly
from .pagination import CustomPagination


class MovieListCreateView(generics.ListCreateAPIView):
    serializer_class = MovieSerializer
    permission_classes = [IsAuthenticated]
    queryset = Movie.objects.all().order_by("id")
    filterset_class = MovieFilter
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class MovieRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MovieSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    queryset = Movie.objects.all()

from django.shortcuts import render

# Create your views here.
