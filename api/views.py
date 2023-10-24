# api/views.py
from rest_framework import generics
from monitor.models import ResultList, Instance
from .serializers import ResultListSerializer
from rest_framework.response import Response


# Using ListAPIView only provide GET method
class ResultListView(generics.ListAPIView):
    serializer_class = ResultListSerializer

    def list(self, request, *args, **kwargs):
        section_name = self.kwargs['sectionName']

        # Retrieve the latest result for the specified section_name
        latest_result_for_section = ResultList.objects.filter(
            image__section__name=section_name
        ).latest('date')

        # Count the instances with predict_class "stalk" in this result
        stalk_count = Instance.objects.filter(
            resultlist_id=latest_result_for_section.id,
            predicted_class="stalk"
        ).count()

        density = determine_density(stalk_count)

        # Build the response data
        response_data = {
            "predict_time": latest_result_for_section.date.strftime("%Y-%m-%d %H:%M:%S"),
            "stalk_count": stalk_count,
            "density": density,
        }

        return Response(response_data)


class BatchSearchView(generics.ListAPIView):
    serializer_class = ResultListSerializer

    def get_queryset(self):
        batch_id = self.kwargs['batchId']
        resultlists = ResultList.objects.filter(demo__id=batch_id)
        return resultlists

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        sections = []
        result_data = []

        for resultlist in queryset:
            sections.append(resultlist.image.section.name)

        result_data = {}
        for section in sections:
            resultlist_per_section = queryset.filter(image__section__name=section)[0]
            stalk_count = Instance.objects.filter(resultlist_id=resultlist_per_section.id, predicted_class="stalk").count()
            density = determine_density(stalk_count)

            result_data[section] = {
                "predict_time": resultlist_per_section.date.strftime("%Y-%m-%d %H:%M:%S"),
                "stalk_count": stalk_count,
                "density": density
            }


        return Response(result_data)


def determine_density(stalk_count):
    if stalk_count > 25:
        density = "high"
    elif 15 <= stalk_count <= 25:
        density = "medium"
    elif stalk_count < 15:
        density = "low"

    return density