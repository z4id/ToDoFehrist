"""
    Contains all custom middleware classes written for todofehrist app.
"""
import logging


class LoggingRequestResponse:
    """
        This class is implements functionality to log all requests
        and responses to/from todofehrist RESTful endpoints.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        This method will be invoked by django for every request.
        It will log request and corresponding response to default
        root logger (set in Settings.py)
        """
        response = self.get_response(request)

        logging.info({"request": request.__dict__, "response": response.__dict__})

        return response
