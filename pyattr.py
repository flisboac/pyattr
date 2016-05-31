
default_impl = object()
'''
A placeholder used to inform that a property's method should be implemented using
the default approach. Used in the context of a property definition, this means
that a property's descriptor method (getter, setter or deleter) should be
trivially implemented.
'''

no_impl = object()
'''
A plceholder used to inform that a property's method should not be implemented.
In other words, the method in question (getter, setter or deleter) will be absent.
'''

# DO NOT CHANGE
def _empty_impl():
    pass
def _empty_impl_doc():
    ""
    pass


def _is_empty_impl(fn):
    '''
    Checks if a function implementation has an empty body.
    Only works with compiled (bytecode) functions. In other words, callables
    other than functions are not eligible.
    '''
    return (_empty_impl.__code__.co_code == fn.__code__.co_code or
            _empty_impl_doc.__code__.co_code == fn.__code__.co_code)


def _full_class_name(o):
    if o is None:
        return "<noclass>"
    if isinstance(o, type):
        return  o.__module__ + "." + o.__name__
    return  o.__module__ + "." + o.__class__.__name__

def _to_seq(o):
    if o is None: return None
    if isinstance(o, list) or isinstance(o, set) or isinstance(o, tuple): return o
    try:
        return [x for x in o]
    except:
        return [o]

class AttrValue(object):
    '''
    A class representing the presence or absence of a value in an object's
    dictionary.
    '''
    def __init__(self, value = None, assigned = None):
        if isinstance(value, type(self)):
            other = value
            value = other.value
            if assigned is None: assigned = other.assigned
        self.value = value
        self.assigned = assigned if assigned is not None else True
    def __str__(self):
        return "<%s assigned='%s' value='%s'>" % (type(self).__name__, str(self.assigned), str(self.value))
    
AttrValue.UNASSIGNED = AttrValue(assigned = False)
AttrValue.NONE = AttrValue()

class Attr(object):

    default_impl = default_impl
    no_impl = no_impl

    def __init__(self,
                 _cls = None,
                 class_field_name = None,
                 doc = None,
                 locked = None):
        if isinstance(_cls, type(self)):
            other = _cls
            _cls = other._cls
            if class_field_name is None: class_field_name = other._class_field_name
            if doc is None: doc = other.__doc__
            if locked is None: locked = other._locked
            self._properties = [_Property(x, attr = self) for x in other._properties]
        else:
            self._properties = []
        self._class_field_name = class_field_name or 'attr'
        self.__doc__ = doc
        self._cls = _cls
        self._locked = locked if locked is not None else False
        
    def __call__(self, _cls = None):
        if _cls is None:
            return lambda fn: self(fn)
        pending_attr = getattr(_cls, self._class_field_name, self)
        if pending_attr is not self:
            pending_attr._locked = self._locked
            pending_attr.__doc__ = self.__doc__
            pending_attr._class_field_name = self._class_field_name
        pending_attr._apply(_cls)
        return _cls
    
    def _apply(self, cls):
        if self._cls:
            raise AssertionError("Attr object already applied to class '%s'" % _full_class_name(self._class))
        self._cls = cls
        if not self.__doc__ and self._cls.__doc__:
            self.__doc__ = self._cls.__doc__
        initializer = self._prepare_initializer(cls = self._cls)
        setattr_fn = self._prepare_setattr(cls = self._cls)
        setattr(self._cls, self._class_field_name, self)
        setattr(self._cls, '__setattr__', setattr_fn)
        setattr(self._cls, '__init__', initializer)
    
    def _prepare_initializer(self,
                             method = None,
                             cls = None,
                             doc = None,
                             initialize_properties = True):
        initializer = self._prepare_method(method, cls, '__init__', doc,
                                      initialize_properties)
        return initializer
    
    def _prepare_setattr(self,
                         method = None,
                         cls = None,
                         doc = None):
        import inspect
        if not method and cls:
            method = getattr(cls, '__setattr__')
            if not method:
                method = object.__setattr__
        special_method_names = ("__init__", 'raw_set')
        def __setattr__(this, key, value):
            if self._locked and not hasattr(this, key) and inspect.stack()[1][3] not in special_method_names:
                this_cls = cls or type(this)                                                                 
                raise AttributeError("Class '{}' is locked, can not set '{}'.".format(this_cls.__name__, key))
            else:
                method(this, key, value)
            #else:
            #    setattr(this, key, value)
        __setattr__._attr = self
        return __setattr__
    
    def _prepare_method(self,
                        method = None,
                        cls = None,
                        name = None,
                        doc = None,
                        initialize_properties = False):
        if not method:
            method = getattr(cls, name, None)
        def modified_method(this, *args, **kwargs):
            if initialize_properties:
                self.initialize_properties(this)
            if method:
                method(this, *args, **kwargs)
        modified_method._attr = self
        if not doc and method:
            doc = method.__doc__
        modified_method.__doc__ = doc # Could do better
        if method:
            modified_method.__name__ = method.__name__
        return modified_method
        
    def property(self, 
                 _fget=None,
                 fset=None,
                 fdel=None,
                 doc=None,
                 name = None,
                 internal_field_name = None,
                 value = AttrValue.UNASSIGNED):
        if _fget is None:
            return lambda fn: self.property(fn, fset, fdel, doc, name,
                                            internal_field_name, value)
        prop = _Property(_fget, fset, fdel, self, doc,
                                 name, internal_field_name, value)
        self._properties.append(prop)
        return prop
            
    def getter(self, 
               _fget=None,
               fdel=None,
               doc=None,
               writable = None,
               deletable = None,
               name = None,
               internal_field_name = None,
               value = AttrValue.UNASSIGNED):
        if _fget is None:
            return lambda fn: self.getter(fn, fdel, doc, writable, deletable, 
                                          name, internal_field_name, value)
        fset = no_impl if not writable else default_impl
        if not fdel:
            fdel = no_impl if not deletable else default_impl
        return self.property(_fget, fset, fdel, doc,
                             name, internal_field_name, value)
    
    def setter(self, 
               _fset=None,
               fdel=None,
               doc=None,
               readable = None,
               deletable = None,
               name = None,
               internal_field_name = None,
               value = AttrValue.UNASSIGNED):
        if _fset is None:
            return lambda fn: self.setter(fn, fdel, doc, readable, deletable, 
                                          name, internal_field_name, value)
        fget = no_impl if not readable else default_impl
        if not fdel:
            fdel = no_impl if not deletable else default_impl
        return self.property(fget, _fset, fdel, doc, 
                             name, internal_field_name, value)
    
    def accessor(self, 
                 _faccessor=None,
                 fdel=None,
                 doc=None,
                 deletable = None,
                 name = None,
                 internal_field_name = None,
                 value = AttrValue.UNASSIGNED):
        if _faccessor is None:
            return lambda fn: self.accessor(fn, fdel, doc, deletable, 
                                            name, internal_field_name, value)
        if not fdel:
            fdel = no_impl if not deletable else default_impl
        return self.property(_faccessor, _faccessor, fdel, doc,
                             name, internal_field_name, value)
    
    def initialize_properties(self, obj, force = False):
        for prop in self._properties:
            prop.initialize_field(obj, force)


class _Property(object):

    def __init__(self,
                 _fget=None,
                 fset=None,
                 fdel=None,
                 attr = None,
                 doc=None,
                 name = None,
                 internal_field_name = None,
                 initial_value = AttrValue.UNASSIGNED):
        if isinstance(_fget, type(self)):
            other = _fget
            _fget = other._get
            if fset is None: fset = other._set
            if fdel is None: fdel = other._del
            if attr is None: attr = other._parent
            if doc is None: doc = other.__doc__
            if name is None: name = other._property_name
            if internal_field_name is None: internal_field_name = other._internal_field_name
            if initial_value is AttrValue.UNASSIGNED: initial_value = other._initial_value
        self._parent = attr
        self._internal_field_name = internal_field_name
        self._initial_value = AttrValue(initial_value)
        self.__doc__ = doc
        self._property_name = name
        self._get = None
        self._set = None
        self._del = None
        self.getter(_fget).setter(fset).deleter(fdel)

    def __get__(self, obj, obj_type=None):
        if obj is None:
            return self
        if self._get is None:
            raise AttributeError("Property '"
                                 + self.get_property_name() + "' from class '"
                                 + _full_class_name(obj) + "' is not readable.")
        return self._get(obj)

    def __set__(self, obj, value):
        if self._set is None:
            raise AttributeError("Property '"
                                 + self.get_property_name() + "' from class '"
                                 + _full_class_name(obj) + "' is not writable.")
        self._set(obj, value)

    def __delete__(self, obj):
        if self._del is None:
            raise AttributeError("Property '"
                                 + self.get_property_name() + "' from class '"
                                 + _full_class_name(obj) + "' is not deletable.")
        self._del(obj)

    def is_getter(self):
        return self._get is not None
    
    def is_setter(self):
        return self._set is not None
    
    def is_accessor(self):
        return self.is_getter() and self.is_setter()
    
    def is_single_accessor(self):
        return self.is_accessor() and self._get == self._set
    
    def get_property_name(self):
        return (self._property_name 
                or (self.is_getter() and self._get.__name__) 
                or (self.is_setter() and self._set.__name__) 
                or None
        )
    
    def get_internal_field_name(self):
        internal_field_name = self._internal_field_name
        if not internal_field_name:
            property_name = self.get_property_name()
            if property_name:
                internal_field_name = "_%s" % property_name
        return internal_field_name
    
    def initialize_field(self, obj, force = False):
        if self._initial_value.assigned and not hasattr(obj, self.get_internal_field_name()):
            self.raw_set(obj, self._initial_value.value)
    
    def raw_get(self, obj, default = AttrValue.UNASSIGNED, fail_if_not_assigned = False):
        value = default
        internal_field_name = self.get_internal_field_name()
        if internal_field_name:
            value = AttrValue(getattr(obj, internal_field_name))
        if not value.assigned and fail_if_not_assigned:
            raise AttributeError("Value not assigned for property '" 
                                 + self.get_property_name() + "' (internal field name: '"
                                 + internal_field_name + "').")
        return value
        
    def raw_set(self, obj, value, fail_if_not_assigned = False):
        success = False
        internal_field_name = self.get_internal_field_name()
        if internal_field_name:
            raw_value = value
            assigned = True
            if isinstance(value, AttrValue):
                raw_value = value.value
                assigned = value.assigned
            if assigned:
                setattr(obj, internal_field_name, raw_value)
                success = True
            elif hasattr(obj, internal_field_name):
                delattr(obj, internal_field_name)
                success = True
        if not success and fail_if_not_assigned:
            raise AttributeError("Could not assign value to property '"
                                 + self.get_property_name() 
                                 + "' (internal field name: '" 
                                 + internal_field_name + "').")
        return success
    
    def raw_del(self, obj, fail_if_not_assigned = False):
        return self.raw_set(obj, AttrValue.UNASSIGNED, fail_if_not_assigned)
        
    def any_get(self, obj, objType = None, default = AttrValue.UNASSIGNED):
        value = None
        if self.is_getter():
            value = AttrValue(self.__get__(obj, objType))
        if not value:
            value = self.raw_get(obj, default)
        return value
    
    def any_set(self, obj, value):
        success = False
        if self.is_setter():
            success = True
            self.__set__(obj, value)
        else:
            value = self.raw_set(obj, value)
        return success
    
    def _set_fn(self, fname, fn, impl):
        if fn is no_impl or fn is None:
            fn = None
        elif fn is default_impl:
            fn = impl
            fn.__name__ = ''
        elif _is_empty_impl(fn):
            impl.__name__ = fn.__name__
            impl.__doc__ = fn.__doc__
            fn = impl
        setattr(self, fname, fn)
        if fn:
            if not self.__doc__:
                self.__doc__ = fn.__doc__
            if not self._property_name:
                self.__name__ = fn.__name__
        return self
    
    def getter(self, _fget):
        return self._set_fn('_get', _fget, lambda this: self.raw_get(this, fail_if_not_assigned = True).value)

    def setter(self, _fset):
        return self._set_fn('_set', _fset, lambda this, value: self.raw_set(this, value, fail_if_not_assigned = True))

    def deleter(self, _fdel):
        return self._set_fn('_del', _fdel, lambda this: self.raw_del(this, fail_if_not_assigned = True))

    
def attr(_cls = None, *args, **kargs):
    if _cls is None:
        return Attr(None, *args, **kargs)
    Attr(_cls, *args, **kargs)
    return _cls
