import logging
import time
import json
import os
from typing import TypedDict
from dotenv import load_dotenv

# LangChain/LangGraph imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

# Local imports
from src.schema import DocumentIssues
from src.system_prompt import system_prompt

# --- Setup and Configuration ---

LOG_FORMAT = "%(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, force=True)
logger = logging.getLogger(__name__)

load_dotenv()

MODEL_NAME = "gemini-2.5-flash"
MAX_DOCUMENTS = 200
API_DELAY_SECONDS = 60  # seconds
OUTPUT_DIR = "src/temp"  # output dir

logger.info(
    f"⚙️ Config: Model={MODEL_NAME}, Docs={MAX_DOCUMENTS}, Delay={API_DELAY_SECONDS}s"
)

# --- State Definition ---


class DocumentProcessingState(TypedDict):
    document_index: int
    llm_output_content: str


# --- LLM Configuration ---

llm = ChatGoogleGenerativeAI(model=MODEL_NAME)
llm.with_structured_output(DocumentIssues)

# --- Graph Nodes (Functions) ---


def initialize_processing(state: DocumentProcessingState) -> DocumentProcessingState:
    logger.info("✨ Graph initialized. Index set to 0.")
    return {"document_index": 0, "llm_output_content": ""}


def invoke_llm_for_document(state: DocumentProcessingState) -> DocumentProcessingState:
    current_index = state.get("document_index", 0)
    logger.info(f"➡️ Calling LLM for Doc #{current_index + 1}...")
    try:
        llm_response = llm.invoke(system_prompt)
        content = llm_response.content
        logger.info("✅ LLM response received.")

        return {"llm_output_content": content}  # type:ignore
    except Exception as e:
        logger.error(f"❌ FATAL Error on Doc #{current_index + 1}: {e}")
        raise


def decide_if_more_documents_needed(state: DocumentProcessingState) -> str:
    current_index = state.get("document_index", 0)

    if current_index >= MAX_DOCUMENTS:
        logger.info("🛑 Loop decision: Max documents reached. Ending.")
        return "end_process"
    else:
        logger.info("🔁 Loop decision: Continuing.")
        return "continue_processing"


def save_and_increment_index(state: DocumentProcessingState) -> DocumentProcessingState:
    """Implements saving, throttling, and increments the document index."""

    current_index = state.get("document_index", 0)
    llm_content = state.get("llm_output_content", "")

    file_name = f"{current_index + 1:03d}_doc.json"
    file_path = os.path.join(OUTPUT_DIR, file_name)

    try:
        # Wrap content in a structure for valid JSON output
        save_data = {
            "document_index": current_index + 1,
            "llm_raw_content": llm_content,
        }
        with open(file_path, "w") as f:
            json.dump(save_data, f, indent=4)
        logger.info(f"💾 Saved output to: {file_path}")

    except Exception as e:
        logger.error(f"❌ File Save Error: Could not save to {file_path}. {e}")

    # Throttling/Delay
    logger.info(f"⏳ Throttling: Sleeping for {API_DELAY_SECONDS}s...")
    time.sleep(API_DELAY_SECONDS)

    new_index = current_index + 1
    logger.info(f"🔢 Index incremented: {current_index} -> {new_index}")

    return {"document_index": new_index, "llm_output_content": ""}


# --- Graph Definition ---

document_graph = StateGraph(DocumentProcessingState)

document_graph.add_node("initialize", initialize_processing)
document_graph.add_node("process_document", invoke_llm_for_document)
document_graph.add_node("save_and_increment", save_and_increment_index)

document_graph.set_entry_point("initialize")

document_graph.add_edge("initialize", "process_document")
document_graph.add_edge("process_document", "save_and_increment")

document_graph.add_conditional_edges(
    "save_and_increment",
    decide_if_more_documents_needed,
    {
        "continue_processing": "process_document",
        "end_process": END,
    },
)

document_processing_app = document_graph.compile()
logger.info("🚀 Graph compiled and ready.")

# Execute
document_processing_app.invoke({"document_index": 0, "llm_output_content": ""})
