from langchain.docstore.document import Document

from ..prompts.prompt_templates import gh_discussion_prompt_template

CHUNK_SEPARATOR = "\n\n -------------------------- \n\n"


def format_docs(docs: list[Document]) -> tuple[str, list[str], list[str], list[str]]:
    doc_text = ""
    doc_texts = []
    doc_urls = []
    doc_srcs = []

    for doc in docs:
        if "source" in doc.metadata:
            doc_src = doc.metadata["source"]
            doc_srcs.append(doc_src)
            if "man1" in doc_src or "man2" in doc_src:
                doc_text = f"Command Name: {doc_src.split('/')[-1].replace('.md', '')}\n\n{doc.page_content}"
            elif "gh_discussions" in doc_src:
                doc_text = f"{gh_discussion_prompt_template}\n\n{doc.page_content}"
            else:
                doc_text = doc.page_content
            doc_texts.append(doc_text)

        if "url" in doc.metadata:
            doc_urls.append(doc.metadata["url"])

    doc_output = CHUNK_SEPARATOR.join(doc_texts)

    return doc_output, doc_srcs, doc_urls, doc_texts
