# represents exceptions associated with API calls and setup

class APIException(Exception):
    pass

class APIConnectionException(APIException):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.status_code = status_code

class APIResponseException(APIConnectionException):
    def __init__(self, message, status_code, request_endpoint, request_params, response_json):
        super().__init__(message, status_code)
        self.status_code = status_code
        self.request_endpoint = request_endpoint
        self.request_params = request_params
        self.response_json = response_json

class APIRateLimitedException(APIConnectionException):
    pass

class APIUnreachableException(APIConnectionException):
    pass

class APIEndpointRejectedException(APIException):
    pass

class APIKeyFileInvalid(APIException):
    pass

class APIConfigFileInvalid(APIException):
    pass