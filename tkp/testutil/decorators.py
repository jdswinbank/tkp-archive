import os
import tkp.config

import unittest
from tkp.testutil import db_subs

if not  hasattr(unittest.TestCase, 'assertIsInstance'):
    import unittest2 as unittest

def requires_database():
    if tkp.config.config['database']['enabled']:
        db_subs.use_test_database_by_default()
        return lambda func: func
    return unittest.skip("Database functionality disabled in configuration")

def requires_data(*args):
    for filename in args:
        if not os.path.exists(filename):
            return unittest.skip("Test data (%s) not available" % filename)
    return lambda func: func

def requires_module(module_name):
    try:
        __import__(module_name)
    except ImportError:
        return unittest.skip("Required module (%s) not available" % module_name)
    return lambda func: func

def duration(test_duration):
    if tkp.config.config['test']['max_duration']:
        if tkp.config.config['test']['max_duration'] < test_duration:
            return unittest.skip(
             "Tests of duration > %s disabled in tkp.config['test'] section." %
                tkp.config.config['test']['max_duration'])
    return lambda func: func
