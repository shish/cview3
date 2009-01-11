#! /usr/bin/python -u

""" FileLock - Implements a file lock mechanism that does not depend
               on fcntl.

    Copyright (c) 1997-2000, Marc-Andre Lemburg; mailto:mal@lemburg.com
    See the documentation for further information on copyrights,
    or contact the author. All Rights Reserved.

"""
from ExitFunctions import ExitFunctions
import os,exceptions,time,string

# Get fully qualified hostname
def _fqhostname(hostname=None,default=('localhost','127.0.0.1')):

    """ Returns fully qualified (hostname, ip) for the given hostname.

        If hostname is not given, the default name of the local host
        is chosen.

        Defaults to default in case an error occurs while trying to
        determine the data.

    """
    try:
        import socket
    except ImportError:
        return default
    try:
        if hostname is None:
            hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        hostname = socket.gethostbyaddr(ip)[0]
    except socket.error:
        return default
    else:
        return hostname,ip

hostname,ip = _fqhostname()

### Errors

class Error(exceptions.StandardError):
    pass

# Backward compatibility:
FileLockError = Error

### Baseclass using symbolic links

class SymbolicFileLock:

    """ Implements a file lock mechanism that uses symbolic links
        for locking. 

        Note that since the mechanism does not use file system
        function calls this may not always work in the desired
        way.

        The lock is acquired per process, not per thread.

        Instancevariables:
         filename - file the lock applies to
         lockfilename - name of the lock file
         locked - indicator if the lock is in position (1) or not (0)

    """
    # Do we hold the lock ?
    locked = 0

    def __init__(self,filename):

        self.filename = filename
        self.lockfilename = filename + '.locked'
        self.locked = 0
        # Avoid deadlocks
        ExitFunctions.register(self.unlock)

    def __del__(self):

        if self.locked:
            self.unlock(0)
        try:
            ExitFunctions.deregister(self.unlock)
        except:
            pass

    def lock(self,timeout=500,sleeptime=0.0001,

             sleep=time.sleep,Error=Error,time=time.time,error=os.error,
             hostname=hostname,ip=ip):

        """ Try to lock the file for this process, waiting 
            timeout ms if necessary.

            Raises an exception if a timeout occurs. Multiple locking
            by the same process is not an error. 

            Note that a non existent path to the file will also result
            in a timeout.

            If the lock is held by a process running on our host, a
            timeout will first invoke a check of the locking
            process. If it is not alive anymore, the lock is removed
            and granted to the current process.
            
        """
        if self.locked:
            return
        lockfilename = self.lockfilename
        lockinfo = '%s:%i' % (hostname,os.getpid())
        stop = time() + timeout * 0.001
        # Localize these for speed
        islink=os.path.islink
        makelink=os.symlink
        readlink=os.readlink
        while 1:
            # These are rather time-critical
            if not islink(lockfilename):
                try:
                    makelink(lockinfo,lockfilename)
                except error:
                    # A non existent path will result in a time out.
                    pass
                else:
                    break
            sleep(sleeptime)
            if time() > stop:
                # Timeout... 
                try:
                    host,locking_pid = string.split(readlink(lockfilename),':')
                except Error,why:
                    raise Error,\
                          'file "%s" could not be locked: %s' % \
                          (self.filename,why)
                locking_pid = string.atoi(locking_pid)
                if host != hostname:
                    # Ok, then compare via IPs
                    other_ip = _fqhostname(host,default=('???','???'))[1]
                    samehost = (ip == other_ip)
                else:
                    samehost = 1
                if samehost:
                    # Check whether the locking process is still alive
                    try:
                        os.kill(locking_pid,0)
                    except error,why:
                        # It's gone without a trace...
                        try:
                            os.unlink(self.lockfilename)
                        except error:
                            # We probably don't have proper permissions.
                            pass
                        else:
                            continue
                raise Error,\
                      'file "%s" is locked by process %s:%i' % \
                      (self.filename,host,locking_pid,hostname)
        self.locked = 1

    def unlock(self,sleeptime=0.0001,

               unlink=os.unlink,Error=Error,sleep=time.sleep,error=os.error):

        """ Release the lock, letting other processes using this
            mechanism access the file. 

            Multiple unlocking is not an error. Raises an exception if
            the lock file was already deleted by another process.

            After having unlocked the file the process sleeps for
            sleeptime seconds to give other processes a chance to
            acquire the lock too. If the lock will only be used every
            once in a while by the process, it is safe to set it to 0.

        """
        if not self.locked: 
            return
        self.locked = 0
        try:
            unlink(self.lockfilename)
        except error:
            raise Error,'lock file "%s" is already gone' % \
                  self.lockfilename
        # Give other processes a chance too
        if sleeptime:
            sleep(sleeptime)
        return 1

    def remove_lock(self,

                    unlink=os.unlink):

        """ Remove any existing lock on the file.
        """
        self.locked = 0
        try:
            unlink(self.lockfilename)
        except:
            pass

    def __repr__(self):

        return '<%s for "%s" at %x>' % (self.__class__.__name__,
                                        self.filename,
                                        id(self))

# Alias
FileLock = SymbolicFileLock

def _test():
    
    lock = SymbolicFileLock('test.lock')
    for i in range(10000):
        print '%i\r'%i,
        lock.lock()
        time.sleep(i/100000.0)
        lock.unlock()
        #time.sleep(i/100000.0)
    print

if __name__ == '__main__':
    _test()
