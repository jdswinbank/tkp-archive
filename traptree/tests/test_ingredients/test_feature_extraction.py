import unittest
import trap.ingredients.feature_extraction
from tkp.database.database import DataBase
from tkp.database import query
from tkp.classification.transient import Transient
from tkp.testutil import db_subs
from tkp.testutil.decorators import requires_database

@requires_database()
class TestFeatureExtraction(unittest.TestCase):
    def __init__(self, *args):
        super(TestFeatureExtraction, self).__init__(*args)
        self.dataset_id = db_subs.create_dataset_8images(extract_sources=True)

        self.database = DataBase()
        runcat_query = "select id from runningcatalog where dataset=%s"
        cursor = query(self.database.connection, runcat_query, [self.dataset_id])
        self.transients = [Transient(runcatid=i) for (i,) in cursor.fetchall()]

    @unittest.skip("TODO: extract_features recipe needs modification!!!")
    def test_extract_features(self):
        transient = self.transients[0]
        trap.ingredients.feature_extraction.extract_features(transient)
