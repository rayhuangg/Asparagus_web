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

        if stalk_count > 25:
            density = "low"
        elif 15 <= stalk_count <= 25:
            density = "medium"
        elif stalk_count < 15:
            density = "low"

        # Build the response data
        response_data = {
            "predice_time": latest_result_for_section.date.strftime("%Y-%m-%d %H:%M:%S"),
            "stalk_count": stalk_count,
            "density": density,
        }

        return Response(response_data)