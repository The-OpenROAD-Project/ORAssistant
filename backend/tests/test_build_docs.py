import os
import sys
import logging
from dotenv import load_dotenv

backend_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv()

from build_docs import (
    purge_folders,
    get_yosys_docs_html,
    get_opensta_docs,
    clone_repo,
    build_or_docs,
    build_orfs_docs,
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
    os.chdir(backend_dir)
    lst = ['test1', 'test2']
    purge_folders(lst)

    # Check if the folders are deleted
    for folder in lst:
        assert not os.path.exists(folder)


def test_get_yosys_rtdocs():
    os.chdir(backend_dir)
    yosys_version='0.36'
    yosys_docs_count=283
    get_yosys_docs_html()
    assert os.path.exists('data/html')

    count = sum(len(files) for _, _, files in os.walk(f"data/html/yosys_docs/yosyshq.readthedocs.io/projects/yosys/en/{yosys_version}"))
    assert count == yosys_docs_count, f"Expected {yosys_docs_count} files, got {count}"    


# def test_get_opensta_docs():
#     os.chdir(backend_dir)
#     get_opensta_docs()
#     assert os.path.exists('data/pdf/OpenSTA/OpenSTA_docs.pdf')


# def test_clone_repo():
#     os.chdir(backend_dir)
#     clone_repo(
#         url = 'https://github.com/octocat/Hello-World.git',
#         commit_hash='7fd1a60b01f91b314f59955a4e4d4e80d8edf11d',
#         folder_name = 'Hello-World',
#     )
#     assert os.path.exists('README')


# def test_build_or_docs():
#     os.chdir(backend_dir)
#     or_docs_count = 55

#     clone_repo(
#         url='https://github.com/The-OpenROAD-Project/OpenROAD.git',
#         commit_hash=os.getenv('OR_REPO_COMMIT', 'ffc5760f2df639cd184c40ceba253c7e02a006d5'),
#         folder_name='OpenROAD',
#     )
#     build_or_docs()
#     count = sum(len(files) for _, _, files in os.walk('data/markdown/OR_docs'))
#     assert count == or_docs_count, f"Expected {or_docs_count} files, got {count}"


# def test_build_orfs_docs():
#     os.chdir(backend_dir)
#     orfs_docs_count = 27

#     clone_repo(
#         url='https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git',
#         commit_hash=os.getenv('ORFS_REPO_COMMIT', 'b94834df01cb58915bc0e8dabf85a314fbd8fb9e'),
#         folder_name='OpenROAD-flow-scripts',
#     )
#     build_orfs_docs()
#     count = sum(len(files) for _, _, files in os.walk('data/markdown/ORFS_docs'))
#     logging.info(count)
#     assert count == orfs_docs_count, f"Expected {orfs_docs_count} files, got {count}"


def test_teardown():
    os.chdir(backend_dir)
    logger.info('Cleaning up...')
    purge_folders(docs_paths)
    purge_folders(['Hello-World'])
    purge_folders(['OpenROAD'])
    purge_folders(['OpenROAD-flow-scripts'])