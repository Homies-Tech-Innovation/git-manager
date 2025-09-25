import logging
import time
import json
import os
import uuid
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
API_DELAY_SECONDS = 60
OUTPUT_DIR = "src/temp"

logger.info(
    f"⚙️ Config: Model={MODEL_NAME}, Docs={MAX_DOCUMENTS}, Delay={API_DELAY_SECONDS}s"
)

# --- State Definition ---


class DocumentProcessingState(TypedDict):
    document_index: int
    llm_output_content: str


# --- LLM Configuration ---

llm = ChatGoogleGenerativeAI(model=MODEL_NAME)
# IMPORTANT: This should return structured output, not just text
structured_llm = llm.with_structured_output(DocumentIssues)

# --- Graph Nodes (Functions) ---


def initialize_processing(state: DocumentProcessingState) -> DocumentProcessingState:
    logger.info("✨ Graph initialized. Index set to 0.")
    return {"document_index": 0, "llm_output_content": ""}


def invoke_llm_for_document(state: DocumentProcessingState) -> DocumentProcessingState:
    current_index = state.get("document_index", 0)
    logger.info(f"➡️ Calling LLM for Doc #{current_index + 1}...")
    try:
        # Use structured LLM to get DocumentIssues object
        llm_response = structured_llm.invoke(system_prompt)

        # llm_response should now be a DocumentIssues object, not just text
        if hasattr(llm_response, "model_dump"):
            # Convert Pydantic model to dict
            content = llm_response.model_dump()
        else:
            # Fallback if it's already a dict
            content = llm_response

        logger.info("✅ LLM structured response received.")
        logger.info(f"📄 Doc length: {len(content.get('doc', ''))}")
        logger.info(f"🎯 Issues count: {len(content.get('issues', []))}")

        return {"llm_output_content": json.dumps(content)}  # Store as JSON string

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

    # Generate a unique filename using a UUID to prevent overwrites
    file_name = f"{uuid.uuid4()}_doc.json"
    file_path = os.path.join(OUTPUT_DIR, file_name)

    try:
        # Parse the JSON string back to object for proper saving
        if isinstance(llm_content, str):
            save_data = json.loads(llm_content)
        else:
            save_data = llm_content

        # Validate the structure
        if (
            not isinstance(save_data, dict)
            or "doc" not in save_data
            or "issues" not in save_data
        ):
            logger.warning("⚠️ Unexpected output structure, saving as-is")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Saved output to: {file_path}")
        logger.info(f"📊 Saved: {len(save_data.get('issues', []))} issues")

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON Parse Error: {e}")
        # Save as plain text if JSON parsing fails
        with open(file_path.replace(".json", "_raw.txt"), "w", encoding="utf-8") as f:
            f.write(llm_content)
        logger.info(
            f"💾 Saved raw content to: {file_path.replace('.json', '_raw.txt')}"
        )

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
if __name__ == "__main__":
    document_processing_app.invoke({"document_index": 0, "llm_output_content": ""})
