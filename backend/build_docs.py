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
from bs4 import BeautifulSoup
from huggingface_hub import snapshot_download


load_dotenv()
source_dict: dict[str, str] = {}

# This code must in run in ./backend
cur_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(cur_dir)

# Get commit hashes from env
or_repo_commit = os.getenv('OR_REPO_COMMIT', 'ffc5760f2df639cd184c40ceba253c7e02a006d5')
orfs_repo_commit = os.getenv(
    'ORFS_REPO_COMMIT', 'b94834df01cb58915bc0e8dabf85a314fbd8fb9e'
)
opensta_repo_commit = os.getenv(
    'OPENSTA_REPO_COMMIT', '1c7f022cd0a02ce71d047aa3dbb64e924b6efbd5'
)

or_docs_url = 'https://openroad.readthedocs.io/en/latest'
orfs_docs_url = 'https://openroad-flow-scripts.readthedocs.io/en/latest'
opensta_docs_url = (
    'https://github.com/The-OpenROAD-Project/OpenSTA/raw/'
    f'{opensta_repo_commit}/doc/OpenSTA.pdf'
)
yosys_html_url = 'https://yosyshq.readthedocs.io/projects/yosys/en/latest'
klayout_html_url = 'https://www.klayout.de/doc.html'
or_website_url = 'https://theopenroadproject.org/'
opensta_readme_url = (
    'https://raw.githubusercontent.com/The-OpenROAD-Project/OpenSTA/'
    f'{opensta_repo_commit}/README.md'
)

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').upper())


def update_src(src_path: str, dst_path: str) -> None:
    if 'OR_docs' in dst_path:
        source_dict[dst_path] = (
            f"{or_docs_url}/{src_path.split('_sources/')[-1].replace('.md', '.html')}"
        )
    elif 'ORFS_docs' in dst_path:
        source_dict[dst_path] = (
            f"{orfs_docs_url}/{src_path.split('_sources/')[-1].replace('.md', '.html')}"
        )
    elif 'manpages' in dst_path:
        manpage_path = dst_path.replace('data/markdown/', 'markdown/')
        source_dict[dst_path] = (
            f'https://huggingface.co/datasets/The-OpenROAD-Project/ORAssistant_RAG_Dataset/raw/main/{manpage_path}'
        )
    elif 'yosys' in dst_path:
        source_dict[dst_path] = f"https://{dst_path[len('data/html/yosys_docs') :]}"
    elif 'klayout' in dst_path:
        source_dict[dst_path] = f"https://{dst_path[len('data/html/klayout_docs') :]}"
    elif 'OpenSTA' in dst_path and 'pdf' in dst_path:
        source_dict[dst_path] = opensta_docs_url
    elif 'OpenSTA' in dst_path and 'markdown' in dst_path:
        source_dict[dst_path] = opensta_readme_url
    elif 'theopenroadproject' in dst_path:
        source_dict[dst_path] = (
            f"https://{dst_path.replace('data/html/or_website/', '').replace('/index.html', '')}"
        )
    else:
        source_dict[dst_path] = dst_path


def purge_folders(folder_paths: list[str]) -> None:
    for folder_path in folder_paths:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            logging.debug(f'Purging, Folder {folder_path} deleted.')


def track_src(src: str) -> None:
    logging.debug(f'Updating source dict for {src}...')
    if not os.path.exists(src):
        logging.error(f'File {src} does not exist. Exiting.')
        sys.exit(1)

    for root, _, files in os.walk(src):
        for file in files:
            src = os.path.join(root, file)
            src_path = src.split('backend/')[-1]

            update_src(src_path, src_path)


def copy_file_track_src(src: str, dst: str) -> None:
    if not os.path.exists(src):
        logging.error(f'File {src} does not exist. Exiting.')
        sys.exit(1)

    if os.path.isfile(src):
        if os.path.exists(dst):
            base, ext = os.path.splitext(dst)
            counter = 2
            while os.path.exists(dst):
                new_file_name = f'{base}_{counter}{ext}'
                logging.debug(f'File {dst} already exists. Renaming to {new_file_name}')
                dst = new_file_name
                counter += 1

        shutil.copy2(src, dst)

        dst_path = dst.split('backend/')[-1]

        update_src(src, dst_path)


def copy_tree_track_src(src: str, dst: str) -> None:
    if not os.path.exists(src):
        logging.debug(f'Folder {src} does not exist. Exiting.')
        sys.exit(1)

    for root, _, files in os.walk(src):
        rel_path = os.path.relpath(root, src)
        dst_dir = dst if rel_path == '.' else os.path.join(dst, rel_path)
        os.makedirs(dst_dir, exist_ok=True)

        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dst_dir, file)

            if os.path.exists(dst_file):
                base, ext = os.path.splitext(file)
                counter = 2
                while os.path.exists(dst_file):
                    new_file_name = f'{base}_{counter}{ext}'
                    dst_file = os.path.join(dst_dir, new_file_name)
                    logging.debug(
                        f'File {dst_file} already exists. Renaming to {new_file_name}'
                    )
                    counter += 1

            shutil.copy2(src_file, dst_file)

            dst_path = dst_file.split('backend/')[-1]
            update_src(src_file, dst_path)


def clone_repo(url: str, folder_name: str, commit_hash: Optional[str] = None) -> None:
    target_dir = os.path.join(cur_dir, folder_name)
    logging.debug(f'Cloning repo from {url} to {target_dir}...')
    command = f'git clone {url} {target_dir}'
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

    copy_tree_track_src(
        f'{md_or_docs}/user', f'{cur_dir}/data/markdown/OR_docs/installation'
    )
    copy_tree_track_src(f'{md_or_docs}/main', f'{cur_dir}/data/markdown/OR_docs/tools')
    copy_file_track_src(
        f'{md_or_docs}/main/README.md',
        f'{cur_dir}/data/markdown/OR_docs/general/README.md',
    )
    copy_tree_track_src(
        f'{md_or_docs}/tutorials', f'{cur_dir}/data/markdown/OR_docs/general'
    )
    copy_tree_track_src(
        f'{md_or_docs}/contrib', f'{cur_dir}/data/markdown/OR_docs/general'
    )
    copy_tree_track_src(
        f'{md_or_docs}/src/test', f'{cur_dir}/data/markdown/OR_docs/general'
    )

    for file in os.listdir(f'{md_or_docs}'):
        if file.endswith('.md'):
            copyfile(
                f'{md_or_docs}/{file}',
                f'{cur_dir}/data/markdown/OR_docs/general/{file}',
            )

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

    copy_tree_track_src(
        f'{md_orfs_docs}/tutorials', f'{cur_dir}/data/markdown/ORFS_docs/general'
    )
    copy_tree_track_src(
        f'{md_orfs_docs}/contrib', f'{cur_dir}/data/markdown/ORFS_docs/general'
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
                copy_file_track_src(
                    f'{md_orfs_docs}/user/{file}',
                    f'{cur_dir}/data/markdown/ORFS_docs/installation/{file}',
                )
            else:
                copy_file_track_src(
                    f'{md_orfs_docs}/user/{file}',
                    f'{cur_dir}/data/markdown/ORFS_docs/general/{file}',
                )

    for file in os.listdir(f'{md_orfs_docs}/'):
        if file.endswith('.md'):
            if file in installation_files:
                copy_file_track_src(
                    f'{md_orfs_docs}/{file}',
                    f'{cur_dir}/data/markdown/ORFS_docs/installation/{file}',
                )
            else:
                copy_file_track_src(
                    f'{md_orfs_docs}/{file}',
                    f'{cur_dir}/data/markdown/ORFS_docs/general/{file}',
                )

    logging.debug('Finished building ORFS docs.')

    return


def build_manpages() -> None:
    logging.debug('Starting manpages build...')

    res = subprocess.run('pandoc --version', shell=True, capture_output=True)
    if res.returncode != 0:
        logging.error('Pandoc is not installed. Please install it.')
        sys.exit(1)
    logging.debug('Pandoc is installed.')

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

    src_dir = os.path.join(cur_dir, 'OpenROAD/docs/md')
    dest_dir = os.path.join(cur_dir, 'data/markdown/manpages')

    copy_tree_track_src(src_dir, dest_dir)
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
    else:
        logging.debug('Failed to download file. Status code:', response.status_code)

    response = requests.get(opensta_readme_url)

    save_path = 'data/markdown/OpenSTA_docs/OpenSTA_readme.md'
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    if response.status_code == 200:
        with open(save_path, 'wb+') as file:
            file.write(response.content)
        logging.debug('OpenSTA readme downloaded successfully.')
    else:
        logging.debug('Failed to download file. Status code:', response.status_code)

    track_src(f'{cur_dir}/data/markdown/OpenSTA_docs')
    track_src(f'{cur_dir}/data/pdf/OpenSTA')


def get_or_website_html() -> None:
    logging.debug('Scraping OR website...')
    try:
        subprocess.run(
            f'wget -r -A.html -P data/html/or_website {or_website_url}',
            shell=True,
        )
    except Exception as e:
        logging.debug(f'Error in downloading OR website docs: {e}')
        sys.exit(1)

    logging.debug('OR website docs downloaded successfully.')
    track_src(f'{cur_dir}/data/html/or_website')


def get_or_publications() -> None:
    try:
        html = requests.get('https://theopenroadproject.org/publications/').text
        soup = BeautifulSoup(html, 'lxml')
        links = soup.find_all('a')
        papers = []

        for link in links:
            href = link.get('href')
            if href and '.pdf' in href:
                papers.append(href)

        for paper_link in papers:
            paper_name = paper_link.split('/')[-1]
            logging.debug(f'Downloading {paper_name}. . .')

            counter = 2
            while os.path.exists(f'{cur_dir}/data/pdf/OR_publications/{paper_name}'):
                logging.debug(f'File {paper_name} already exists. Renaming. . .')
                paper_name = f"{paper_name.split('.')[0]}_{counter}.pdf"
                counter += 1

            subprocess.run([
                'wget',
                paper_link,
                '-O',
                f'data/pdf/OR_publications/{paper_name}',
            ])

            source_dict[f'data/pdf/OR_publications/{paper_name}'] = paper_link

    except Exception as e:
        logging.debug(f'Error in downloading OR publications: {e}')
        sys.exit(1)

    logging.debug('OR publications downloaded successfully.')


def get_yosys_docs_html() -> None:
    logging.debug('Scraping Yosys RT docs...')
    try:
        subprocess.run(
            f'wget -r -A.html -P data/html/yosys_docs {yosys_html_url} ',
            shell=True,
        )
    except Exception as e:
        logging.debug(f'Error in downloading Yosys docs: {e}')
        sys.exit(1)

    logging.debug('Yosys docs downloaded successfully.')
    track_src(f'{cur_dir}/data/html/yosys_docs')


def get_klayout_docs_html() -> None:
    logging.debug('Scraping KLayout docs...')
    try:
        subprocess.run(
            f'wget -r -A.html -l 3 -P data/html/klayout_docs {klayout_html_url} ',
            shell=True,
        )
    except Exception as e:
        logging.debug(f'Error in downloading KLayout docs: {e}')
        sys.exit(1)

    logging.debug('KLayout docs downloaded successfully.')
    track_src(f'{cur_dir}/data/html/klayout_docs')


if __name__ == '__main__':
    logging.info('Building knowledge base...')
    docs_paths = [
        'data/markdown/manpages',
        'data/markdown/OR_docs',
        'data/markdown/ORFS_docs',
        'data/markdown/OpenSTA_docs',
        'data/pdf',
        'data/html',
    ]
    purge_folders(folder_paths=docs_paths)

    os.makedirs('data/markdown/manpages', exist_ok=True)
    os.makedirs('data/markdown/OR_docs', exist_ok=True)
    os.makedirs('data/markdown/OR_docs/installation', exist_ok=True)
    os.makedirs('data/markdown/OR_docs/tools', exist_ok=True)
    os.makedirs('data/markdown/OR_docs/general', exist_ok=True)
    os.makedirs('data/markdown/ORFS_docs', exist_ok=True)
    os.makedirs('data/markdown/ORFS_docs/installation', exist_ok=True)
    os.makedirs('data/markdown/ORFS_docs/general', exist_ok=True)
    os.makedirs('data/markdown/OpenSTA_docs', exist_ok=True)
    os.makedirs('data/pdf/OpenSTA', exist_ok=True)
    os.makedirs('data/pdf/OR_publications', exist_ok=True)
    os.makedirs('data/html', exist_ok=True)

    get_klayout_docs_html()
    get_yosys_docs_html()

    get_or_publications()
    get_or_website_html()
    get_opensta_docs()

    clone_repo(
        url='https://github.com/The-OpenROAD-Project/OpenROAD.git',
        commit_hash=or_repo_commit,
        folder_name='OpenROAD',
    )
    clone_repo(
        url='https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git',
        commit_hash=orfs_repo_commit,
        folder_name='OpenROAD-flow-scripts',
    )

    build_or_docs()
    build_orfs_docs()
    build_manpages()

    os.chdir(cur_dir)
    copy_file_track_src(
        f'{cur_dir}/data/markdown/OR_docs/installation/MessagesFinal.md',
        f'{cur_dir}/data/markdown/manpages/man3/ErrorMessages.md',
    )

    os.remove(f'{cur_dir}/data/markdown/OR_docs/installation/MessagesFinal.md')

    snapshot_download(
        repo_id='The-OpenROAD-Project/ORAssistant_RAG_Dataset',
        repo_type='dataset',
        revision='main',
        allow_patterns=[
            'markdown/gh_discussions/**/*',
            'markdown/gh_discussions/*',
        ],
        local_dir='data',
    )

    with open(f'{cur_dir}/data/markdown/gh_discussions/mapping.json') as gh_disc:
        gh_disc_src = json.load(gh_disc)
    # gh_disc_src_json = open(f'{cur_dir}/data/markdown/gh_discussions/mapping.json', 'r')
    # gh_disc_src = json.load(gh_disc_src_json)
    gh_disc_path = 'data/markdown/gh_discussions'
    source_dict = {}
    for file in gh_disc_src.keys():
        full_path = os.path.join(gh_disc_path, file)
        source_dict[full_path] = gh_disc_src[file]['url']

    with open('data/source_list.json', 'w+') as src:
        src.write(json.dumps(source_dict))

    repo_paths = ['OpenROAD', 'OpenROAD-flow-scripts']
    purge_folders(folder_paths=repo_paths)
