"""
    Views containing for overall emumbaproject
"""
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response


class RootView(APIView):
    """
        Contains get handler for root /, in most cases readiness/health probing
    """

    def get(self, request):
        """
        returns an empty response with 200 HTTP status
        """

        return Response({}, status=status.HTTP_200_OK)
