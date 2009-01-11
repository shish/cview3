""" Helper to enable simple lazy module import. 

    'Lazy' means the actual import is deferred until an attribute is
    requested from the module's namespace. This has the advantage of
    allowing all imports to be done at the top of a script (in a
    prominent and visible place) without having a great impact
    on startup time.

    Copyright (c) 1999-2000, Marc-Andre Lemburg; mailto:mal@lemburg.com
    See the documentation for further information on copyrights,
    or contact the author. All Rights Reserved.
"""
class LazyModule:

    """ Lazy module class.

        Lazy modules are imported into the given namespaces whenever a
        non-special attribute (there are some attributes like __doc__
        that class instances handle without calling __getattr__) is
        requested. The module is then registered under the given name
        in locals usually replacing the import wrapper instance. The
        import itself is done using globals as global namespace.

        Example of creating a lazy load module:

        ISO = LazyModule('ISO',locals(),globals())

        Later, requesting an attribute from ISO will load the module
        automatically into the locals() namespace, overriding the
        LazyModule instance:

        t = ISO.Week(1998,1,1)

    """
    def __init__(self,name,locals,globals=None):

        """ Create a LazyModule instance wrapping module name.

            The module will later on be registered in locals under the
            given module name.

            globals is optional and defaults to locals.
        
        """
        self.__locals__ = locals
        if globals is None:
            globals = locals
        self.__globals__ = globals
        mainname = globals.get('__name__','')
        if mainname:
            self.__name__ = mainname + '.' + name
            self.__importname__ = name
        else:
            self.__name__ = self.__importname__ = name

    def __getattr__(self,what):

        """ Import the module now.
        """
        # Load and register module
        name = self.__importname__
        # print 'Loading module',name
        self.__locals__[name] \
             = module \
             = __import__(name,self.__locals__,self.__globals__,'*')

        # Fill namespace with all symbols from original module to
        # provide faster access.
        self.__dict__.update(module.__dict__)

        # print 'lazy module',name,'import trigger:',what
        return getattr(module,what)

    def __repr__(self):
        return "<lazy module '%s'>" % self.__name__
