""" PackageTools - A set of tools to aid working with packages.

    XXX Still needs some more testing...

    Copyright (c) 1998-2000, Marc-Andre Lemburg; mailto:mal@lemburg.com
    Copyright (c) 2000-2001, eGenix.com Software GmbH; mailto:info@egenix.com
    See the documentation for further information on copyrights,
    or contact the author. All Rights Reserved.
"""
__version__ = '0.2.2'

import os,types,sys,string,re,imp,__builtin__
import mx.Tools.NewBuiltins

# RE to identify Python modules
suffixes = projection(imp.get_suffixes(),0)
module_name = re.compile('(.*)(' + string.join(suffixes,'|') + ')$')
initmodule_name = re.compile('__init__(' + string.join(suffixes,'|') + ')$')

def find_packages(dir=os.curdir,files_only=0,recursive=0,pkgbasename='',
                  pkglist=None,
                  
                  isdir=os.path.isdir,exists=os.path.exists,
                  join=os.path.join,listdir=os.listdir,
                  module_name=module_name,initmodule_name=initmodule_name):

    """ Return a list of package names found in dir.

        Packages are Python modules and subdirectories that provide an
        __init__ module.  The .py extension is removed from the
        files. The __init__ modules are not considered being seperate
        packages.

        If files_only is true, only Python files are included in the
        search (subdirectories are *not* taken into account). If
        recursive is true the search recurses into package
        directories.

        pkgbasename and pkglist are only used during recursion.
        
    """
    l = listdir(dir)
    if pkglist is None:
        pkglist = []
    if files_only:
        for filename in l:
            m = module_name.match(filename)
            if m and m.group(1) != '__init__':
                pkglist.append(pkgbasename+m.group(1))
    else:
        for filename in l:
            path = join(dir,filename)
            if isdir(path):
                # Check for __init__ module(s)
                for file in os.listdir(path):
                    m = initmodule_name.match(file)
                    if m:
                        pkglist.append(pkgbasename+filename)
                        if recursive:
                            find_packages(path,
                                          recursive=1,
                                          pkgbasename=pkgbasename+filename+'.',
                                          pkglist=pkglist)
                        break
            else:
                m = module_name.match(filename)
                if m and m.group(1) != '__init__':
                    pkglist.append(pkgbasename+m.group(1))
    return pkglist

def find_subpackages(package,

                     split=string.split,join=string.join,
                     splitpath=os.path.split):

    """ Assuming that package points to a loaded package module, this
        function tries to identify all subpackages of that package.

        Subpackages are all Python files included in the same
        directory as the module plus all subdirectories having an
        __init__.py file.  The modules name is prepended to all
        subpackage names.

        The module location is found by looking at the __file__
        attribute that non-builtin modules define. The function uses
        the __all__ attribute from the package __init__ module if
        available.
        
    """
    # Try the __all__ attribute...
    try:
        subpackages = list(package.__all__)
    except (ImportError,AttributeError):
        # Did not work, then let's try to find the subpackages by looking
        # at the directory where package lives...
        subpackages = find_packages(package.__path__[0])
    basename = package.__name__ + '.'
    for i,name in irange(subpackages):
        subpackages[i] = basename + name
    return subpackages

def _thismodule(upcount=1,

                exc_info=sys.exc_info,trange=trange):

    """ Returns the module object that the callee is calling from.

        upcount can be given to indicate how far up the execution
        stack the function is supposed to look (1 == direct callee, 2
        == callee of callee, etc.).

    """
    try:
        1/0
    except:
        frame = exc_info()[2].tb_frame
        for i in trange(upcount):
            frame = frame.f_back
    name = frame.f_globals['__name__']
    del frame
    return sys.modules[name]

def import_modules(modnames,module=None,errors='strict',reload=0,

                   thismodule=_thismodule,importer=__import__,
                   reloader=reload):

    """ Import all modules given in modnames into module.

        module defaults to the callees module. modnames may contain
        dotted package names.

        If errors is 'strict' (default), then ImportErrors are
        raised. If set to 'ignore', they are silently ignored.

        If reload is true (default is false), all already modules
        among the list will be forced to reload.
        
    """
    if module is None:
        module = _thismodule(2)
    locals = module.__dict__
    sysmods = sys.modules
    for name in modnames:
        if not sysmods.has_key(name):
            is_new = 1
        else:
            is_new = 0
        try:
            mod = importer(name,locals,locals,['*'])
            if reload and not is_new:
                mod = reloader(mod)
        except ImportError, why:
            if errors == 'ignore':
                continue
            elif errors == 'strict':
                raise ImportError, why
            else:
                raise ValueError,'unkown errors value'
        locals[name] = mod
      
    
def import_subpackages(module,reload=0,

                       import_modules=import_modules,
                       find_subpackages=find_subpackages):

    """ Does a subpackages scan using find_subpackages(module) and then
        imports all submodules found into module.

        The module location is found by looking at the __file__
        attribute that non-builtin modules define. The function uses
        the __all__ attribute from the package __init__ module if
        available.

        If reload is true (default is false), all already modules
        among the list will be forced to reload.
        
    """
    import_modules(find_subpackages(module), module, reload=reload)

def load_modules(modnames,locals=None,globals=None,errors='strict',reload=0,

                 importer=__import__,reloader=reload):

    """ Imports all modules in modnames using the given namespaces and returns
        list of corresponding module objects.

        If errors is 'strict' (default), then ImportErrors are
        raised. If set to 'ignore', they are silently ignored.

        If reload is true (default is false), all already modules
        among the list will be forced to reload.
        
    """
    modules = []
    append = modules.append
    sysmods = sys.modules
    for name in modnames:
        if not sysmods.has_key(name):
            is_new = 1
        else:
            is_new = 0
        try:
            mod = importer(name,locals,locals,['*'])
            if reload and not is_new:
                mod = reloader(mod)
        except ImportError, why:
            if errors == 'ignore':
                continue
            elif errors == 'strict':
                raise ImportError, why
            else:
                raise ValueError,'unkown errors value'
        append(mod)
    return modules
    
def load_subpackages(module,locals=None,globals=None,errors='strict',reload=0,

                     load_modules=load_modules,
                     find_subpackages=find_subpackages):

    """ Same as import_subpackages but with load_modules
        functionality, i.e. imports the modules and also returns a list of
        module objects.

        If errors is 'strict' (default), then ImportErrors are
        raised. If set to 'ignore', they are silently ignored.

        If reload is true (default is false), all already modules
        among the list will be forced to reload.
        
    """
    return load_modules(find_subpackages(module), locals, globals,
                        errors=errors, reload=reload)

def modules(names,

            extract=extract):

    """ Converts a list of module names into a list of module objects.
    
        The modules must already be loaded.

    """
    return extract(sys.modules, names)

def package_modules(pkgname):

    """ Returns a list of all modules belonging to the package with the
        given name.

        The package must already be loaded. Only the currently
        registered modules are included in the list.
        
    """
    match = pkgname + '.'
    match_len = len(match)
    mods = [sys.modules[pkgname]]
    for k,v in sys.modules.items():
        if k[:match_len] == match and v is not None:
            mods.append(v)
    return mods

def find_classes(mods,baseclass=None,annotated=0,

                 ClassType=types.ClassType,issubclass=issubclass):

    """ Find all subclasses of baseclass or simply all classes (if baseclass
        is None) defined by the module objects in list mods.

        If annotated is true the returned list will contain tuples
        (module_object,name,class_object) for each class found where
        module_object is the module where the class is defined.
        
    """
    classes = []
    for mod in mods:
        for name,obj in mod.__dict__.items():
            if type(obj) is ClassType:
                if baseclass and not issubclass(obj,baseclass):
                    continue
                if annotated:
                    classes.append((mod, name, obj))
                else:
                    classes.append(obj)
    return classes

def find_instances(mods,baseclass,annotated=0,

                   InstanceType=types.InstanceType,issubclass=issubclass):

    """ Find all instances of baseclass defined by the module objects
        in list mods.

        If annotated is true the returned list will contain tuples
        (module_object,name,instances_object) for each instances found where
        module_object is the module where the instances is defined.
        
    """
    instances = []
    for mod in mods:
        for name,obj in mod.__dict__.items():
            if isinstance(obj,baseclass):
                if annotated:
                    instances.append((mod,name,obj))
                else:
                    instances.append(obj)
    return instances
