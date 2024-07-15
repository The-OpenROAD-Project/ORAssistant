from langchain.docstore.document import Document


def format_docs(docs: list[Document]) -> str:
    formatted_text = ''
    for doc in docs:
        if doc.metadata is not None and 'source' in doc.metadata:
            title = str(doc.metadata['source'].split('data/markdown')[1])
            title = (
                title.replace('.md', '')
                .replace('/', ' - ')
                .replace('ORFS', 'OpenROAD-flow-scripts')
                .replace('OR', 'OpenROAD')
                .replace('_', ' ')
                .upper()
            )
            formatted_text += (
                f'\n{title}\n{doc.page_content}'
                + '\n- - - - - -  - - - - - - - - - - - - - - - -\n\n'
            )
        else:
            formatted_text += doc.page_content

    return formatted_text
