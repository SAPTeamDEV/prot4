class ProtException(Exception):
    '''
    base exception for prot exception classes.
    '''

    reprMessage = False

    def __init__(self, message):
        if self.reprMessage:
            super().__init__(repr(message))
        else:
            super().__init__(message)

    @staticmethod
    def getMessages():
        return {}

class PackageNotFoundError(ProtException):
    '''
    package not found.
    '''

    reprMessage = True

class ModeError(ProtException):
    '''
    operation not supported in selected mode.
    '''

    pass

class FileTypeError(ProtException):
    '''
    file type not supported.
    '''

    pass

class ColorNotFoundError(ProtException):
    '''
    color not found.
    '''

    pass

class AttributeExistsError(ProtException):
    '''
    attribute already exists.
    '''

    reprMessage = True

class ProgressError(ProtException):
    '''
    error occured while processing Progress or Widget objects.
    '''

    pass

class ProgramNameNotRegistedError(ProtException):
    '''
    program name not registered.
    '''

    pass

class SessionError(ProtException):
    '''
    error occured in a session operation.
    '''

    @staticmethod
    def getMessages():
        return {
                'noActiveSession': 'active session not found.',
                'started': 'session already started.',
                'finished': 'session already finished.',
                'notActivated': 'session not activated.',
                }

class ContextError(ProtException):
    '''
    error occured in a context operation.
    '''

    @staticmethod
    def getMessages():
        return {
                'noneContext': 'current context is none.',
                }

def handleException(exception, message=''):
    if not isinstance(exception, ProtException):
        raise TypeError(f'exception {exception} not supported.')
    raise exception(exception.getMessages()[message])