import os
import subprocess
import requests
import sys
import shutil
import json
from distutils.dir_util import copy_tree
from shutil import copyfile

from typing import Optional

source_dict: dict[str,str] = {}
cur_dir: str = os.getcwd()


def purge_folders(folder_paths: list[str]) -> None:
    for folder_path in folder_paths:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            print(f'Purging, Folder {folder_path} deleted.')


def update_source_dict(dir_path: str) -> None:
    print(f'Updating source_dict for {dir_path}...')
    for root, _, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_name = os.path.basename(file_path)
            source_dict[file_path] = file_name


def clone_repo(url: str, folder_name: str, commit_hash:Optional[str] = None) -> None:
    target_dir = os.path.join(cur_dir, folder_name)
    print(f'Cloning repo from {url} to {target_dir}...')
    command = f'git clone {url} --depth 1 {target_dir}'
    res = subprocess.run(command, shell=True, capture_output=True)
    if res.returncode != 0:
        print(f"Error in cloning repo: {res.stderr.decode('utf-8')}")
        sys.exit(1)
    if commit_hash:
        os.chdir(target_dir)
        command = f'git checkout {commit_hash}'
        res = subprocess.run(command, shell=True, capture_output=True)
        if res.returncode != 0:
            print(f"Error in checking out commit hash: {res.stderr.decode('utf-8')}")
            sys.exit(1)
    print('Cloned repo successfully.')


def build_or_docs() -> None:
    print('Starting OR docs build...')

    os.chdir(os.path.join(cur_dir, 'OpenROAD/docs'))
    subprocess.run('make html', shell=True, capture_output=True)

    print('Copying OR docs...')
    os.chdir(cur_dir)
    md_or_docs = os.path.join(cur_dir, 'OpenROAD/docs/build/html/_sources')

    if not os.path.isdir(md_or_docs):
        print(f'Directory {md_or_docs} does not exist. Exiting.')
        sys.exit(1)

    copy_tree(f'{md_or_docs}/user', f'{cur_dir}/data/markdown/OR_docs/installation')
    copy_tree(f'{md_or_docs}/main/src', f'{cur_dir}/data/markdown/OR_docs/tools')
    copy_tree(f'{md_or_docs}/tutorials', f'{cur_dir}/data/markdown/OR_docs')
    copy_tree(f'{md_or_docs}/contrib', f'{cur_dir}/data/markdown/OR_docs')
    copy_tree(f'{md_or_docs}/src/test', f'{cur_dir}/data/markdown/OR_docs')

    for file in os.listdir(f'{md_or_docs}'):
        if file.endswith('.md'):
            copyfile(f'{md_or_docs}/{file}', f'{cur_dir}/data/markdown/OR_docs/{file}')

    print('Finished building OR docs.')

    return


def build_orfs_docs() -> None:
    print('Starting ORFS docs build...')
    os.chdir(os.path.join(cur_dir, 'OpenROAD-flow-scripts/docs'))

    subprocess.run('make html', shell=True, capture_output=True)

    print('Copying ORFS docs...')
    os.chdir(cur_dir)
    md_orfs_docs = os.path.join(
        cur_dir, 'OpenROAD-flow-scripts/docs/build/html/_sources'
    )

    if not os.path.isdir(md_orfs_docs):
        print(f'Directory {md_orfs_docs} does not exist. Exiting.')
        sys.exit(1)

    copy_tree(f'{md_orfs_docs}/tutorials', f'{cur_dir}/data/markdown/ORFS_docs')
    copy_tree(f'{md_orfs_docs}/contrib', f'{cur_dir}/data/markdown/ORFS_docs')

    os.makedirs(f'{cur_dir}/data/markdown/ORFS_docs/installation', exist_ok=True)

    for file in os.listdir(f'{md_orfs_docs}/user'):
        if file.endswith('.md'):
            if 'build' in file.lower():
                copyfile(
                    f'{md_orfs_docs}/user/{file}',
                    f'{cur_dir}/data/markdown/ORFS_docs/installation/{file}',
                )
            else:
                copyfile(
                    f'{md_orfs_docs}/user/{file}',
                    f'{cur_dir}/data/markdown/ORFS_docs/{file}',
                )

    for file in os.listdir(f'{md_orfs_docs}'):
        if file.endswith('.md'):
            copyfile(
                f'{md_orfs_docs}/{file}', f'{cur_dir}/data/markdown/ORFS_docs/{file}'
            )
    print('Finished building ORFS docs.')

    return


def build_manpages() -> None:
    print('Starting manpages build...')

    # check if pandoc is installed, if not error out.
    res = subprocess.run('pandoc --version', shell=True, capture_output=True)
    if res.returncode != 0:
        print('Pandoc is not installed. Please install it.')
        sys.exit(1)
    print('Pandoc is installed.')

    # generate manpages
    command = '../../etc/find_messages.py > messages.txt'
    for module in os.listdir(os.path.join(cur_dir, 'OpenROAD/src')):
        path = os.path.join(cur_dir, 'OpenROAD/src', module)
        if not os.path.isdir(path):
            continue
        print('Processing module:', module)
        os.chdir(path)
        res = subprocess.run(command, shell=True, capture_output=True)
        if res.returncode != 0:
            print(
                f"Error in finding messages for {module}: {res.stderr.decode('utf-8')}"
            )
            continue
    os.chdir(os.path.join(cur_dir, 'OpenROAD/docs'))
    num_cores = os.cpu_count()
    command = f'make clean && make preprocess && make -j{num_cores}'
    res = subprocess.run(command, shell=True, capture_output=True)
    print('Finished building manpages.')

    # copy folder contents to data/markdown/manpages
    src_dir = os.path.join(cur_dir, 'OpenROAD/docs/md')
    dest_dir = os.path.join(cur_dir, 'data/markdown/manpages')
    shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)
    print('Copied manpages to data/markdown/manpages.')

    print('Finished building manpages.')

    return


def get_opensta_docs() -> None:
    url = 'https://github.com/The-OpenROAD-Project/OpenSTA/raw/1c7f022cd0a02ce71d047aa3dbb64e924b6efbd5/doc/OpenSTA.pdf'

    response = requests.get(url)

    save_path = 'data/pdf/OpenSTA/OpenSTA_docs.pdf'
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    if response.status_code == 200:
        with open(save_path, 'wb+') as file:
            file.write(response.content)
        print('OpenSTA docs downloaded successfully.')
    else:
        print('Failed to download file. Status code:', response.status_code)


if __name__ == '__main__':
    docs_paths = ['data']
    purge_folders(folder_paths=docs_paths)

    clone_repo(
        url='https://github.com/The-OpenROAD-Project/OpenROAD.git',
        commit_hash='d48987e36206795f5790e2f48b2e69a03d9029d4',
        folder_name='OpenROAD',
    )
    clone_repo(
        url='https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git',
        commit_hash='3395328e1dd9952de67871f6c4d5963788082fcc',
        folder_name='OpenROAD-flow-scripts',
    )

    os.makedirs('data/markdown/manpages', exist_ok=True)
    os.makedirs('data/markdown/OR_docs', exist_ok=True)
    os.makedirs('data/markdown/ORFS_docs', exist_ok=True)
    os.makedirs('data/markdown/OR_docs/installation', exist_ok=True)
    os.makedirs('data/markdown/OR_docs/tools', exist_ok=True)
    os.makedirs('data/pdf/OpenSTA', exist_ok=True)

    build_or_docs()
    build_orfs_docs()
    build_manpages()

    os.chdir(cur_dir)
    get_opensta_docs()

    update_source_dict('data/markdown/OR_docs')
    update_source_dict('data/markdown/OR_docs/installation')
    update_source_dict('data/markdown/OR_docs/tools')
    update_source_dict('data/markdown/ORFS_docs')
    update_source_dict('data/markdown/ORFS_docs/installation')
    update_source_dict('data/markdown/manpages')
    update_source_dict('data/pdf/OpenSTA')

    repo_paths = ['OpenROAD', 'OpenROAD-flow-scripts']
    purge_folders(folder_paths=repo_paths)

    with open('src/source_list.json', 'w+') as src_file:
        src_file.write(json.dumps(source_dict))
