import unittest2 as unittest
import tkp.db
from tkp.db import monitoringlist
from tkp.testutil import db_subs
from tkp.testutil.decorators import requires_database
from tkp.db import associations as dbass
from tkp.db import transients as tr_search


class TestIntermittentToMonitorlist(unittest.TestCase):
    """
    These tests will check an intermittent source, having
    a null-detection in the second image out of three images.
    This source should end up in the monitoringlist
    """
    @requires_database()
    def setUp(self):
        self.database = tkp.db.Database()

    def tearDown(self):
        tkp.db.rollback()

    def test_intermittentToMonitorlist(self):
        dataset = tkp.db.DataSet(database=self.database, data={'description': "Monlist:" + self._testMethodName})
        n_images = 3
        im_params = db_subs.example_dbimage_datasets(n_images)

        steady_srcs = []
        # We will work with 2 sources per image
        # one being detected in all images and not in the monlist
        # the second having a null-detection in the second image
        # and stored in the monlist
        n_steady_srcs = 2
        for i in range(n_steady_srcs):
            src = db_subs.example_extractedsource_tuple()
            src = src._replace(ra=src.ra + 2 * i)
            steady_srcs.append(src)

        for idx, im in enumerate(im_params):
            image = tkp.db.Image(database=self.database, dataset=dataset, data=im)

            if idx == 1:
                # The second image has a null detection, so only the first source is detected
                image.insert_extracted_sources(steady_srcs[0:1])
            else:
                image.insert_extracted_sources(steady_srcs)

            # First, we check for null detections
            nd = monitoringlist.get_nulldetections(image.id, deRuiter_r=3.717)

            if idx == 0:
                self.assertEqual(len(nd), 0)
            elif idx == 1:
                self.assertEqual(len(nd), 1)
                # The null detection is found,
                # We simulate the forced fit result back into extractedsource
                # Check that the null-detection ra is the ra of source two
                self.assertEqual(nd[0][0], steady_srcs[1].ra)
                #print "nd=",nd
                tuple_ff_nd = steady_srcs[1:2]
                monitoringlist.insert_forcedfits_into_extractedsource(image.id, tuple_ff_nd, 'ff_nd')
            elif idx == 2:
                self.assertEqual(len(nd), 0)

            # Secondly, we do the source association
            dbass.associate_extracted_sources(image.id, deRuiter_r=3.717)
            monitoringlist.add_nulldetections(image.id)
            # We also need to run the transient search in order to pick up the variable
            # eta_lim, V_lim, prob_threshold, minpoints, resp.
            transients = tr_search.multi_epoch_transient_search(image.id,
                                                     0.0,
                                                     0.0,
                                                     0.5,
                                                     1)

            # Adjust (insert/update/remove) transients in monlist as well
            monitoringlist.adjust_transients_in_monitoringlist(image.id,
                                                               transients)

        # So after the three images have been processed,
        # We should have the null-detection source in the monlist

        # Get the null detection in extractedsource
        # These are of extract_type = 1
        query = """\
        select x.id
          from extractedsource x
              ,image i
         where x.image = i.id
           and i.dataset = %s
           and x.extract_type = 1
        """
        self.database.cursor.execute(query, (dataset.id,))
        result = zip(*self.database.cursor.fetchall())
        null_det = result[0]
        self.assertEqual(len(null_det), 1)

        query = """\
        select a.runcat
              ,a.xtrsrc
              ,r.wm_ra
              ,r.wm_decl
          from assocxtrsource a
              ,extractedsource x
              ,image i
              ,runningcatalog r
         where a.xtrsrc = x.id
           and x.id = %s
           and x.image = i.id
           and i.dataset = %s
           and a.runcat = r.id
           and r.dataset = i.dataset
        """
        self.database.cursor.execute(query, (null_det[0], dataset.id,))
        result = zip(*self.database.cursor.fetchall())
        assocruncat = result[0]
        xtrsrc = result[1]
        wm_ra = result[2]
        wm_decl = result[3]
        self.assertEqual(len(assocruncat), 1)

        query = """\
        SELECT runcat
              ,ra
              ,decl
          FROM monitoringlist
         WHERE dataset = %s
        """
        self.database.cursor.execute(query, (dataset.id,))
        result = zip(*self.database.cursor.fetchall())
#        print "len(result)=",len(result)
        self.assertEqual(len(result), 3)
        #self.assertEqual(0, 1)
        monruncat = result[0]
        ra = result[1]
        decl = result[2]
        self.assertEqual(len(monruncat), 1)
        self.assertEqual(monruncat[0], assocruncat[0])
        self.assertEqual(ra[0], wm_ra[0])
        self.assertAlmostEqual(decl[0], wm_decl[0])
