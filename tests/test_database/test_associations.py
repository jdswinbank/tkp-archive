import math

import unittest2 as unittest

import tkp.db
import tkp.db.general as dbgen
from tkp.db.orm import DataSet
from tkp.db.associations import associate_extracted_sources
from tkp.db.generic import columns_from_table
from tkp.testutil import db_subs
from tkp.testutil.decorators import requires_database


@requires_database()
class TestOne2One(unittest.TestCase):
    """
    These tests will check the 1-to-1 source associations, i.e. an extractedsource
    has exactly one counterpart in the runningcatalog
    """
    def shortDescription(self):
        """http://www.saltycrane.com/blog/2012/07/how-prevent-nose-unittest-using-docstring-when-verbosity-2/"""
        return None

    def tearDown(self):
        tkp.db.rollback()

    def test_one2one(self):
        dataset = DataSet(data={'description': 'assoc test set: 1-1'})
        n_images = 8
        im_params = db_subs.example_dbimage_datasets(n_images)

        steady_srcs = []
        n_steady_srcs = 3
        for i in range(n_steady_srcs):
            src = db_subs.example_extractedsource_tuple()
            src = src._replace(ra=src.ra + 2 * i)
            steady_srcs.append(src)

        for im in im_params:
            image = tkp.db.Image(dataset=dataset, data=im)
            dbgen.insert_extracted_sources(image.id, steady_srcs, 'blind')
            associate_extracted_sources(image.id, deRuiter_r = 3.717)

        # Check runningcatalog, runningcatalog_flux, assocxtrsource.
        # note that the order of insertions is not garanteed, so we ORDER by
        # wm_RA
        query = """\
        SELECT datapoints
              ,wm_ra
              ,wm_decl
              ,wm_ra_err
              ,wm_decl_err
              ,x
              ,y
              ,z
          FROM runningcatalog
         WHERE dataset = %s
        ORDER BY wm_ra
        """
        cursor = tkp.db.execute(query, (dataset.id,))
        runcat = zip(*cursor.fetchall())
        self.assertNotEqual(len(runcat), 0)
        dp = runcat[0]
        wm_ra = runcat[1]
        wm_decl = runcat[2]
        wm_ra_err = runcat[3]
        wm_decl_err = runcat[4]
        x = runcat[5]
        y = runcat[6]
        z = runcat[7]
        # Check for 1 entry in runcat
        self.assertEqual(len(dp), len(steady_srcs))
        self.assertEqual(dp[0], n_images)
        self.assertAlmostEqual(wm_ra[0], steady_srcs[0].ra)
        self.assertAlmostEqual(wm_decl[0], steady_srcs[0].dec)
        self.assertAlmostEqual(wm_ra_err[0], math.sqrt(
                           1./ (n_images / ( (steady_srcs[0].ra_fit_err*3600.)**2 + (steady_srcs[0].ra_sys_err)**2))
                               ))
        self.assertAlmostEqual(wm_decl_err[0], math.sqrt(
                           1./ (n_images / ((steady_srcs[0].dec_fit_err*3600.)**2 + (steady_srcs[0].dec_sys_err)**2 ))
                               ))

        self.assertAlmostEqual(x[0],
                    math.cos(math.radians(steady_srcs[0].dec))*
                        math.cos(math.radians(steady_srcs[0].ra)))
        self.assertAlmostEqual(y[0],
                   math.cos(math.radians(steady_srcs[0].dec))*
                        math.sin(math.radians(steady_srcs[0].ra)))
        self.assertAlmostEqual(z[0], math.sin(math.radians(steady_srcs[0].dec)))

        # Check that xtrsrc ids in assocxtrsource are the ones from extractedsource
        query ="""\
        SELECT a.runcat
              ,a.xtrsrc
          FROM assocxtrsource a
              ,runningcatalog r
         WHERE a.runcat = r.id
           AND r.dataset = %s
        ORDER BY a.xtrsrc
        """
        cursor = tkp.db.execute(query, (dataset.id,))
        assoc = zip(*cursor.fetchall())
        self.assertNotEqual(len(assoc), 0)
        aruncat = assoc[0]
        axtrsrc = assoc[1]
        self.assertEqual(len(axtrsrc), n_images * n_steady_srcs)

        query = """\
        SELECT x.id
          FROM extractedsource x
              ,image i
         WHERE x.image = i.id
           AND i.dataset = %s
        ORDER BY x.id
        """
        cursor = tkp.db.execute(query, (dataset.id,))
        xtrsrcs = zip(*cursor.fetchall())
        self.assertNotEqual(len(xtrsrcs), 0)
        xtrsrc = xtrsrcs[0]
        self.assertEqual(len(xtrsrc), n_images * n_steady_srcs)

        for i in range(len(xtrsrc)):
            self.assertEqual(axtrsrc[i], xtrsrc[i])

        # Check runcat_fluxes
        query = """\
        SELECT rf.band
              ,rf.stokes
              ,rf.f_datapoints
              ,rf.avg_f_peak
              ,rf.avg_f_peak_weight
              ,rf.avg_f_int
              ,rf.avg_f_int_weight
          FROM runningcatalog_flux rf
              ,runningcatalog r
         WHERE r.id = rf.runcat
           AND r.dataset = %s
        """
        cursor = tkp.db.execute(query, (dataset.id,))
        fluxes = zip(*cursor.fetchall())
        self.assertNotEqual(len(fluxes), 0)
        f_datapoints = fluxes[2]
        avg_f_peak = fluxes[3]
        avg_f_peak_weight = fluxes[4]
        avg_f_int = fluxes[5]
        avg_f_int_weight = fluxes[6]
        self.assertEqual(len(f_datapoints), n_steady_srcs)
        self.assertEqual(f_datapoints[0], n_images)
        self.assertEqual(avg_f_peak[0], steady_srcs[0].peak)
        self.assertEqual(avg_f_peak_weight[0], 1./steady_srcs[0].peak_err**2)
        self.assertEqual(avg_f_int[0], steady_srcs[0].flux)
        self.assertEqual(avg_f_int_weight[0], 1./steady_srcs[0].flux_err**2)


@requires_database()
class TestMixedSkyregions(unittest.TestCase):
    """
    Tests that association and related calculations happen correctly when a
    source is seen in multiple skyregions.
    """
    def shortDescription(self):
        return None

    def tearDown(self):
        tkp.db.rollback()

    def TestCrossMeridian(self):
        """
        A source is observed in two skyregions: one which crosses the
        meridian, and one which does not. We check that the associated source
        has the correct weighted mean RA.

        See also #4497.
        """
        dataset = DataSet(data={'description': "Test:" + self._testMethodName})

        im_list = [
            db_subs.example_dbimage_datasets(
                n_images=1, centre_ra=0, centre_decl=0, xtr_radius=10
            )[0],
            db_subs.example_dbimage_datasets(
                n_images=1, centre_ra=0, centre_decl=0, xtr_radius=10
            )[0],
            db_subs.example_dbimage_datasets(
                n_images=1, centre_ra=15, centre_decl=0, xtr_radius=10
            )[0],
            db_subs.example_dbimage_datasets(
                n_images=1, centre_ra=15, centre_decl=0, xtr_radius=10
            )[0],
        ]

        source_ra = 7.5
        src = db_subs.example_extractedsource_tuple(ra=source_ra, dec=0)

        for im in im_list:
            image = tkp.db.Image(dataset=dataset, data=im)
            image.insert_extracted_sources([src])
            associate_extracted_sources(image.id, deRuiter_r=3.717)

        runcat = columns_from_table('runningcatalog', ['wm_ra'],
            where={'dataset': dataset.id}
        )
        self.assertAlmostEqual(runcat[0]['wm_ra'], source_ra)


#@unittest.skip
@requires_database()
class TestMeridianOne2One(unittest.TestCase):
    """
    These tests will check the 1-to-1 source associations, i.e. an extractedsource
    has exactly one counterpart in the runningcatalog
    """
    def shortDescription(self):
        return None

    def tearDown(self):
        tkp.db.rollback()

    def TestMeridianCrossLowHighEdgeCase(self):
        """What happens if a source is right on the meridian?"""

        dataset = DataSet(data={'description':"Assoc 1-to-1:" + self._testMethodName})
        n_images = 3
        im_params = db_subs.example_dbimage_datasets(n_images, centre_ra=0.5,
                                                      centre_decl=10)
        src_list = []
        src0 = db_subs.example_extractedsource_tuple(ra=0.0001, dec=10.5,
                                             ra_fit_err=0.01, dec_fit_err=0.01)
        src_list.append(src0)
        src1 = src0._replace(ra=0.0003)
        src_list.append(src1)
        src2 = src0._replace(ra=359.9999)
        src_list.append(src2)

        for idx, im in enumerate(im_params):
            im['centre_ra'] = 359.9
            image = tkp.db.Image(dataset=dataset, data=im)
            image.insert_extracted_sources([src_list[idx]])
            associate_extracted_sources(image.id, deRuiter_r=3.717)
        runcat = columns_from_table('runningcatalog', ['datapoints', 'wm_ra'],
                                   where={'dataset':dataset.id})
#        print "***\nRESULTS:", runcat, "\n*****"
        self.assertEqual(len(runcat), 1)
        self.assertEqual(runcat[0]['datapoints'], 3)
        avg_ra = ((src0.ra+180)%360 + (src1.ra+180)%360 + (src2.ra+180)%360)/3 - 180
        self.assertAlmostEqual(runcat[0]['wm_ra'], avg_ra)

    def TestMeridianCrossHighLowEdgeCase(self):
        """What happens if a source is right on the meridian?"""

        dataset = DataSet(data={'description':"Assoc 1-to-1:" + self._testMethodName})
        n_images = 3
        im_params = db_subs.example_dbimage_datasets(n_images, centre_ra=0.5,
                                                      centre_decl=10)
        src_list = []
        src0 = db_subs.example_extractedsource_tuple(ra=359.9999, dec=10.5,
                                             ra_fit_err=0.01, dec_fit_err=0.01)
        src_list.append(src0)
        src1 = src0._replace(ra=0.0003)
        src_list.append(src1)
        src2 = src0._replace(ra=0.0001)
        src_list.append(src2)

        for idx, im in enumerate(im_params):
            im['centre_ra'] = 359.9
            image = tkp.db.Image(dataset=dataset, data=im)
            image.insert_extracted_sources([src_list[idx]])
            associate_extracted_sources(image.id, deRuiter_r=3.717)
        runcat = columns_from_table(
                                   'runningcatalog', ['datapoints', 'wm_ra'],
                                   where={'dataset':dataset.id})
#        print "***\nRESULTS:", runcat, "\n*****"
        self.assertEqual(len(runcat), 1)
        self.assertEqual(runcat[0]['datapoints'], 3)
        avg_ra = ((src0.ra+180)%360 + (src1.ra+180)%360 + (src2.ra+180)%360)/3 - 180
        self.assertAlmostEqual(runcat[0]['wm_ra'], avg_ra)

    def TestMeridianHigherEdgeCase(self):
        """What happens if a source is right on the meridian?"""

        dataset = DataSet(data={'description':"Assoc 1-to-1:" + self._testMethodName})
        n_images = 3
        im_params = db_subs.example_dbimage_datasets(n_images, centre_ra=0.5,
                                                      centre_decl=10)
        src_list = []
        src0 = db_subs.example_extractedsource_tuple(ra=359.9983, dec=10.5,
                                             ra_fit_err=0.01, dec_fit_err=0.01)
        src_list.append(src0)
        src1 = src0._replace(ra=359.9986)
        src_list.append(src1)
        src2 = src0._replace(ra=359.9989)
        src_list.append(src2)

        for idx, im in enumerate(im_params):
            im['centre_ra'] = 359.9
            image = tkp.db.Image(dataset=dataset, data=im)
            image.insert_extracted_sources([src_list[idx]])
            associate_extracted_sources(image.id, deRuiter_r=3.717)
        runcat = columns_from_table('runningcatalog', ['datapoints', 'wm_ra'],
                                   where={'dataset':dataset.id})
#        print "***\nRESULTS:", runcat, "\n*****"
        self.assertEqual(len(runcat), 1)
        self.assertEqual(runcat[0]['datapoints'], 3)
        avg_ra = (src0.ra + src1.ra +src2.ra)/3
        self.assertAlmostEqual(runcat[0]['wm_ra'], avg_ra)

    def TestMeridianLowerEdgeCase(self):
        """What happens if a source is right on the meridian?"""

        dataset = DataSet(data={'description':"Assoc 1-to-1:" +
                                self._testMethodName})
        n_images = 3
        im_params = db_subs.example_dbimage_datasets(n_images, centre_ra=0.5,
                                                      centre_decl=10)
        src_list = []
        src0 = db_subs.example_extractedsource_tuple(ra=0.0002, dec=10.5,
                                             ra_fit_err=0.01, dec_fit_err=0.01)
        src_list.append(src0)
        src1 = src0._replace(ra=0.0003)
        src_list.append(src1)
        src2 = src0._replace(ra=0.0004)
        src_list.append(src2)

        for idx, im in enumerate(im_params):
            im['centre_ra'] = 359.9
            image = tkp.db.Image(dataset=dataset, data=im)
            image.insert_extracted_sources([src_list[idx]])
            associate_extracted_sources(image.id, deRuiter_r=3.717)
        runcat = columns_from_table('runningcatalog', ['datapoints', 'wm_ra'],
                                   where={'dataset':dataset.id})
#        print "***\nRESULTS:", runcat, "\n*****"
        self.assertEqual(len(runcat), 1)
        self.assertEqual(runcat[0]['datapoints'], 3)
        avg_ra = (src0.ra + src1.ra +src2.ra)/3
        self.assertAlmostEqual(runcat[0]['wm_ra'], avg_ra)

    def TestDeRuiterCalculation(self):
        """Check all the unit conversions are correct"""
        dataset = DataSet(data={'description':"Assoc 1-to-1:" + self._testMethodName})
        n_images = 2
        im_params = db_subs.example_dbimage_datasets(n_images, centre_ra=10,
                                                     centre_decl=0)


        #Note ra / ra_fit_err are in degrees.
        # ra_sys_err is in arcseconds, but we set it = 0 so doesn't matter.
        #ra_fit_err cannot be zero or we get div by zero errors.
        #Also, there is a hard limit on association radii:
        #currently this defaults to 0.03 degrees== 108 arcseconds
        src0 = db_subs.example_extractedsource_tuple(ra=10.00, dec=0.0,
                                             ra_fit_err=0.1, dec_fit_err=1.00,
                                             ra_sys_err=0.0, dec_sys_err=0.0)
        src1 = db_subs.example_extractedsource_tuple(ra=10.02, dec=0.0,
                                             ra_fit_err=0.1, dec_fit_err=1.00,
                                             ra_sys_err=0.0, dec_sys_err=0.0)
        src_list = [src0, src1]
        #NB dec_fit_err nonzero, but since delta_dec==0 this simplifies to:
        expected_DR_radius = math.sqrt((src1.ra - src0.ra) ** 2 /
                               (src0.ra_fit_err ** 2 + src1.ra_fit_err ** 2))
#        print "Expected DR", expected_DR_radius

        for idx in [0, 1]:
            image = tkp.db.Image(dataset=dataset,
                                data=im_params[idx])
            image.insert_extracted_sources([src_list[idx]])
            #Peform very loose association since we just want to store DR value.
            associate_extracted_sources(image.id, deRuiter_r=100)
        runcat = columns_from_table('runningcatalog', ['id'],
                                   where={'dataset':dataset.id})
#        print "***\nRESULTS:", runcat, "\n*****"
        self.assertEqual(len(runcat), 1)
        assoc = columns_from_table('assocxtrsource', ['r'],
                                   where={'runcat':runcat[0]['id']})
#        print "Got assocs:", assoc
        self.assertEqual(len(assoc), 2)
        self.assertAlmostEqual(assoc[1]['r'], expected_DR_radius)


class TestOne2Many(unittest.TestCase):
    """
    These tests will check the 1-to-many source associations, i.e. two extractedsources
    have the same one counterpart in the runningcatalog
    """
    @requires_database()
    def setUp(self):
        self.database = tkp.db.Database()

    def tearDown(self):
        """remove all stuff after the test has been run"""
        tkp.db.rollback()

    def test_one2many(self):
        dataset = DataSet(data={'description': 'assoc test set: 1-n'})
        n_images = 2
        im_params = db_subs.example_dbimage_datasets(n_images)

        # image 1
        image = tkp.db.Image(dataset=dataset, data=im_params[0])
        imageid1 = image.id
        src = []
        # 1 source
        src.append(db_subs.example_extractedsource_tuple(ra=123.1235, dec=10.55,
                                                     ra_fit_err=5./3600, dec_fit_err=6./3600,
                                                     peak = 15e-3, peak_err = 5e-4,
                                                     flux = 15e-3, flux_err = 5e-4,
                                                     sigma = 15,
                                                     beam_maj = 100, beam_min = 100, beam_angle = 45,
                                                     ra_sys_err=20, dec_sys_err=20
                                                        ))
        results = []
        results.append(src[-1])
        dbgen.insert_extracted_sources(imageid1, results, 'blind')
        associate_extracted_sources(imageid1, deRuiter_r = 3.717)

        query = """\
        SELECT id
          FROM extractedsource
         WHERE image = %s
        """
        self.database.cursor.execute(query, (imageid1,))
        im1 = zip(*self.database.cursor.fetchall())
        self.assertNotEqual(len(im1), 0)
        im1src1 = im1[0]
        self.assertEqual(len(im1src1), 1)

        query = """\
        SELECT id
              ,xtrsrc
          FROM runningcatalog
         WHERE dataset = %s
        """
        self.database.cursor.execute(query, (dataset.id,))
        rc1 = zip(*self.database.cursor.fetchall())
        self.assertNotEqual(len(rc1), 0)
        runcat1 = rc1[0]
        xtrsrc1 = rc1[1]
        self.assertEqual(len(runcat1), len(src))
        self.assertEqual(xtrsrc1[0], im1src1[0])

        query = """\
        SELECT a.runcat
              ,a.xtrsrc
              ,a.type
          FROM assocxtrsource a
              ,runningcatalog r
         WHERE a.runcat = r.id
           AND r.dataset = %s
        """
        self.database.cursor.execute(query, (dataset.id,))
        assoc1 = zip(*self.database.cursor.fetchall())
        self.assertNotEqual(len(assoc1), 0)
        aruncat1 = assoc1[0]
        axtrsrc1 = assoc1[1]
        atype = assoc1[2]
        self.assertEqual(len(aruncat1), len(src))
        self.assertEqual(axtrsrc1[0], im1src1[0])
        self.assertEqual(axtrsrc1[0], xtrsrc1[0])
        self.assertEqual(atype[0], 4)
        #TODO: Add runcat_flux test

        # image 2
        image = tkp.db.Image(dataset=dataset, data=im_params[1])
        imageid2 = image.id
        src = []
        # 2 sources (located close to source 1, catching the 1-to-many case
        src.append(db_subs.example_extractedsource_tuple(ra=123.12349, dec=10.549,
                                                     ra_fit_err=5./3600, dec_fit_err=6./3600,
                                                     peak = 15e-3, peak_err = 5e-4,
                                                     flux = 15e-3, flux_err = 5e-4,
                                                     sigma = 15,
                                                     beam_maj = 100, beam_min = 100, beam_angle = 45,
                                                     ra_sys_err=20, dec_sys_err=20
                                                        ))
        src.append(db_subs.example_extractedsource_tuple(ra=123.12351, dec=10.551,
                                                     ra_fit_err=5./3600, dec_fit_err=6./3600,
                                                     peak = 15e-3, peak_err = 5e-4,
                                                     flux = 15e-3, flux_err = 5e-4,
                                                     sigma = 15,
                                                     beam_maj = 100, beam_min = 100, beam_angle = 45,
                                                     ra_sys_err=20, dec_sys_err=20
                                                        ))
        results = []
        results.append(src[0])
        results.append(src[1])
        dbgen.insert_extracted_sources(imageid2, results, 'blind')
        associate_extracted_sources(imageid2, deRuiter_r = 3.717)

        query = """\
        SELECT id
          FROM extractedsource
         WHERE image = %s
        ORDER BY id
        """
        self.database.cursor.execute(query, (imageid2,))
        im2 = zip(*self.database.cursor.fetchall())
        self.assertNotEqual(len(im2), 0)
        im2src = im2[0]
        self.assertEqual(len(im2src), len(src))

        query = """\
        SELECT r.id
              ,r.xtrsrc
              ,x.image
              ,r.datapoints
              ,r.wm_ra
              ,r.wm_decl
              ,r.wm_ra_err
              ,r.wm_decl_err
          FROM runningcatalog r
              ,extractedsource x
         WHERE r.xtrsrc = x.id
           AND dataset = %s
        ORDER BY r.id
        """
        self.database.cursor.execute(query, (dataset.id,))
        rc2 = zip(*self.database.cursor.fetchall())
        self.assertNotEqual(len(rc2), 0)
        runcat2 = rc2[0]
        xtrsrc2 = rc2[1]
        image2 = rc2[2]
        self.assertEqual(len(runcat2), len(src))
        self.assertNotEqual(xtrsrc2[0], xtrsrc2[1])
        self.assertEqual(image2[0], image2[1])
        self.assertEqual(image2[0], imageid2)

        query = """\
        SELECT a.runcat
              ,a.xtrsrc
              ,a.type
              ,x.image
          FROM assocxtrsource a
              ,runningcatalog r
              ,extractedsource x
         WHERE a.runcat = r.id
           AND a.xtrsrc = x.id
           AND r.dataset = %s
        ORDER BY a.xtrsrc
                ,a.runcat
        """
        self.database.cursor.execute(query, (dataset.id,))
        assoc2 = zip(*self.database.cursor.fetchall())
        self.assertNotEqual(len(assoc2), 0)
        aruncat2 = assoc2[0]
        axtrsrc2 = assoc2[1]
        atype2 = assoc2[2]
        aimage2 = assoc2[3]
        self.assertEqual(len(aruncat2), 2*len(src))
        self.assertEqual(axtrsrc2[0], im1src1[0])
        self.assertEqual(axtrsrc2[1], im1src1[0])
        self.assertNotEqual(axtrsrc2[2], axtrsrc2[3])
        self.assertEqual(aimage2[2], aimage2[3])
        self.assertEqual(aimage2[2], imageid2)
        self.assertEqual(atype2[0], 6)
        self.assertEqual(atype2[1], 6)
        self.assertEqual(atype2[2], 2)
        self.assertEqual(atype2[3], 2)
        self.assertEqual(aruncat2[0], runcat2[0])
        self.assertEqual(aruncat2[1], runcat2[1])

        query = """\
        SELECT COUNT(*)
          FROM runningcatalog
         WHERE dataset = %s
           AND xtrsrc IN (SELECT id
                            FROM extractedsource
                           WHERE image = %s
                         )
        """
        self.database.cursor.execute(query, (dataset.id, imageid1))
        count = zip(*self.database.cursor.fetchall())
        self.assertEqual(count[0][0], 0)

        #TODO: Add runcat_flux test


class TestMany2One(unittest.TestCase):
    """
    These tests will check the many-to-1 source associations, i.e. one extractedsource
    that has two (or more) counterparts in the runningcatalog.

    """
    @requires_database()
    def setUp(self):
        self.database = tkp.db.Database()

    def tearDown(self):
        """remove all stuff after the test has been run"""
        tkp.db.rollback()

    def test_many2one(self):
        dataset = DataSet(data={'description': 'assoc test set: n-1'})
        n_images = 2
        im_params = db_subs.example_dbimage_datasets(n_images)

        # image 1
        image = tkp.db.Image(dataset=dataset, data=im_params[0])
        imageid1 = image.id
        src = []
        # 2 sources (located close together, so the catching the many-to-1 case in next image
        src.append(db_subs.example_extractedsource_tuple(ra=122.985, dec=10.5,
                                                     ra_fit_err=5./3600, dec_fit_err=6./3600,
                                                     peak = 15e-3, peak_err = 5e-4,
                                                     flux = 15e-3, flux_err = 5e-4,
                                                     sigma = 15,
                                                     beam_maj = 100, beam_min = 100, beam_angle = 45,
                                                     ra_sys_err=20, dec_sys_err=20
                                                        ))
        src.append(db_subs.example_extractedsource_tuple(ra=123.015, dec=10.5,
                                                     ra_fit_err=5./3600, dec_fit_err=6./3600,
                                                     peak = 15e-3, peak_err = 5e-4,
                                                     flux = 15e-3, flux_err = 5e-4,
                                                     sigma = 15,
                                                     beam_maj = 100, beam_min = 100, beam_angle = 45,
                                                     ra_sys_err=20, dec_sys_err=20
                                                        ))
        results = []
        results.append(src[0])
        results.append(src[1])
        dbgen.insert_extracted_sources(imageid1, results, 'blind')
        associate_extracted_sources(imageid1, deRuiter_r = 3.717)

        query = """\
        SELECT id
          FROM extractedsource
         WHERE image = %s
        ORDER BY id
        """
        self.database.cursor.execute(query, (imageid1,))
        im1 = zip(*self.database.cursor.fetchall())
        self.assertNotEqual(len(im1), 0)
        im1src = im1[0]
        self.assertEqual(len(im1src), len(src))

        # image 2
        image = tkp.db.Image(dataset=dataset, data=im_params[1])
        imageid2 = image.id
        src = []
        # 1 source
        src.append(db_subs.example_extractedsource_tuple(ra=123.0, dec=10.5,
                                                     ra_fit_err=5./3600, dec_fit_err=6./3600,
                                                     peak = 15e-3, peak_err = 5e-4,
                                                     flux = 15e-3, flux_err = 5e-4,
                                                     sigma = 15,
                                                     beam_maj = 100, beam_min = 100, beam_angle = 45,
                                                     ra_sys_err=20, dec_sys_err=20
                                                        ))
        results = []
        results.append(src[-1])
        dbgen.insert_extracted_sources(imageid2, results, 'blind')
        associate_extracted_sources(imageid2, deRuiter_r = 3.717)

        query = """\
        SELECT id
          FROM extractedsource
         WHERE image = %s
        """
        self.database.cursor.execute(query, (imageid2,))
        im2 = zip(*self.database.cursor.fetchall())
        self.assertNotEqual(len(im2), 0)
        im2src = im2[0]
        self.assertEqual(len(im2src), 1)

        query = """\
        SELECT id
              ,xtrsrc
              ,datapoints
          FROM runningcatalog
         WHERE dataset = %s
        ORDER BY xtrsrc
        """
        self.database.cursor.execute(query, (dataset.id,))
        rc2 = zip(*self.database.cursor.fetchall())
        self.assertNotEqual(len(rc2), 0)
        runcat2 = rc2[0]
        xtrsrc2 = rc2[1]
        datapoints = rc2[2]
        self.assertEqual(len(runcat2), 2)
        self.assertEqual(xtrsrc2[0], im1src[0])
        self.assertEqual(xtrsrc2[1], im1src[1])
        self.assertEqual(datapoints[0], datapoints[1])
        self.assertEqual(datapoints[0], 2)

        query = """\
        SELECT a.runcat
              ,r.xtrsrc as rxtrsrc
              ,a.xtrsrc as axtrsrc
              ,a.type
              ,x.image
          FROM assocxtrsource a
              ,runningcatalog r
              ,extractedsource x
         WHERE a.runcat = r.id
           AND a.xtrsrc = x.id
           AND r.dataset = %s
        ORDER BY r.xtrsrc
                ,a.xtrsrc
        """
        self.database.cursor.execute(query, (dataset.id,))
        assoc2 = zip(*self.database.cursor.fetchall())
        self.assertNotEqual(len(assoc2), 0)
        aruncat2 = assoc2[0]
        rxtrsrc2 = assoc2[1]
        axtrsrc2 = assoc2[2]
        atype2 = assoc2[3]
        aimage2 = assoc2[4]
        self.assertEqual(len(aruncat2), 4)
        # We can't tell/predict the order of insertion of the runcat entries,
        # but we can for the xtrsrc of the runcat-xtrsrc pair.
        #self.assertEqual(aruncat2[0], aruncat2[2])
        #self.assertEqual(aruncat2[1], aruncat2[3])
        self.assertEqual(rxtrsrc2[0], rxtrsrc2[1])
        self.assertEqual(rxtrsrc2[2], rxtrsrc2[3])
        self.assertEqual(rxtrsrc2[0], axtrsrc2[0])
        self.assertEqual(rxtrsrc2[1], axtrsrc2[1] - 2)
        self.assertEqual(rxtrsrc2[2], axtrsrc2[2])
        self.assertEqual(rxtrsrc2[3], axtrsrc2[3] - 1)
        self.assertEqual(axtrsrc2[0], im1src[0])
        self.assertEqual(axtrsrc2[1], im2src[0])
        self.assertEqual(axtrsrc2[2], im1src[1])
        self.assertEqual(axtrsrc2[3], im2src[0])
        self.assertEqual(atype2[0], 4)
        self.assertEqual(atype2[1], 3)
        self.assertEqual(atype2[2], 4)
        self.assertEqual(atype2[3], 3)
        self.assertEqual(aimage2[0], imageid1)
        self.assertEqual(aimage2[1], imageid2)
        self.assertEqual(aimage2[2], imageid1)
        self.assertEqual(aimage2[3], imageid2)
        #TODO: Add runcat_flux test


class TestMany2Many(unittest.TestCase):
    """
    These tests will check the many-to-many source associations, i.e. many extractedsources
    that has two (or more) counterparts in the runningcatalog.

    """
    @requires_database()
    def setUp(self):
        self.database = tkp.db.Database()

    def tearDown(self):
        """remove all stuff after the test has been run"""
        tkp.db.rollback()

    def test_many2many(self):
        dataset = DataSet(data={'description': 'assoc test set: n-m'})
        n_images = 2
        im_params = db_subs.example_dbimage_datasets(n_images)

        # image 1
        image = tkp.db.Image(dataset=dataset, data=im_params[0])
        imageid1 = image.id
        src1 = []
        # 2 sources (located relatively close together, so the catching the many-to-1 case in next image
        src1.append(db_subs.example_extractedsource_tuple(ra=122.985, dec=10.5,
                                                     ra_fit_err=5./3600, dec_fit_err=6./3600,
                                                     peak = 15e-3, peak_err = 5e-4,
                                                     flux = 15e-3, flux_err = 5e-4,
                                                     sigma = 15,
                                                     beam_maj = 100, beam_min = 100, beam_angle = 45,
                                                     ra_sys_err=20, dec_sys_err=20
                                                        ))
        src1.append(db_subs.example_extractedsource_tuple(ra=123.015, dec=10.5,
                                                     ra_fit_err=5./3600, dec_fit_err=6./3600,
                                                     peak = 15e-3, peak_err = 5e-4,
                                                     flux = 15e-3, flux_err = 5e-4,
                                                     sigma = 15,
                                                     beam_maj = 100, beam_min = 100, beam_angle = 45,
                                                     ra_sys_err=20, dec_sys_err=20
                                                        ))
        results = []
        results.append(src1[0])
        results.append(src1[1])
        dbgen.insert_extracted_sources(imageid1, results, 'blind')
        # We use a default value of 3.717
        associate_extracted_sources(imageid1, deRuiter_r = 3.717)

        query = """\
        SELECT id
          FROM extractedsource
         WHERE image = %s
        ORDER BY id
        """
        self.database.cursor.execute(query, (imageid1,))
        im1 = zip(*self.database.cursor.fetchall())
        self.assertNotEqual(len(im1), 0)
        im1src = im1[0]
        self.assertEqual(len(im1src), len(src1))

        # image 2
        image = tkp.db.Image(dataset=dataset, data=im_params[1])
        imageid2 = image.id
        src2 = []
        # 2 sources, where both can be associated with both from image 1
        src2.append(db_subs.example_extractedsource_tuple(ra=123.0, dec=10.485,
                                                     ra_fit_err=5./3600, dec_fit_err=6./3600,
                                                     peak = 15e-3, peak_err = 5e-4,
                                                     flux = 15e-3, flux_err = 5e-4,
                                                     sigma = 15,
                                                     beam_maj = 100, beam_min = 100, beam_angle = 45,
                                                     ra_sys_err=20, dec_sys_err=20
                                                        ))
        src2.append(db_subs.example_extractedsource_tuple(ra=123.0, dec=10.515,
                                                     ra_fit_err=5./3600, dec_fit_err=6./3600,
                                                     peak = 15e-3, peak_err = 5e-4,
                                                     flux = 15e-3, flux_err = 5e-4,
                                                     sigma = 15,
                                                     beam_maj = 100, beam_min = 100, beam_angle = 45,
                                                     ra_sys_err=20, dec_sys_err=20
                                                        ))
        results = []
        results.append(src2[0])
        results.append(src2[1])
        dbgen.insert_extracted_sources(imageid2, results, 'blind')
        associate_extracted_sources(imageid2, deRuiter_r = 3.717)

        query = """\
        SELECT id
          FROM extractedsource
         WHERE image = %s
        ORDER BY id
        """
        self.database.cursor.execute(query, (imageid2,))
        im2 = zip(*self.database.cursor.fetchall())
        self.assertNotEqual(len(im2), 0)
        im2src = im2[0]
        self.assertEqual(len(im2src), len(src2))

        query = """\
        SELECT id
              ,xtrsrc
              ,datapoints
          FROM runningcatalog
         WHERE dataset = %s
        ORDER BY xtrsrc
        """
        self.database.cursor.execute(query, (dataset.id,))
        rc2 = zip(*self.database.cursor.fetchall())
        self.assertNotEqual(len(rc2), 0)
        runcat2 = rc2[0]
        xtrsrc2 = rc2[1]
        datapoints = rc2[2]
        self.assertEqual(len(runcat2), 2)
        self.assertEqual(xtrsrc2[0], im1src[0])
        self.assertEqual(xtrsrc2[1], im1src[1])
        self.assertEqual(datapoints[0], datapoints[1])
        self.assertEqual(datapoints[0], 2)

        query = """\
        SELECT a.runcat
              ,r.xtrsrc as rxtrsrc
              ,a.xtrsrc as axtrsrc
              ,a.type
              ,x.image
          FROM assocxtrsource a
              ,runningcatalog r
              ,extractedsource x
         WHERE a.runcat = r.id
           AND a.xtrsrc = x.id
           AND r.dataset = %s
        ORDER BY r.xtrsrc
                ,a.xtrsrc
        """
        self.database.cursor.execute(query, (dataset.id,))
        assoc2 = zip(*self.database.cursor.fetchall())
        self.assertNotEqual(len(assoc2), 0)
        aruncat2 = assoc2[0]
        rxtrsrc2 = assoc2[1]
        axtrsrc2 = assoc2[2]
        atype2 = assoc2[3]
        aimage2 = assoc2[4]
        self.assertEqual(len(aruncat2), 4)
        # Idem as many-to-one case
        #self.assertEqual(aruncat2[0], aruncat2[3])
        #self.assertEqual(aruncat2[1], aruncat2[2])
        self.assertEqual(rxtrsrc2[0], rxtrsrc2[1])
        self.assertEqual(rxtrsrc2[2], rxtrsrc2[3])
        self.assertEqual(rxtrsrc2[0], axtrsrc2[0])
        self.assertEqual(rxtrsrc2[1], axtrsrc2[1] - 3)
        self.assertEqual(rxtrsrc2[2], axtrsrc2[2])
        self.assertEqual(rxtrsrc2[3], axtrsrc2[3] - 1)
        self.assertEqual(axtrsrc2[0], im1src[0])
        self.assertEqual(axtrsrc2[1], im2src[1])
        self.assertEqual(axtrsrc2[2], im1src[1])
        self.assertEqual(axtrsrc2[3], im2src[0])
        self.assertEqual(atype2[0], 4)
        self.assertEqual(atype2[1], 3)
        self.assertEqual(atype2[2], 4)
        self.assertEqual(atype2[3], 3)
        self.assertEqual(aimage2[0], imageid1)
        self.assertEqual(aimage2[1], imageid2)
        self.assertEqual(aimage2[2], imageid1)
        self.assertEqual(aimage2[3], imageid2)
        #TODO: Add runcat_flux test

