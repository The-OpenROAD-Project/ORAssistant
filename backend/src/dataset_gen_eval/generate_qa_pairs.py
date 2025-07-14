import json
from pathlib import Path
from typing import List, Dict, Optional
import random

from ..vectorstores.faiss import FAISSVectorDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.docstore.document import Document
from dotenv import load_dotenv

load_dotenv()


# didn't include command_reference cause didn't index it
DOMAINS = [
    "installation_guides",
    "error_messages",
    "opensta_yosys_klayout",
    "general_openroad",
]

QA_PAIRS_PER_DOMAIN = 10

QA_GENERATION_PROMPT = """
Your task is to write a factoid question and an answer given a context.
Your factoid question should be answerable with a specific, concise piece of factual information from the context.
Your factoid question should be formulated in the same style as questions users could ask in a search engine.
This means that your factoid question MUST NOT mention something like "according to the passage" or "context".

Provide your answer as follows:

Output:::
Factoid question: (your factoid question)
Answer: (your answer to the factoid question)

Now here is the context.

Context: {context}\n
Output:::"""


def load_domain_database(domain: str) -> Optional[FAISSVectorDatabase]:
    """Load the FAISS vector database for a specific domain."""
    print(f"Loading vector database for domain: {domain}")

    vdb = FAISSVectorDatabase(
        embeddings_type="HF",
        embeddings_model_name="sentence-transformers/all-MiniLM-L6-v2",
    )

    try:
        vdb.load_db(name=domain)
        print(f"Successfully loaded {domain} database")
        return vdb
    except Exception as e:
        print(f"Error loading database for {domain}: {e}")
        return None


def sample_documents_from_db(
    vdb: FAISSVectorDatabase, num_samples: int = 5
) -> List[Document]:
    """Sample random documents from the vector database to use for QA generation."""
    try:
        all_docs = list(vdb.get_documents())
        print(f"Total documents in database: {len(all_docs)}")

        # Sample random documents
        sample_size = min(num_samples, len(all_docs))
        sampled_docs = random.sample(all_docs, sample_size)

        print(f"Sampled {len(sampled_docs)} documents")
        return sampled_docs

    except Exception as e:
        print(f"Error sampling documents: {e}")
        return []


def generate_qa_pairs_for_content(
    all_docs: List[Document], domain: str, num_qa: int = 5
) -> List[Dict[str, str]]:
    """Use Gemini to generate QA pairs from the given documents."""
    try:
        # Initialize Gemini model
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            temperature=0.3,
        )

        print(f"Generating {num_qa} QA pairs for {domain} domain...")

        all_qa_pairs = []

        for i in range(num_qa):
            try:
                # Sample different documents for each QA pair to get variety
                sample_size = min(5, len(all_docs))
                sampled_docs = random.sample(all_docs, sample_size)

                # Combine content from this sample
                content = "\n\n---DOCUMENT SEPARATOR---\n\n".join(
                    [doc.page_content for doc in sampled_docs]
                )

                prompt = QA_GENERATION_PROMPT.format(context=content[:15000])

                print(f"  Generating QA pair {i + 1}/{num_qa}...")

                # gemini cost analysis here, langsmith
                response = llm.invoke(prompt)

                response_content = response.content
                response_text = response_content.strip() if isinstance(response_content, str) else str(response_content).strip()

                if "Output:::" in response_text:
                    output_section = response_text.split("Output:::")[-1].strip()

                    lines = output_section.split("\n")
                    question = ""
                    answer = ""

                    for line in lines:
                        line = line.strip()
                        if line.startswith("Factoid question:"):
                            question = line.replace("Factoid question:", "").strip()
                        elif line.startswith("Answer:"):
                            answer = line.replace("Answer:", "").strip()

                    if question and answer:
                        qa_pair = {
                            "question": question,
                            "answer": answer,
                            "domain": domain,
                            "source": "generated_from_docs",  # context source add here
                            "context": content[
                                :15000
                            ],  # Add the context used for generation
                        }
                        all_qa_pairs.append(qa_pair)
                        print(f"Generated: {question[:50]}...")
                    else:
                        print("Failed to parse QA pair from response")
                        print(f"Raw response: {response_text[:200]}...")
                else:
                    print("No 'Output:::' section found in response")
                    print(f"Raw response: {response_text[:200]}...")

            except Exception as e:
                print(f"Error generating QA pair {i + 1}: {e}")
                continue

        print(
            f"Successfully generated {len(all_qa_pairs)} QA pairs out of {num_qa} attempts"
        )
        return all_qa_pairs

    except Exception as e:
        print(f"Error in QA generation process: {e}")
        return []


def process_domain(domain: str, qa_per_domain: int = 10) -> List[Dict[str, str]]:
    """Process a single domain to generate QA pairs."""
    print(f"\n{'=' * 50}")
    print(f"Processing domain: {domain}")
    print(f"{'=' * 50}")

    # Load the vector database
    vdb = load_domain_database(domain)
    if not vdb:
        return []

    # Sample documents from the database
    sampled_docs = sample_documents_from_db(vdb, num_samples=100)
    if not sampled_docs:
        return []

    print(f"Will generate QA pairs from pool of {len(sampled_docs)} documents")

    # Generate QA pairs (each QA pair will sample different docs)
    qa_pairs = generate_qa_pairs_for_content(
        all_docs=sampled_docs, domain=domain, num_qa=qa_per_domain
    )

    return qa_pairs


def save_qa_pairs(all_qa_pairs: List[Dict[str, str]], output_file: str):
    """Save the generated QA pairs to a JSON file."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_qa_pairs, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(all_qa_pairs)} QA pairs to: {output_path}")


def main():
    """Main function to generate QA pairs for all domains."""
    print("Starting QA pair generation...")
    print(f"Target domains: {DOMAINS}")
    print(f"QA pairs per domain: {QA_PAIRS_PER_DOMAIN}")

    all_qa_pairs = []

    for domain in DOMAINS:
        try:
            qa_pairs = process_domain(domain, QA_PAIRS_PER_DOMAIN)
            all_qa_pairs.extend(qa_pairs)
            print(f"Generated {len(qa_pairs)} QA pairs for {domain}")

        except Exception as e:
            print(f"Error processing domain {domain}: {e}")
            continue

    # Save all QA pairs
    if all_qa_pairs:
        output_file = "data/generated_qa_pairs_gemini_pro_new.json"
        save_qa_pairs(all_qa_pairs, output_file)

        print(f"{'=' * 50}")
        print(f"Total QA pairs generated: {len(all_qa_pairs)}")

        domain_counts = {}
        for qa in all_qa_pairs:
            domain = qa.get("domain", "unknown")
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

        for domain, count in domain_counts.items():
            print(f"  {domain}: {count} pairs")

    else:
        print("No QA pairs were generated!")


if __name__ == "__main__":
    main()
