import os
import subprocess
import requests
import sys
import shutil
import json
import logging
from shutil import copyfile
from dotenv import load_dotenv
from typing import Optional

load_dotenv()
source_dict: dict[str, str] = {}
cur_dir: str = os.getcwd()

or_docs_url = 'https://openroad.readthedocs.io/en/latest'
orfs_docs_url = 'https://openroad-flow-scripts.readthedocs.io/en/latest'
opensta_docs_url = 'https://github.com/The-OpenROAD-Project/OpenSTA/raw/1c7f022cd0a02ce71d047aa3dbb64e924b6efbd5/doc/OpenSTA.pdf'
yosys_rtdocs_url = 'https://yosyshq.readthedocs.io/projects/yosys/en/latest'

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').upper())


def purge_folders(folder_paths: list[str]) -> None:
    for folder_path in folder_paths:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            logging.debug(f'Purging, Folder {folder_path} deleted.')


def track_src(src: str) -> dict[str, str]:
    copied_files = {}

    if not os.path.exists(src):
        logging.debug(f'File {src} does not exist. Exiting.')
        sys.exit(1)

    for root, _, files in os.walk(src):
        for file in files:
            src = os.path.join(root, file)
            src_path = src.split('backend/')[-1]

            if 'OR_docs' in src:
                copied_files[src_path] = (
                    f"{or_docs_url}/{src.split('_sources/')[-1].replace('.md', '.html')}"
                )
            elif 'ORFS_docs' in src:
                copied_files[src_path] = (
                    f"{orfs_docs_url}/{src.split('_sources/')[-1].replace('.md', '.html')}"
                )
            elif 'manpages' in src:
                copied_files[src_path] = (
                    f"OpenROAD Manpages - {src_path.split('/')[-1]}"
                )
            elif 'yosys' in src:
                copied_files[src_path] = src_path.split('/data/rtdocs/')[-1]
            elif 'OpenSTA' in src:
                copied_files[src_path] = opensta_docs_url
            else:
                copied_files[src_path] = src_path

    return copied_files


def copy_file_track_src(src: str, dst: str) -> dict[str, str]:
    copied_files = {}

    if not os.path.exists(src):
        logging.debug(f'File {src} does not exist. Exiting.')
        sys.exit(1)

    if os.path.isfile(src):
        shutil.copy2(src, dst)

        dst_path = dst.split('backend/')[-1]

        if 'OR_docs' in dst:
            copied_files[dst_path] = (
                f"{or_docs_url}/{src.split('_sources/')[-1].replace('.md', '.html')}"
            )
        elif 'ORFS_docs' in dst:
            copied_files[dst_path] = (
                f"{orfs_docs_url}/{src.split('_sources/')[-1].replace('.md', '.html')}"
            )
        elif 'manpages' in dst:
            copied_files[dst_path] = (
                f"OpenROAD Manpages - {src.split('data/markdown/')[-1]}"
            )
        elif 'yosys' in dst:
            copied_files[dst_path] = src.split('/data/rtdocs/')[-1]
        elif 'OpenSTA' in dst:
            copied_files[dst_path] = opensta_docs_url
        else:
            copied_files[dst_path] = dst_path

    return copied_files


def copy_tree_track_src(src: str, dst: str) -> dict[str, str]:
    copied_files = {}

    if not os.path.exists(src):
        logging.debug(f'Folder {src} does not exist. Exiting.')
        sys.exit(1)

    for root, _, files in os.walk(src):
        rel_path = os.path.relpath(root, src)
        if rel_path == '.':
            dst_dir = dst
        else:
            dst_dir = os.path.join(dst, rel_path)
        os.makedirs(dst_dir, exist_ok=True)

        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dst_dir, file)
            shutil.copy2(src_file, dst_file)

            dst_path = dst_file.split('backend/')[-1]

            if 'OR_docs' in dst_file:
                copied_files[dst_path] = (
                    f"{or_docs_url}/{src_file.split('_sources/')[-1].replace('.md', '.html')}"
                )
            elif 'ORFS_docs' in dst_file:
                copied_files[dst_path] = (
                    f"{orfs_docs_url}/{src_file.split('_sources/')[-1].replace('.md', '.html')}"
                )
            elif 'manpages' in dst_file:
                copied_files[dst_path] = (
                    f"OpenROAD Manpages - {src.split('data/markdown/')[-1]}"
                )
            elif 'yosys' in dst_file:
                copied_files[dst_path] = src.split('/data/rtdocs/')[-1]
            elif 'OpenSTA' in dst_file:
                copied_files[dst_path] = opensta_docs_url
            else:
                copied_files[dst_path] = dst_path

    return copied_files


def clone_repo(url: str, folder_name: str, commit_hash: Optional[str] = None) -> None:
    target_dir = os.path.join(cur_dir, folder_name)
    logging.debug(f'Cloning repo from {url} to {target_dir}...')
    command = f'git clone {url} --depth 1 {target_dir}'
    res = subprocess.run(command, shell=True, capture_output=True)
    if res.returncode != 0:
        logging.debug(f"Error in cloning repo: {res.stderr.decode('utf-8')}")
        sys.exit(1)
    if commit_hash:
        os.chdir(target_dir)
        command = f'git fetch origin {commit_hash} && git checkout {commit_hash}'
        res = subprocess.run(command, shell=True, capture_output=True)
        if res.returncode != 0:
            logging.debug(
                f"Error in checking out commit hash: {res.stderr.decode('utf-8')}"
            )
            sys.exit(1)
    logging.debug('Cloned repo successfully.')


def build_or_docs() -> None:
    logging.debug('Starting OR docs build...')

    os.chdir(os.path.join(cur_dir, 'OpenROAD/docs'))
    subprocess.run('make html', shell=True, capture_output=True)

    logging.debug('Copying OR docs...')
    os.chdir(cur_dir)
    md_or_docs = os.path.join(cur_dir, 'OpenROAD/docs/build/html/_sources')

    if not os.path.isdir(md_or_docs):
        logging.debug(f'Directory {md_or_docs} does not exist. Exiting.')
        sys.exit(1)

    source_dict.update(
        copy_tree_track_src(
            f'{md_or_docs}/user', f'{cur_dir}/data/markdown/OR_docs/installation'
        )
    )
    source_dict.update(
        copy_tree_track_src(
            f'{md_or_docs}/main/src', f'{cur_dir}/data/markdown/OR_docs/tools'
        )
    )
    source_dict.update(
        copy_tree_track_src(
            f'{md_or_docs}/tutorials', f'{cur_dir}/data/markdown/OR_docs'
        )
    )
    source_dict.update(
        copy_tree_track_src(f'{md_or_docs}/contrib', f'{cur_dir}/data/markdown/OR_docs')
    )
    source_dict.update(
        copy_tree_track_src(
            f'{md_or_docs}/src/test', f'{cur_dir}/data/markdown/OR_docs'
        )
    )

    for file in os.listdir(f'{md_or_docs}'):
        if file.endswith('.md'):
            copyfile(f'{md_or_docs}/{file}', f'{cur_dir}/data/markdown/OR_docs/{file}')

    logging.debug('Finished building OR docs.')

    return


def build_orfs_docs() -> None:
    logging.debug('Starting ORFS docs build...')
    os.chdir(os.path.join(cur_dir, 'OpenROAD-flow-scripts/docs'))

    subprocess.run('make html', shell=True, capture_output=True)

    logging.debug('Copying ORFS docs...')
    os.chdir(cur_dir)
    md_orfs_docs = os.path.join(
        cur_dir, 'OpenROAD-flow-scripts/docs/build/html/_sources'
    )

    if not os.path.isdir(md_orfs_docs):
        logging.debug(f'Directory {md_orfs_docs} does not exist. Exiting.')
        sys.exit(1)

    source_dict.update(
        copy_tree_track_src(
            f'{md_orfs_docs}/tutorials', f'{cur_dir}/data/markdown/ORFS_docs'
        )
    )
    source_dict.update(
        copy_tree_track_src(
            f'{md_orfs_docs}/contrib', f'{cur_dir}/data/markdown/ORFS_docs'
        )
    )

    installation_files = [
        'FAQS.md',
        'BuildLocally.md',
        'BuildWithDocker.md',
        'BuildWithPrebuilt.md',
        'BuildWithWSL.md',
        'SupportedOS.md',
        'index2.md',
    ]

    for file in os.listdir(f'{md_orfs_docs}/user'):
        if file.endswith('.md'):
            if file in installation_files:
                source_dict.update(
                    copy_file_track_src(
                        f'{md_orfs_docs}/user/{file}',
                        f'{cur_dir}/data/markdown/ORFS_docs/installation/{file}',
                    )
                )
            else:
                source_dict.update(
                    copy_file_track_src(
                        f'{md_orfs_docs}/user/{file}',
                        f'{cur_dir}/data/markdown/ORFS_docs/{file}',
                    )
                )

    for file in os.listdir(f'{md_orfs_docs}/'):
        if file.endswith('.md'):
            if file in installation_files:
                source_dict.update(
                    copy_file_track_src(
                        f'{md_orfs_docs}/{file}',
                        f'{cur_dir}/data/markdown/ORFS_docs/installation/{file}',
                    )
                )
            else:
                source_dict.update(
                    copy_file_track_src(
                        f'{md_orfs_docs}/{file}',
                        f'{cur_dir}/data/markdown/ORFS_docs/{file}',
                    )
                )
    logging.debug('Finished building ORFS docs.')

    return


def build_manpages() -> None:
    logging.debug('Starting manpages build...')

    # check if pandoc is installed, if not error out.
    res = subprocess.run('pandoc --version', shell=True, capture_output=True)
    if res.returncode != 0:
        logging.debug('Pandoc is not installed. Please install it.')
        sys.exit(1)
    logging.debug('Pandoc is installed.')

    # generate manpages
    command = '../../etc/find_messages.py > messages.txt'
    for module in os.listdir(os.path.join(cur_dir, 'OpenROAD/src')):
        path = os.path.join(cur_dir, 'OpenROAD/src', module)
        if not os.path.isdir(path):
            continue
        os.chdir(path)
        res = subprocess.run(command, shell=True, capture_output=True)
        if res.returncode != 0:
            logging.error(
                f"Error in finding messages for {module}: {res.stderr.decode('utf-8')}"
            )
            continue
    os.chdir(os.path.join(cur_dir, 'OpenROAD/docs'))
    num_cores = os.cpu_count()
    command = f'make clean && make preprocess && make -j{num_cores}'
    res = subprocess.run(command, shell=True, capture_output=True)
    logging.debug('Finished building manpages.')

    # copy folder contents to data/markdown/manpages
    src_dir = os.path.join(cur_dir, 'OpenROAD/docs/md')
    dest_dir = os.path.join(cur_dir, 'data/markdown/manpages')

    source_dict.update(copy_tree_track_src(src_dir, dest_dir))
    logging.debug('Copied manpages to data/markdown/manpages.')

    logging.debug('Finished building manpages.')

    return


def get_opensta_docs() -> None:
    os.chdir(cur_dir)
    response = requests.get(opensta_docs_url)

    save_path = 'data/pdf/OpenSTA/OpenSTA_docs.pdf'
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    if response.status_code == 200:
        with open(save_path, 'wb+') as file:
            file.write(response.content)
        logging.debug('OpenSTA docs downloaded successfully.')
        source_dict.update(track_src(f'{cur_dir}/data/pdf/OpenSTA'))
    else:
        logging.debug('Failed to download file. Status code:', response.status_code)


def get_yosys_rtdocs() -> None:
    logging.debug('Downloading Yosys RT docs...')
    try:
        subprocess.run(
            f'wget -r -A.html -P data/rtdocs {yosys_rtdocs_url} ',
            shell=True,
        )
    except Exception as e:
        logging.debug(f'Error in downloading Yosys RT docs: {e}')
        sys.exit(1)

    logging.debug('Yosys RT docs downloaded successfully.')
    source_dict.update(track_src(f'{cur_dir}/data/rtdocs'))


if __name__ == '__main__':
    logging.info('Building knowledge base...')
    docs_paths = [
        'data/markdown/manpages',
        'data/markdown/OR_docs',
        'data/markdown/ORFS_docs',
        'data/pdf',
        'data/rtdocs',
    ]
    purge_folders(folder_paths=docs_paths)

    os.makedirs('data/markdown/manpages', exist_ok=True)
    os.makedirs('data/markdown/OR_docs', exist_ok=True)
    os.makedirs('data/markdown/OR_docs/installation', exist_ok=True)
    os.makedirs('data/markdown/OR_docs/tools', exist_ok=True)
    os.makedirs('data/markdown/ORFS_docs', exist_ok=True)
    os.makedirs('data/markdown/ORFS_docs/installation', exist_ok=True)
    os.makedirs('data/pdf/OpenSTA', exist_ok=True)
    os.makedirs('data/rtdocs', exist_ok=True)

    get_yosys_rtdocs()
    get_opensta_docs()

    clone_repo(
        url='https://github.com/The-OpenROAD-Project/OpenROAD.git',
        commit_hash=os.getenv(
            'OR_REPO_COMMIT', 'ffc5760f2df639cd184c40ceba253c7e02a006d5'
        ),
        folder_name='OpenROAD',
    )
    clone_repo(
        url='https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git',
        commit_hash=os.getenv(
            'ORFS_REPO_COMMIT', 'b94834df01cb58915bc0e8dabf85a314fbd8fb9e'
        ),
        folder_name='OpenROAD-flow-scripts',
    )

    build_or_docs()
    build_orfs_docs()
    build_manpages()

    os.chdir(cur_dir)
    source_dict.update(
        copy_file_track_src(
            f'{cur_dir}/data/markdown/OR_docs/installation/MessagesFinal.md',
            f'{cur_dir}/data/markdown/manpages/man3/ErrorMessages.md',
        )
    )
    os.remove(f'{cur_dir}/data/markdown/OR_docs/installation/MessagesFinal.md')

    gh_disc_src_json = open(f'{cur_dir}/data/markdown/gh_discussions/mapping.json', 'r')
    gh_disc_src = json.load(gh_disc_src_json)
    gh_disc_path = 'data/markdown/gh_discussions'
    for file in gh_disc_src.keys():
        full_path = os.path.join(gh_disc_path, file)
        source_dict[full_path] = gh_disc_src[file]['url']

    with open('src/source_list.json', 'w+') as src:
        src.write(json.dumps(source_dict))

    repo_paths = ['OpenROAD', 'OpenROAD-flow-scripts']
    purge_folders(folder_paths=repo_paths)
