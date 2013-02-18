Description
===========

The transients pipeline (TraP), or more accurately, the transients detection and classification pipeline, is a software
pipeline that accepts LOFAR imaging data (images, or possibly UV data), tries to find variable or new sources in those
data, and extracts information about those sources in an attempt to classify these sources, all fully automated.

The TraP makes use the Transients Key Project (TKP) library, a Python package which contains the necessary routines for
source finding, source associations, determination of source characteristics and source classification.
The pipeline itself (the framework) is the LOFAR pipeline system.

More info: http://docs.transientskp.org/trap/


Requirements
============

 * TKP http://docs.transientskp.org/tkp/

 * If you want to store the saved images you should install mongo, pymongo and python-gridfs.

   http://www.mongodb.org/

   For Ubuntu:
   $ sudo apt-get install python-pymongo  python-gridfs mongodb-server


Installation
============

 $ python setup.py install

