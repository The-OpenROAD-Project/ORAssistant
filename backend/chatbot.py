import os
import sys
import logging
from uuid import UUID, uuid4
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from sqlalchemy.orm import Session

from src.agents.retriever_graph import RetrieverGraph
from src.database import get_db, init_database
from src.database import crud

from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

load_dotenv()
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper())

console = Console()


def setup_llm() -> ChatVertexAI | ChatGoogleGenerativeAI | ChatOllama:
    temp = float(os.getenv("LLM_TEMP", "0.0"))

    if os.getenv("LLM_MODEL") == "ollama":
        model = str(os.getenv("OLLAMA_MODEL"))
        return ChatOllama(model=model, temperature=temp)

    elif os.getenv("LLM_MODEL") == "gemini":
        gemini = os.getenv("GOOGLE_GEMINI")
        if gemini in {"1_pro", "1.5_flash", "1.5_pro"}:
            raise ValueError(f"Gemini {gemini} (v1.0-1.5) disabled. Use v2.0+")
        elif gemini == "2.0_flash":
            return ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=temp)
        elif gemini == "2.5_flash":
            return ChatVertexAI(model_name="gemini-2.5-flash", temperature=temp)
        elif gemini == "2.5_pro":
            return ChatVertexAI(model_name="gemini-2.5-pro", temperature=temp)
        else:
            raise ValueError(f"Invalid GOOGLE_GEMINI value: {gemini}")

    else:
        raise ValueError(f"Invalid LLM_MODEL: {os.getenv('LLM_MODEL')}")


def setup_embeddings() -> dict[str, str]:
    embed_type = str(os.getenv("EMBEDDINGS_TYPE"))

    if embed_type == "HF":
        model = str(os.getenv("HF_EMBEDDINGS"))
    elif embed_type in {"GOOGLE_GENAI", "GOOGLE_VERTEXAI"}:
        model = str(os.getenv("GOOGLE_EMBEDDINGS"))
    else:
        raise ValueError(f"Invalid EMBEDDINGS_TYPE: {embed_type}")

    return {"type": embed_type, "name": model}


def get_history(
    db: Session | None, conv_id: UUID | None, local_history: list[dict]
) -> str:
    if db and conv_id:
        history = crud.get_conversation_history(db, conv_id)
        result = ""
        for msg in history:
            user = msg.get("User", "")
            ai = msg.get("AI", "")
            if user and ai:
                result += f"User : {user}\nAI : {ai}\n\n"
        return result
    else:
        result = ""
        for msg in local_history:
            user = msg.get("User", "")
            ai = msg.get("AI", "")
            if user and ai:
                result += f"User : {user}\nAI : {ai}\n\n"
        return result


def parse_output(output: list) -> tuple[str, list[str], list[str]]:
    fail_msg = "Failed to get response"

    if not isinstance(output, list) or len(output) < 3:
        return fail_msg, [], []

    last = output[-1]
    if not isinstance(last, dict):
        return fail_msg, [], []

    is_rag = "rag_generate" in last
    key = "rag_generate" if is_rag else "generate"

    if key not in last or "messages" not in last[key]:
        return fail_msg, [], []

    msgs = last[key]["messages"]
    if not msgs:
        return fail_msg, [], []

    response = str(msgs[0])
    sources = []
    tools = []

    if is_rag:
        for item in output[1:-1]:
            if isinstance(item, dict):
                for k, v in item.items():
                    if k.startswith("retrieve_") and isinstance(v, dict):
                        urls = v.get("urls", [])
                        sources.extend(urls)
    else:
        if "agent" in output[0] and "tools" in output[0]["agent"]:
            tools = output[0]["agent"]["tools"]
            for i in range(len(tools)):
                if i + 1 < len(output):
                    tool_out = list(output[i + 1].values())[0]
                    urls = tool_out.get("urls", [])
                    sources.extend(urls)

    return response, list(set(sources)), tools


def show_response(text: str, sources: list[str], tools: list[str]) -> None:
    console.print(
        Panel(Markdown(text), title="[bold cyan]Assistant", border_style="cyan")
    )

    if tools:
        console.print(f"[yellow]Tools:[/yellow] {', '.join(tools)}")

    if sources:
        src_table = Table(title="Sources", show_header=False, border_style="dim")
        src_table.add_column("URL", style="blue")
        for src in sources:
            src_table.add_row(src)
        console.print(src_table)

    console.print()


def main() -> None:
    console.clear()
    console.print(
        Panel("[bold green]ORAssistant Chatbot[/bold green]", border_style="green")
    )

    cuda = str(os.getenv("USE_CUDA")).lower() == "true"
    fast = str(os.getenv("FAST_MODE")).lower() == "true"
    debug = str(os.getenv("DEBUG")).lower() == "true"
    mcp = str(os.getenv("ENABLE_MCP")).lower() == "true"
    use_db = str(os.getenv("USE_DB", "true")).lower() == "true"

    llm = setup_llm()
    embed_cfg = setup_embeddings()
    reranker = str(os.getenv("HF_RERANKER"))

    with console.status("[bold green]Initializing graph...", spinner="dots"):
        graph = RetrieverGraph(
            llm_model=llm,
            embeddings_config=embed_cfg,
            reranking_model_name=reranker,
            use_cuda=cuda,
            inbuilt_tool_calling=True,
            fast_mode=fast,
            debug=debug,
            enable_mcp=mcp,
        )
        graph.initialize()

    if graph.graph is None:
        console.print("[bold red]Failed to initialize graph[/bold red]")
        sys.exit(1)

    db = None
    conv_id = None
    local_history: list[dict[str, str]] = []

    if use_db:
        if init_database():
            db = next(get_db())
            conv_id = uuid4()
            crud.create_conversation(db, conversation_uuid=conv_id, title=None)
            console.print("[dim]Database: enabled[/dim]")
        else:
            console.print("[yellow]Database unavailable, using local memory[/yellow]")
            use_db = False
    else:
        console.print("[dim]Database: disabled[/dim]")

    console.print("[dim]Type 'exit' or 'quit' to end session[/dim]\n")

    while True:
        try:
            query = Prompt.ask("[bold blue]You[/bold blue]")

            if query.lower() in {"exit", "quit", "q"}:
                console.print("[yellow]Goodbye![/yellow]")
                break

            if not query.strip():
                continue

            if use_db and db and conv_id:
                crud.create_message(
                    db=db,
                    conversation_uuid=conv_id,
                    role="user",
                    content=query,
                )

            inputs = {
                "messages": [("user", query)],
                "chat_history": get_history(db, conv_id, local_history),
            }

            with console.status("[bold green]Thinking...", spinner="dots"):
                output = list(graph.graph.stream(inputs, stream_mode="updates"))

            response, sources, tools = parse_output(output)

            if use_db and db and conv_id:
                ctx_srcs = {"sources": [{"source": s, "context": ""} for s in sources]}
                crud.create_message(
                    db=db,
                    conversation_uuid=conv_id,
                    role="assistant",
                    content=response,
                    context_sources=ctx_srcs,
                    tools=tools,
                )
            else:
                local_history.append({"User": query, "AI": response})

            show_response(response, sources, tools)

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            if debug:
                logging.exception("Error in main loop")


if __name__ == "__main__":
    main()
