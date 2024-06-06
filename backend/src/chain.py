from dotenv import load_dotenv

from langchain.prompts import ChatPromptTemplate
from langchain.retrievers import EnsembleRetriever
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough,RunnableParallel

from src.faiss_vector_retriever import FAISSVectorDatabase

import json

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-pro",temperature=1)

vector_db = FAISSVectorDatabase(embeddings_model_name="thenlper/gte-large" , print_progress=True)

prompt_template_str = """Your task is to act as a knowledgeable assistant for users seeking information and guidance about the OpenROAD project. Avoid speculating or inventing information beyond the scope of the provided data. 

Use the following context:

{context}

-------------------------------------------------------------------------------------------------

Give a detailed answer to this question: 

{question}

"""
prompt_template = ChatPromptTemplate.from_template(prompt_template_str)

or_docs_vector_db = vector_db.process_md(folder_paths=["./data/markdown/OR_docs"])
orfs_docs_vector_db = vector_db.process_md(folder_paths=["data/markdown/ORFS_docs"])

k = [3,3,2]
or_docs_retriever = or_docs_vector_db.as_retriever(search_kwargs={"k": k[0]})
orfs_docs_retriever = orfs_docs_vector_db.as_retriever(search_kwargs={"k":k[1]})

ensemble_retriever = EnsembleRetriever(
    retrievers = [or_docs_retriever,orfs_docs_retriever],
    weights = [0.5,0.5]
)

def format_docs(docs):
    formatted_text = ""
    q_a = ""
    for d in docs:
        if "Infer knowledge from this conversation and use it to answer the given question" in d.page_content:
            q_a_summarized = llm.invoke("This is a conversation between User1 and User2. Infer knowledge from it and give me bullet points: " + d.page_content)
            d.page_content = d.page_content.replace("\n","")
            q_a += d.page_content + f"\nSummary:{q_a_summarized.content}" +"\nSource: " + str(d.metadata) + "\n\n"
            continue
        formatted_text = formatted_text + d.page_content + "\nSource: " + str(d.metadata) + "\n - - - - - - - - - -\n\n"
    formatted_text = formatted_text + "\n" +q_a + "\n"

    return formatted_text

output_parser = StrOutputParser()

llm_chain =  (
    RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
    | prompt_template 
    | llm 
    | output_parser
)

llm_chain_with_source = RunnableParallel(
    {"context": ensemble_retriever, "question": RunnablePassthrough()} 
).assign(answer=llm_chain)

with open("src/source_list.json") as f:
    src_dict = json.loads(f.read())

if __name__ == "__main__":
    while(True):
        links = []
        user_question = input("Ask a question: ")
        result = llm_chain_with_source.invoke(user_question)

        for i in result['context']:
            links.append(src_dict[i.metadata['source']])
        
        links = set(links)

        print(result['answer'])

        print("\n\nSources:")
        for i in links:
            print(i + "\n")



