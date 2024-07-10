import os
import subprocess
import sys
import requests
import json
import shutil
from bs4 import BeautifulSoup

source_dict = {}


def check_and_purge_docs() -> None:
    folder_paths = [
        'data/markdown/OR_docs',
        'data/markdown/ORFS_docs',
        'data/markdown/manpages',
    ]
    for folder_path in folder_paths:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            print(f'Purging existing docs, Folder {folder_path} deleted.')


def download_markdown(url: str, folder_name: str) -> None:
    path = url.split('latest/')[-1]
    base_url = url.replace('latest/', 'latest/_sources/')
    path = path.replace('html', 'md')
    dl_url = base_url.replace('html', 'md')
    response = requests.get(dl_url)

    if response.status_code == 200:
        file_name = path.replace('/', '_')

        if 'build' in file_name.lower():
            folder_name += '/installation'
        elif 'main_src' in file_name.lower():
            folder_name += '/tools'

        markdown_content = response.text
        file_name = f"data/markdown/{folder_name}/{path.replace('/', '_')}"
        if os.path.isfile(file_name):
            file_name, file_extension = os.path.splitext(file_name)
            file_name = file_name + '_1' + file_extension
        with open(file_name, 'w+', encoding='utf-8') as file:
            file.write(markdown_content)
        print(f'{url} - Saved OK - {file_name}')
        source_dict[file_name] = url
    else:
        print(f'{url} - ERROR - Status code: {response.status_code}')


def get_href_list(url: str) -> list[str]:
    try:
        hrefs = []
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        soup_list = [a['href'] for a in soup.select('a')]
        for a in soup_list:
            if (
                'https' not in a and '#' not in a and 'mailto' not in a
            ):  # remove external links and heading links
                hrefs.append(f'{url}/{a}')
        return hrefs
    except Exception as e:
        print('Error:', e)
        return []


def scrape_url(url: str, folder_name: str) -> None:
    hrefs = set(get_href_list(url))

    print(f'{len(hrefs)} links found on', url, 'are:')
    for href in hrefs:
        download_markdown(href, folder_name)


def get_manpages() -> None:
    print("Starting manpages build...")

    # clone repo
    or_url = "https://github.com/The-OpenROAD-Project/OpenROAD"
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    target_dir = os.path.join(cur_dir, "OpenROAD")
    command = f"git clone {or_url} --depth 1 {target_dir}"
    res = subprocess.run(command, shell=True, capture_output=True)
    if res.returncode != 0:
        print(f"Error in cloning OpenROAD: {res.stderr}")
        sys.exit(1)
    print("Cloned OpenROAD successfully.")

    # check if pandoc is installed, if not error out.
    res = subprocess.run("pandoc --version", shell=True, capture_output=True)
    if res.returncode != 0:
        print("Pandoc is not installed. Please install it.")
        sys.exit(1)
    print("Pandoc is installed.")

    # generate manpages
    command = "../../etc/find_messages.py > messages.txt"
    for module in os.listdir(os.path.join(cur_dir, "OpenROAD/src")):
        path = os.path.join(cur_dir, "OpenROAD/src", module)
        if not os.path.isdir(path):
            continue
        print("Processing module:", module)
        os.chdir(path)
        res = subprocess.run(command, shell=True, capture_output=True)
        if res.returncode != 0:
            print(f"Error in finding messages for {module}: {res.stderr}")
            continue
    os.chdir(os.path.join(cur_dir, "OpenROAD/docs"))
    num_cores = os.cpu_count()
    command = f"make clean && make preprocess && make -j{num_cores}"
    res = subprocess.run(command, shell=True, capture_output=True)
    print("Finished building manpages.")

    # copy folder contents to data/markdown/manpages
    src_dir = os.path.join(cur_dir, "OpenROAD/docs/md")
    dest_dir = os.path.join(cur_dir, "data/markdown/manpages")
    shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)
    print("Copied manpages to data/markdown/manpages.")

    # update source_dict
    for root, _, files in os.walk(dest_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_name = os.path.basename(file_path)
            source_dict[file_path] = file_name

    # change back to the file directory
    os.chdir(cur_dir)
    shutil.rmtree("OpenROAD")
    print("Removed OpenROAD temp directory.")


if __name__ == "__main__":
    check_and_purge_docs()

    os.makedirs("data/markdown/OR_docs", exist_ok=True)
    os.makedirs("data/markdown/ORFS_docs", exist_ok=True)
    os.makedirs("data/markdown/manpages", exist_ok=True)

    # OR docs
    url = "https://openroad.readthedocs.io/en/latest"
    scrape_url(url, "OR_docs")

    # ORFS docs
    url = "https://openroad-flow-scripts.readthedocs.io/en/latest"
    scrape_url(url, "ORFS_docs")

    # Json
    source_dict["data/json/OR-github_discussions.txt"] = "OpenROAD GitHub Discussions"
    source_dict["data/json/OR-github_issues.txt"] = "OpenROAD GitHub Issues"

    # Manpages
    get_manpages()

    with open("src/source_list.json", "w+") as src_file:
        src_file.write(json.dumps(source_dict))
