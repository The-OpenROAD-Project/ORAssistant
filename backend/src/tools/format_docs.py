from langchain.docstore.document import Document


def format_docs(docs: list[Document]) -> str:
    formatted_text = ''
    for doc in docs:
        source = doc.metadata.get('source', '')
        if 'data/markdown' in source:
            parts = source.split('data/markdown')
            if len(parts) > 1:
                title = parts[1]
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
                print('Title part not found. Skipping')
                formatted_text += doc.page_content
        else:
            print('Source not found. Skipping')
            formatted_text += doc.page_content

    return formatted_text
