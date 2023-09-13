# api/views.py
from django.shortcuts import render

from rest_framework import generics
from monitor.models import ResultList, Instance
from .serializers import ResultListSerializer
from rest_framework.response import Response


class ResultListView(generics.ListAPIView):
    serializer_class = ResultListSerializer

    def get_queryset(self):
        section_name = self.kwargs['sectionName']
        latest_result_for_specific_section = ResultList.objects.filter(image__section__name=section_name).latest('date')

        # return ResultList.objects.filter(demo__id=section)
        return [latest_result_for_specific_section]

    # def list(self, request, *args, **kwargs):
    #     queryset = self.get_queryset()
    #     serializer = self.get_serializer(queryset, many=True)
    #     print("aaaaa")
    #     return Response(serializer.data)