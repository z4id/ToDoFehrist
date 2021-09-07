"""
    Defines all custom exception handlers
"""
from rest_framework import status
from todofehrist.utility import BaseAPIView


class HTTPStatusCodeHandler(BaseAPIView):
    """
        Implements method for handling every exception against
        all HTTP status codes.
    """

    def handler500(self, request):
        """
        This method handles the HTTP_500_INTERNAL_SERVER_ERROR
        exception and return a specific message to RESTful endpoint.
        """
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return self.response({}, "", "Something went wrong",
                                 "Internal Server Error, Try Again.",
                                 status_code)
