import os
import sys
import logging

# TODO: Fix this using pip install -e .
os.chdir(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from build_docs import (
    purge_folders,
    get_yosys_rtdocs,
    get_opensta_docs
)


docs_paths = [
    'data/markdown/manpages',
    'data/markdown/OR_docs',
    'data/markdown/OR_docs/installation',
    'data/markdown/OR_docs/tools',
    'data/markdown/ORFS_docs',
    'data/markdown/ORFS_docs/installation',
    'data/pdf/OpenSTA',
    'data/rtdocs',
]


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def test_setup():
    logger.info('Setting up...')
    for path in docs_paths:
        os.makedirs(path, exist_ok=True)


def test_purge_folders():
    lst = ['test1', 'test2']
    purge_folders(lst)

    # Check if the folders are deleted
    for folder in lst:
        assert not os.path.exists(folder)


def test_get_yosys_rtdocs():
    yosys_version='0.36'
    yosys_docs_count=283
    get_yosys_rtdocs()
    assert os.path.exists('data/rtdocs')

    count = sum(len(files) for _, _, files in os.walk(f"data/rtdocs/yosyshq.readthedocs.io/projects/yosys/en/{yosys_version}"))
    assert count == yosys_docs_count, f"Expected {yosys_docs_count} files, got {count}"    


def test_get_opensta_docs():
    get_opensta_docs()
    assert os.path.exists('data/pdf/OpenSTA/OpenSTA_docs.pdf')


def test_teardown():
    logger.info('Cleaning up...')
    purge_folders(docs_paths)