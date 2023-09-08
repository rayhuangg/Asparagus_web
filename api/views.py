from django.shortcuts import render

from rest_framework import generics
from monitor.models import ResultList
from .serializers import ResultListSerializer

class ResultListView(generics.ListAPIView):
    serializer_class = ResultListSerializer

    def get_queryset(self):
        demo_id = self.kwargs['demoID']
        return ResultList.objects.filter(demo__id=demo_id)