class PicoServerException(Exception):
    def __init__(self, statusCode:int=500, message:str='internal server error', details:str=""):
        self.statusCode = statusCode
        self.message = message
        self.details = details
        
    def __str__(self):
        return str(self.statusCode)+": "+self.message+" / "+str(self.details)     

class NotFoundException(PicoServerException):
    def __init__(self, details:str=""):
        super().__init__(404,"not found",details)
        
class InternalServerErrorException(PicoServerException):
    def __init__(self, details:str=""):
        super().__init__(500,"internal server error",details)
        
class NotAuthorizedException(PicoServerException):
    def __init__(self, details:str=""):
        super().__init__(401,"not authorized",details)

class BadRequestException(PicoServerException):
    def __init__(self, details:str=""):
        super().__init__(400,"bad request",details)
