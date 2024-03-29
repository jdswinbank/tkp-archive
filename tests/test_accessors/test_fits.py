"""
Tests for simulated LOFAR datasets.
"""

import os

import unittest2 as unittest

from tkp.testutil.data import DATAPATH
from tkp import accessors
from tkp.accessors.fitsimage import FitsImage
from tkp.db.orm import DataSet
from tkp.db.database import Database
import tkp.db
from tkp.testutil.decorators import requires_data
from tkp.testutil.decorators import requires_database



class PyfitsFitsImage(unittest.TestCase):

    def tearDown(self):
        tkp.db.rollback()

    @requires_data(os.path.join(DATAPATH, 'L15_12h_const/observed-all.fits'))
    @requires_data(os.path.join(DATAPATH, 'CORRELATED_NOISE.FITS'))
    def testOpen(self):
        fits_file = os.path.join(DATAPATH, 'L15_12h_const/observed-all.fits')
        image = FitsImage(fits_file, beam=(54./3600, 54./3600, 0.))
        self.assertAlmostEqual(image.beam[0], 0.225)
        self.assertAlmostEqual(image.beam[1], 0.225)
        self.assertAlmostEqual(image.beam[2], 0.)
        self.assertAlmostEqual(image.wcs.crval[0], 350.85)
        self.assertAlmostEqual(image.wcs.crval[1], 58.815)
        self.assertAlmostEqual(image.wcs.crpix[0], 1441.)
        self.assertAlmostEqual(image.wcs.crpix[1], 1441.)
        self.assertAlmostEqual(image.wcs.cdelt[0], -0.03333333)
        self.assertAlmostEqual(image.wcs.cdelt[1], 0.03333333)
        self.assertTupleEqual(image.wcs.ctype, ('RA---SIN', 'DEC--SIN'))
        # Beam included in image
        fits_file = os.path.join(DATAPATH, 'CORRELATED_NOISE.FITS')
        image = FitsImage(fits_file)
        self.assertAlmostEqual(image.beam[0], 2.7977999)
        self.assertAlmostEqual(image.beam[1], 2.3396999)
        self.assertAlmostEqual(image.beam[2], -0.869173967)
        self.assertAlmostEqual(image.wcs.crval[0], 266.363244382)
        self.assertAlmostEqual(image.wcs.crval[1], -29.9529359725)
        self.assertAlmostEqual(image.wcs.crpix[0], 128.)
        self.assertAlmostEqual(image.wcs.crpix[1], 129.)
        self.assertAlmostEqual(image.wcs.cdelt[0], -0.003333333414)
        self.assertAlmostEqual(image.wcs.cdelt[1], 0.003333333414)
        self.assertTupleEqual(image.wcs.ctype, ('RA---SIN', 'DEC--SIN'))

    @requires_data(os.path.join(DATAPATH, 'L15_12h_const/observed-all.fits'))
    def testSFImageFromFITS(self):
        fits_file = os.path.join(DATAPATH, 'L15_12h_const/observed-all.fits')
        image = FitsImage(fits_file, beam=(54./3600, 54./3600, 0.))
        sfimage = accessors.sourcefinder_image_from_accessor(image)



class TestFitsImage(unittest.TestCase):

    def tearDown(self):
        tkp.db.rollback()

    @requires_data(os.path.join(DATAPATH, 'L15_12h_const/observed-all.fits'))
    @requires_data(os.path.join(DATAPATH, 'CORRELATED_NOISE.FITS'))
    def testOpen(self):
        # Beam specified by user
        fits_file = os.path.join(DATAPATH, 'L15_12h_const/observed-all.fits')
        image = FitsImage(fits_file, beam=(54./3600, 54./3600, 0.))
        self.assertEqual(image.telescope, 'LOFAR20') #God knows why it's 'LOFAR20'
        self.assertAlmostEqual(image.beam[0], 0.225)
        self.assertAlmostEqual(image.beam[1], 0.225)
        self.assertAlmostEqual(image.beam[2], 0.)
        self.assertAlmostEqual(image.wcs.crval[0], 350.85)
        self.assertAlmostEqual(image.wcs.crval[1], 58.815)
        self.assertAlmostEqual(image.wcs.crpix[0], 1441.)
        self.assertAlmostEqual(image.wcs.crpix[1], 1441.)
        self.assertAlmostEqual(image.wcs.cdelt[0], -0.03333333)
        self.assertAlmostEqual(image.wcs.cdelt[1], 0.03333333)
        self.assertTupleEqual(image.wcs.ctype, ('RA---SIN', 'DEC--SIN'))
        # Beam included in image
        image = FitsImage(os.path.join(DATAPATH, 'CORRELATED_NOISE.FITS'))
        self.assertAlmostEqual(image.beam[0], 2.7977999)
        self.assertAlmostEqual(image.beam[1], 2.3396999)
        self.assertAlmostEqual(image.beam[2], -0.869173967)
        self.assertAlmostEqual(image.wcs.crval[0], 266.363244382)
        self.assertAlmostEqual(image.wcs.crval[1], -29.9529359725)
        self.assertAlmostEqual(image.wcs.crpix[0], 128.)
        self.assertAlmostEqual(image.wcs.crpix[1], 129.)
        self.assertAlmostEqual(image.wcs.cdelt[0], -0.003333333414)
        self.assertAlmostEqual(image.wcs.cdelt[1], 0.003333333414)
        self.assertTupleEqual(image.wcs.ctype, ('RA---SIN', 'DEC--SIN'))

    @requires_data(os.path.join(DATAPATH, 'L15_12h_const/observed-all.fits'))
    def testSFImageFromFITS(self):
        image = FitsImage(os.path.join(DATAPATH, 'L15_12h_const/observed-all.fits'),
                                   beam=(54./3600, 54./3600, 0.))
        sfimage = accessors.sourcefinder_image_from_accessor(image)


class DataBaseImage(unittest.TestCase):
    """TO DO: split this into an accessor test and a database test.
                Move the database part to the database unit-tests"""

    def tearDown(self):
        tkp.db.rollback()

    @requires_database()
    @requires_data(os.path.join(DATAPATH, 'L15_12h_const/observed-all.fits'))
    def testDBImageFromAccessor(self):
        import tkp.db.database

        image = FitsImage(os.path.join(DATAPATH, 'L15_12h_const/observed-all.fits'),
                                      beam=(54./3600, 54./3600, 0.))

        database = tkp.db.database.Database()
        dataset = DataSet(data={'description': 'Accessor test'}, database=database)
        dbimage = accessors.dbimage_from_accessor(dataset, image,
                                                  extraction_radius=3)


class FrequencyInformation(unittest.TestCase):
    """TO DO: split this into an accessor test and a database test.
                Move the database part to the database unit-tests"""

    def tearDown(self):
        tkp.db.rollback()

    @requires_database()
    @requires_data(os.path.join(DATAPATH, 'VLSS.fits'))
    def testFreqinfo(self):
        database = Database()
        dataset = DataSet(data={'description': 'dataset'}, database=database)

        # image without frequency information
        image = FitsImage(os.path.join(DATAPATH, 'VLSS.fits'))
        # The database requires frequency information
        #self.assertRaises(ValueError, accessors.dbimage_from_accessor, dataset, image)
        # But the sourcefinder does not need frequency information
        self.assertListEqual(
            list(accessors.sourcefinder_image_from_accessor(image).data.shape),
            [2048, 2048])
        tkp.db.rollback()

if __name__ == '__main__':
    unittest.main()
