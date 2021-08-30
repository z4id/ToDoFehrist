import logging


class LoggingRequestResponse(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        logging.info({"request": request.__dict__, "response": response.__dict__})

        return response
