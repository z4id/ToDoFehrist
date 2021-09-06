"""
    Defines all custom exception handlers
"""
from rest_framework import status
from rest_framework.response import Response


class HTTPStatusCodeHandler:
    """
        Implements method for handling every exception against
        all HTTP status codes.
    """

    def __init__(self):
        pass

    @staticmethod
    def handler500(request):
        """
        This method handles the HTTP_500_INTERNAL_SERVER_ERROR
        exception and return a specific message to RESTful endpoint.
        """
        status_code_ = status.HTTP_500_INTERNAL_SERVER_ERROR
        msg = 'Internal Server Error occurred while processing your request'
        return Response({"msg": msg}, status=status_code_)
