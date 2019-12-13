## This module holds utility functions for dealing with threads.

import threading


## Decorator function to cause the wrapped function to be called in a new
# thread.
def callInNewThread(func):
    def wrappedFunc(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrappedFunc



## Maps class instances to threading.Locks
INSTANCE_TO_LOCK = dict()
## Lock on accessing/modifying the above.
classLockedLock = threading.Lock()
## Decorator function that prevents the wrapped function from executing at the
# same time as any other similarly-wrapped function for the same class
# instance. Assumes that the class instance is the first argument to the 
# function.
def classLocked(func):
    def wrappedFunc(instance, *args, **kwargs):
        with classLockedLock:
            if instance not in INSTANCE_TO_LOCK:
                INSTANCE_TO_LOCK[instance] = threading.Lock()
        with INSTANCE_TO_LOCK[instance]:
            func(instance, *args, **kwargs)
    return wrappedFunc
