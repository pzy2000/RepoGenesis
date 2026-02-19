from rest_framework import generics, permissions
from django.contrib.auth.models import User
from .serializers import RegisterSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

from django.shortcuts import render

# Create your views here.
