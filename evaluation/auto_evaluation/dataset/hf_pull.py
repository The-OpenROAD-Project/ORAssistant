from huggingface_hub import snapshot_download
import os

if __name__ == "__main__":
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    snapshot_download(
        "The-OpenROAD-Project/ORAssistant_Public_Evals",
        revision="main",
        local_dir=cur_dir,
        repo_type="dataset",
        ignore_patterns=[
            ".gitattributes",
            "README.md",
        ],
    )
