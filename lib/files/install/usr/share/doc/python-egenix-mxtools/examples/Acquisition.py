import mx.Tools.NewBuiltins

class AcquisitionMixin:

    """ Mixin class allowing implicit acquisition of attributes from
        objects up a containment hierachy.

        To enable this feature, an object 'b' contained in another
        object 'a' must set the instance variable b.baseobj to
        a. The search is done recursively until either an exception
        is raised by the queried object or the object is found.

        Attributes that strt with an underscore ('_') can not
        be acquired. Be careful when acquiring methods: the method
        will be executed in the baseobjects context, not the one
        it is acquired into.

        See the documentation of acquire() for details.

    """
    baseobj = None              # Base object ("containing" this object)

    # Implicit acquisition
    __getattr__ = acquire       # Use the (new) builtin acquire() to implement
                                # the acquisition mechanism

    def __init__(self,*args,**kw):

        """ Create the object and call startup(*args,**kw)
            - if you give a keyword 'baseobj' then its parameter
              is used to set the baseobj for acquisition; the keyword
              is then deleted from kw
        """
        # Set baseobj for acquisition to work properly
        baseobj = kw.get('baseobj',None)
        if baseobj is not None:
            self.baseobj = baseobj
            del kw['baseobj']
        # call startup()
        apply(self.startup,args,kw)

    def startup(self,*args,**kw):

        """ Override this to init the instance.
        """
        pass

class PythonAcquisitionMixin(AcquisitionMixin):

    def __getattr__(self,name,

                    getattr=getattr,AttributeError=AttributeError):

        if name[0] != '_':
            return getattr(self.baseobj,name)
        raise AttributeError,name

    # Localize these here for speed
    baseobj = AcquisitionMixin.baseobj
    __init__ = AcquisitionMixin.__init__
    startup = AcquisitionMixin.startup

def _test():

    class C(AcquisitionMixin):
        a = 2
        x = 9

    class D(AcquisitionMixin):
        b = 3

    class E(AcquisitionMixin):
        c = 4

    # Setup acquisition chain
    c = C()
    d = D(baseobj=c)
    e = E(baseobj=d)

    # Give implicit acquisition a go...
    print c.a, d.a, e.a
    print d.b, e.b
    print e.c

    d.a = 5
    print c.a, d.a, e.a

    c.b = 1
    print c.b, d.b, e.b
    print
    
    # Performance comparism:
    print 'Performance:'
    print
    import time
    l = range(100000)

    class C(AcquisitionMixin):
        x = 9

    class D(AcquisitionMixin):
        y = 8

    class E(AcquisitionMixin):
        z = 7

    # Setup acquisition chain
    c = C()
    d = D(baseobj=c)
    e = E(baseobj=d)

    t = time.time()
    for i in l:
        e.x
        e.y
        e.z
    print 'AcquisitionMixin:',time.time() - t,'seconds'

    class C(PythonAcquisitionMixin):
        x = 9

    class D(PythonAcquisitionMixin):
        y = 8

    class E(PythonAcquisitionMixin):
        z = 7

    # Setup acquisition chain
    c = C()
    d = D(baseobj=c)
    e = E(baseobj=d)

    t = time.time()
    for i in l:
        e.x
        e.y
        e.z
    print 'PythonAcquisitionMixin:',time.time() - t,'seconds'

if __name__ == '__main__':
    _test()

