import os
import requests
import json
import shutil
from bs4 import BeautifulSoup

source_dict = {}


def check_and_purge_docs():
    folder_paths = ["data/markdown/OR_docs", "data/markdown/ORFS_docs"]
    for folder_path in folder_paths:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            print(f"Purging existing docs, Folder {folder_path} deleted.")


def download_markdown(url: str, folder_name: str) -> None:
    path = url.split("latest/")[-1]
    base_url = url.replace("latest/", "latest/_sources/")
    path = path.replace("html", "md")
    dl_url = base_url.replace("html", "md")
    response = requests.get(dl_url)

    if response.status_code == 200:
        markdown_content = response.text
        file_name = f"data/markdown/{folder_name}/{path.replace("/", "_")}"
        if os.path.isfile(file_name):
            file_name, file_extension = os.path.splitext(file_name)
            file_name = file_name + "_1" + file_extension
        with open(file_name, "w+", encoding="utf-8") as file:
            file.write(markdown_content)
        print(f"{url} - Saved OK - {file_name}")
        source_dict[file_name] = url
    else:
        print(f"{url} - ERROR - Status code: {response.status_code}")


def get_href_list(url) -> list[str]:
    try:
        hrefs = []
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        soup_list = [a["href"] for a in soup.select("a")]
        for a in soup_list:
            if (
                "https" not in a and "#" not in a and "mailto" not in a
            ):  # remove external links and heading links
                hrefs.append(f"{url}/{a}")
        return hrefs
    except Exception as e:
        print("Error:", e)
        return []


def scrape_url(url: str, folder_name: str) -> None:
    hrefs = set(get_href_list(url))

    print(f"{len(hrefs)} links found on", url, "are:")
    for href in hrefs:
        download_markdown(href, folder_name)


if __name__ == "__main__":
    check_and_purge_docs()

    os.makedirs("data/", exist_ok=True)
    os.makedirs("data/markdown/", exist_ok=True)
    os.makedirs("data/markdown/OR_docs", exist_ok=True)
    os.makedirs("data/markdown/ORFS_docs", exist_ok=True)

    url = "https://openroad.readthedocs.io/en/latest"
    scrape_url(url, "OR_docs")

    url = "https://openroad-flow-scripts.readthedocs.io/en/latest"
    scrape_url(url, "ORFS_docs")

    source_dict["data/json/OR-github_discussions.txt"] = "OpenROAD GitHub Discussions"
    source_dict["data/json/OR-github_issues.txt"] = "OpenROAD GitHub Issues"

    with open("src/source_list.json", "w+") as src_file:
        src_file.write(json.dumps(source_dict))
