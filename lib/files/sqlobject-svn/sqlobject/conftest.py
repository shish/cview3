"""
This module is used by py.test to configure testing for this
application.
"""

# Override some options (doesn't override command line):
verbose = 0
exitfirst = True

import py
import os
import sqlobject

try:
    import pkg_resources
except ImportError: # Python 2.2
    pass
else:
    pkg_resources.require('SQLObject')

connectionShortcuts = {
    'mysql': 'mysql://test@localhost/test',
    'dbm': 'dbm:///data',
    'postgres': 'postgres:///test',
    'postgresql': 'postgres:///test',
    'pygresql': 'pygresql://localhost/test',
    'sqlite': 'sqlite:/:memory:',
    'sybase': 'sybase://test:test123@sybase/test?autoCommit=0',
    'firebird': 'firebird://sysdba:masterkey@localhost/var/lib/firebird/data/test.gdb',
    'mssql': 'mssql://sa:@127.0.0.1/test'
    }

Option = py.test.config.Option
option = py.test.config.addoptions(
    "SQLObject options",
    Option('-D', '--Database',
           action="store", dest="Database", default='sqlite',
           help="The database to run the tests under (default sqlite).  "
           "Can also use an alias from: %s"
           % (', '.join(connectionShortcuts.keys()))),
    Option('-S', '--SQL',
           action="store_true", dest="show_sql", default=False,
           help="Show SQL from statements (when capturing stdout the "
           "SQL is only displayed when a test fails)"),
    Option('-O', '--SQL-output',
           action="store_true", dest="show_sql_output", default=False,
           help="Show output from SQL statements (when capturing "
           "stdout the output is only displayed when a test fails)"),
    Option('-E', '--events',
           action="store_true", dest="debug_events", default=False,
           help="Debug events (print information about events as they are "
           "sent)"),
    )

class SQLObjectClass(py.test.collect.Class):
    def run(self):
        if (isinstance(self.obj, type)
            and issubclass(self.obj, sqlobject.SQLObject)):
            return []
        return super(SQLObjectClass, self).run()

Class = SQLObjectClass

def setup_tests():
    if option.debug_events:
        from sqlobject import events
        events.debug_events()
