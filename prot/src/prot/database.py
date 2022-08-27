from . import data

from .exceptions import AttributeExistsError
from .utils import getRandomString, lister

class DataHolder(object):
    showRoot = True

    def __init__(self, parent=None, identifier=None, allowDuplicate=True, isRoot=False):
        if identifier and not type(identifier) == str:
            raise TypeError(f'identifier must be str object, not {type(identifier)}.')
        self.parent = parent
        self.isRoot = isRoot
        self.id = identifier
        self.allowDuplicate = allowDuplicate
        self.changeableAtts = []
        self.entries = []

    def __bool__(self):
        return True

    def __dir__(self):
        attrs = []
        for f in super().__dir__():
            if f in self.entries:
                attrs.append(f)
        return attrs

    def __len__(self):
        return len(dir(self))

    def __iter__(self):
        return iter(dir(self))

    def __setattr__(self, name, value):
        update = hasattr(self, name)
        if hasattr(self, 'allowDuplicate') and not self.allowDuplicate and hasattr(self, 'changeableAtts') and not name in self.changeableAtts and hasattr(self, name) and getattr(self, name) is not None:
            raise AttributeExistsError(name)
        super().__setattr__(name, value)
        if hasattr(self, 'entries') and not name == 'entries':
            self.addEntry(name, update)

    def __delattr__(self, name):
        super().__delattr__(name)
        try:
            self.entries.remove(name)
        except: pass

    def __getitem__(self, name):
        try:
            if '.' in name:
                item = self
                for i in name.split('.'):
                    item = item[i]
                return item
        except: pass
        return super().__getattribute__(name)

    def __setitem__(self, name, value):
        try:    
            if '.' in name:
                item = self
                set = name.split('.')[-1]
                for i in name.split('.'):
                    if i == set:
                        item[i] = value
                    item = item[i]
                return
        except AttributeError: pass
        self.__setattr__(name, value)

    def __delitem__(self, name):
        try:
            if '.' in name:
                item = self
                delete = name.split('.')[-1]
                for i in name.split('.'):
                    if i == delete:
                        del item[i]
                    item = item[i]
                return
        except: pass
        self.__delattr__(name)

    def __repr__(self):
        return f'<{self.__class__.__name__}>' if not self.tree else f'<{self.__class__.__name__} at {self.tree}>'

    def __str__(self):
        return f'<{self.__class__.__name__}>' if not self.tree else f'<{self.__class__.__name__} at {self.tree}>'

    def addEntry(self, name, update=False):
        if update:
            if name in self.entries:
                self.entries.remove(name)
                self.entries.append(name)
        else:
            self.entries.append(name)

    @property
    def canShow(self):
        if self.showRoot:
            if self.isRoot:
                return True
        else:
            if self.isRoot:
                return False
        return True

    @property
    def tree(self):
        tree = []
        if self.parent and self.parent.id and self.parent.canShow:
            tree.append(self.parent.tree)
        if self.id and self.canShow:
            tree.append(self.id)
        return '.'.join(tree)

    @property
    def store(self):
        store = self
        if store.isRoot and store.id == None:
            return root
        while not (not store == self and store.isRoot and store.id == None):
            if store.parent:
                store = store.parent
            else:
               break
        return store

    @property
    def root(self):
        root = self
        if root.isRoot:
            return root
        while not (not root == self and root.isRoot):
            if root.parent:
                root = root.parent
            else:
               break
        return root

    def new(self, name, object, *args, **kwargs):
        if '.' in name:
            parent = self['.'.join(name.split('.')[:-1])]
            name = name.split('.')[-1]
            return parent.new(name, object, *args, **kwargs)
        else:
            self[name] = None
            id = self.entries[-1]
            if not 'allowDuplicate' in kwargs:
                kwargs['allowDuplicate'] = self.allowDuplicate
            object = object(self, id, *args, **kwargs)
            self[name] = object
            return object

class DataSlot(DataHolder):
    def new(self, name, object=None, *args, **kwargs):
        if not object:
            object = DataSlot
        return super().new(name, object, *args, **kwargs)

class DataStore(DataSlot):
    def __init__(self, allowDuplicate=True):
        super().__init__(allowDuplicate=allowDuplicate, isRoot=True)
        self.new('objects')
        self.new('dataSlots')
        self.new('dicts')

    def new(self, name, object=None, *args, **kwargs):
        if not 'isRoot' in kwargs and not '.' in name:
            kwargs['isRoot'] = True
        return super().new(name, object, *args, **kwargs)

def verifyType(type):
    type = str(type) + 's'
    if not type in data.dataStore:
        raise TypeError(f'type {type[:-1]} is invalid.')
    return type

def registerType(type, handler, object, *args, **kwargs):
    type += 's'
    data.registeredDatabaseTypes[type] = handler
    data.dataStore.new(type, object, *args, **kwargs)

def getTypeHandler(type):
    return data.registeredDatabaseTypes[type]

def register(type, *args, **kwargs):
    type = verifyType(type)
    if type == 'objects':
        object = args[0]
        identifier = None
        while not identifier or hasattr(data.dataStore['objects'], identifier):
            identifier = getRandomString(8, ['numbers'])
        data.dataStore['objects'][identifier] = object
        return identifier
    elif type == 'dataSlots':
        identifier = str(args[0])
        return data.dataStore['dataSlots'].new(identifier)
    elif type == 'dicts':
        identifier = str(args[0])
        value = {} if len(args) < 2 else dict(args[1])
        data.dataStore['dicts'][identifier] = value
    else:
        handler = getTypeHandler(type)
        return handler(*args, **kwargs)

def query(type, identifier=None):
    type = verifyType(type)
    typeHolder = data.dataStore[type]
    if identifier:
        return typeHolder[str(identifier)]
    return typeHolder

def exists(type, identifier=None):
    try:
        query(type, identifier)
        return True
    except AttributeError or KeyError:
        return False

def delete(type, identifier):
    type = verifyType(type)
    del data.dataStore[type][str(identifier)]

data.dataStore = DataStore(False)
for slot, content in data.slots.items():
    for args in content:
        register(slot, *lister(args))