import os
import logging
from src.api.routers import graphs


def get_history_str(chat_history: list[dict[str, str]]) -> str:
    history_str = ""
    for i in chat_history:
        history_str += f"User : {i['User']}\nAI : {i['AI']}\n\n"
    return history_str


chat_history: list[dict[str, str]] = []

if __name__ == "__main__":
    rg = graphs.rg
    os.system("clear")

    while True:
        user_question = input(">>> ")

        inputs = {
            "messages": [
                ("user", user_question),
            ],
            "chat_history": get_history_str(chat_history=chat_history),
        }

        try:
            if rg.graph is not None:
                output = list(rg.graph.stream(inputs))

            else:
                raise ValueError("RetrieverGraph not initialized.")
        except RuntimeError:
            logging.error("Runtime Error!")

        if (
            isinstance(output, list)
            and len(output) > 2
            and "rag_generate" in output[-1]
            and "messages" in output[-1]["rag_generate"]
            and len(output[-1]["rag_generate"]["messages"]) > 0
        ):
            llm_response = output[-1]["rag_generate"]["messages"][0]

            tool = list(output[-2].keys())[0]
            srcs = set(output[-2][tool]["sources"])
            urls = output[-2][tool]["urls"]
            chat_history.append({"User": user_question, "AI": llm_response})

            print(f"LLM: {llm_response} \nSources: {srcs} \nURLs: {urls}\n\n")

        elif (
            isinstance(output, list)
            and len(output) > 2
            and "mcp_tools" in output[-1]
            and "messages" in output[-1]["mcp_tools"]
        ):
            logging.info(output)
            llm_response = output[-1]["mcp_tools"]["messages"][0]
            chat_history.append({"User": user_question, "AI": llm_response})
            result = output[-1]["mcp_tools"]["messages"]
            print()
            if len(result) > 0:
                for _ in result:
                    print(_)
            else:
                print("No Message!")
        else:
            logging.info(output)
            print("LLM response extraction failed")
