from .database import DataHolder, registerType, query
from .exceptions import SessionError, ContextError, handleException
from .utils import getRandomString

class ContextContainer(object):
    def __init__(self):
        self.context = None

    def __getattribute__(self, name):
        if not (name.startswith('__') and name.endswith('__')) and not name in dir(self) and 'context' in dir(self):
            if not self.context:
                handleException(ContextError, 'noneContext')
            return self.context.__getattribute__(name)
        else:
            return super().__getattribute__(name)

    def __setattr__(self, name, value):
        if not (name.startswith('__') and name.endswith('__')) and not name == 'context' and 'context' in dir(self):
            if not self.context:
                handleException(ContextError, 'noneContext')
            self.context.__setattr__(name, value)
        else:
            super().__setattr__(name, value)

    def __delattr__(self, name):
        if not (name.startswith('__') and name.endswith('__')) and not name in dir(self) and 'context' in dir(self):
            if not self.context:
                handleException(ContextError, 'noneContext')
            self.context.__delattr__(name)
        else:
            super().__delattr__(name)

    def __getitem__(self, name):
        return self.__getattribute__(name)

    def __setitem__(self, name, value):
        self.__setattr__(name, value)

    def __delitem__(self, name):
        self.__delattr__(name)

    def __str__(self):
        return f'<context {self.context.__str__()}>'

    def __repr__(self):
        return f'<context {self.context.__repr__()}>'

    def setContext(self, session):
        if self.context:
            self.context.unsetContext()
        self.context = None if not session else session.setContext()
        return self.context

    def getContext(self):
        return self.context

class Context(object):
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        self.oldSession = context.getContext()
        return context.setContext(self.session)

    def __exit__(self, *exc_info):
        context.setContext(self.oldSession)

context = ContextContainer()

class SessionContainer(DataHolder):
    showRoot = False

    def __init__(self, *args, **kwargs):
        self.managers = []
        super().__init__(*args, **kwargs)



    def new(self, name, object, *args, **kwargs):
        manager = super().new(name, object, *args, **kwargs)
        self.managers.append(manager)
        return manager

class SessionManager(DataHolder):
    def __init__(self, *args, **kwargs):
        self.sessions = []
        super().__init__(*args, **kwargs)

    def _setSession(self, session):
        sessions = list(self.sessions)
        sessions.remove(session)
        for session in sessions:
            if session.activated:
                session.deactivate()

    def setSession(self, session):
        session.activate()

    def getSession(self):
        sessions = list(self.sessions)
        sessions.reverse()
        for session in sessions:
            if session.activated:
                return session
        handleException(SessionError, 'noActiveSession')

    def newSession(self, name, object, *args, **kwargs):
        session = super().new(name, object, *args, **kwargs)
        self.sessions.append(session)
        return session

class Session(DataHolder):
    def __init__(self, *args, **kwargs):
        self.status = 'initialized'
        super().__init__(*args, **kwargs)
        self.changeableAtts.append('status')

    def setContext(self):
        if not self.activated:
            self.activate()
        return self

    def unsetContext(self):
        pass

    def start(self):
        if not self.started:
            self.status = 'started'
        else:
            handleException(SessionError, 'started')

    @property
    def started(self):
        return self.status in ['started', 'activated']

    def activate(self):
        if not self.started:
            self.start()
        self.status = 'activated'
        self.parent._setSession(self)

    @property
    def activated(self):
        return self.status == 'activated'

    def deactivate(self):
        if self.activated:
            self.status = 'started'
        else:
            handleException(SessionError, 'notActivated')

    def finish(self):
        if not self.finished:
            self.status = 'finished'
        else:
            handleException(SessionError, 'finished')

    @property
    def finished(self):
        return self.status == 'finished'

def newSessionManager(name, *args, **kwargs):
    sessions = query('session', None)
    return sessions.new(name, *args, **kwargs)

def getSession(manager):
    sessionManager = query('session', manager)
    return sessionManager.getSession()

def newSession(manager, *args, **kwargs):
    sessionManager = query('session', manager)
    identifier = None
    while not identifier or hasattr(sessionManager, identifier):
        identifier = getRandomString(8, ['numbers'])
    return sessionManager.new(identifier, *args, **kwargs)

def setSession(manager, session):
    sessionManager = query('session', manager)
    sessionManager.setSession(session)

def setContext(session):
    return context.setContext(session)

def getContext(manager=None):
    context = context.getContext()
    if manager:
        if context:
            if not context.parent.id == manager:
                context = getSession(manager)
        else:
            context = getSession(manager)
    if not context:
        handleException(ContextError, 'noneContext')
    return context

registerType('session', newSessionManager, SessionContainer)