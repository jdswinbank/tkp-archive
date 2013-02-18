import unittest
import tempfile
import trap.ingredients.source_extraction
from tkp.testutil import db_subs, db_queries, data

class TestSourceExtraction(unittest.TestCase):
    def __init__(self, *args):
        super(TestSourceExtraction, self).__init__(*args)
        self.dataset_id = db_subs.create_dataset_8images()
        self.parset = tempfile.NamedTemporaryFile()
        parset_text = """\
# extraction threshold (basically S/N) and associetion radius (in units of the default De Ruiter radius) 
# Systematic errors on ra & decl (units in arcsec)
# See Dario Carbone's presentation at TKP Meeting 20121204
detection_threshold = 15
analysis_threshold = 5
#association_radius = 1  # TODO: not used?
backsize_x = 32
backsize_y = 32
margin = 10
deblend = False
deblend_nthresh = 32
radius = 280
ra_sys_err = 20
dec_sys_err = 20
"""
        self.parset.write(parset_text)
        self.parset.flush()

    def test_extract_sources(self):
        image_path = data.fits_file
        trap.ingredients.source_extraction.extract_sources(image_path, self.parset.name)
