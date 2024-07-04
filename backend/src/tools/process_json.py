import json

from langchain.docstore.document import Document


def parse_json(json_object) -> str:
    parsed_text = "Infer knowledge from this conversation and use it to answer the given question.\n\t"
    for body in json_object["messages"]:
        if "user" in body:
            parsed_text += f"\nUser1: {body["user"].strip()}"
        if "assistant" in body:
            parsed_text += f"\nUser2: {body["assistant"].strip()}"

    return parsed_text


def generate_knowledge_base(file_paths: list[str]) -> list[Document]:
    json_knowledge_base = []
    for file_path in file_paths:
        try:
            with open(file_path, "r") as file:
                print(f"Processing {file_path}...")
                for line in file:
                    try:
                        json_object = json.loads(line)
                        json_knowledge_base.append(
                            Document(
                                page_content=str(parse_json(json_object)),
                                metadata={"source": file_path},
                            )
                        )
                    except json.JSONDecodeError:
                        print("Error: Invalid JSON format line:", line)
        except FileNotFoundError:
            print(f"{file_path} not found.")

    return json_knowledge_base
