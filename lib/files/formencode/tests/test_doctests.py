import os, sys

if __name__ == '__main__':
    base = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(base)
try:
    import doctest
    doctest.OutputChecker
except AttributeError:
    import formencode.util.doctest24 as doctest

from formencode import doctest_xml_compare

doctest_xml_compare.install()

text_files = [
    'docs/htmlfill.txt',
    'docs/Validator.txt',
    'tests/non_empty.txt',
    ]

from formencode import validators
from formencode import schema
modules = [validators, schema]

if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    verbose = False
    if '-v' in args:
        args.remove('-v')
        verbose = True
    if not args:
        args = text_files + modules
    for fn in args:
        if isinstance(fn, str):
            fn = os.path.join(base, fn)
            doctest.testfile(fn, module_relative=False,
                             optionflags=doctest.ELLIPSIS,
                             verbose=verbose)
        else:
            doctest.testmod(fn, optionflags=doctest.ELLIPSIS,
                            verbose=verbose)


