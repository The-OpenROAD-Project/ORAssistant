from huggingface_hub import HfApi, snapshot_download
import os

DATASET_REPO = "The-OpenROAD-Project/ORAssistant_Public_Evals"


def main() -> str:
    """Download the eval dataset and return the Hugging Face commit it came from."""
    # Resolve the branch first and download that commit, so the recorded
    # revision is the data that was evaluated even if the branch moves.
    revision: str = HfApi().dataset_info(DATASET_REPO, revision="main").sha
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    snapshot_download(
        DATASET_REPO,
        revision=revision,
        local_dir=cur_dir,
        repo_type="dataset",
        ignore_patterns=[
            ".gitattributes",
            "README.md",
        ],
    )
    return revision


if __name__ == "__main__":
    print(main())
