from rest_framework import status
from rest_framework.response import Response


class HTTPStatusCodeHandler:

    def __init__(self):
        pass

    @staticmethod
    def handler500(request):
        status_code_ = status.HTTP_500_INTERNAL_SERVER_ERROR
        msg = 'Internal Server Error occurred while processing your request'
        return Response({"msg": msg}, status=status_code_)
