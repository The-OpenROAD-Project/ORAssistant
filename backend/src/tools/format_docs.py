def format_docs(docs) -> str:
    formatted_text = ""
    for doc in docs:
        title = str(doc.metadata['source'].split("data/markdown")[1])
        title = title.replace(".md","").replace("/"," - ").replace("ORFS","OpenROAD-flow-scripts").replace("OR","OpenROAD").replace("_"," ").upper()
        formatted_text +=  f"Title {title}\n{doc.page_content}" + "\n - - - - - - - - - - - - - - - -\n\n"
        
    return formatted_text