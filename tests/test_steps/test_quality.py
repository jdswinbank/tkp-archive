import unittest
import tkp.steps.quality
import tkp.accessors
import tkp.testutil.data as testdata
from tkp.testutil.decorators import requires_database
import tkp.utility.parset as parset
from tkp.testutil.data import default_parset_paths

@requires_database()
class TestQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.accessor = tkp.accessors.open(testdata.casa_table)
        with open(default_parset_paths['quality_check.parset']) as f:
            cls.parset = parset.read_config_section(f, 'quality_lofar')

    def test_check(self):
        tkp.steps.quality.reject_check(self.accessor.url, self.parset)
