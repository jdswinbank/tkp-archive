#!/usr/bin/env python

import os
from distutils.core import setup

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)


packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
    trap_dir = 'trap'

for dirpath, dirnames, filenames in os.walk(trap_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

setup(
    name="trap",
    version="0.1-dev",
    packages= packages,
    data_files = data_files,
    description="LOFAR Transients pipeline (TRAP)",
    author="TKP Discovery WG",
    author_email="discovery@transientskp.org",
    url="http://www.transientskp.org/",
    scripts=["trap/bin/trap-manage.py", "trap/bin/trap-local.py", "trap/bin/trap-run.py", "trap/bin/trap-inject.py"]
)
