import threading
import time
import util.threads
import unittest

class TestThreadFunctions(unittest.TestCase):

    def test_call(self):
        @util.threads.callInNewThread
        def func():
            time.sleep(0.5)

        thread = func()
        self.assertTrue(thread.isAlive())
        self.assertNotEquals(thread, threading.currentThread)
        thread.join(1.0)
        self.assertFalse(thread.isAlive())

    def test_args(self):
        @util.threads.callInNewThread
        def func(callback, *args):
            callback(args)

        args = [1,2,3]
        check_args = []
        func(lambda x: check_args.extend(x),1,2,3)
        self.assertEquals(args, check_args)





