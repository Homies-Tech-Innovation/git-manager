import time
import json
import os
from typing import TypedDict
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from src.schema import DocumentIssues
from src.system_prompt import get_prompt
from src.topics import topics
from src.logger import logger

load_dotenv()


class Config:
    MODEL_NAME = "gemini-2.5-flash"
    MAX_DOCUMENTS = len(topics)
    API_DELAY_SECONDS = 60
    OUTPUT_DIR = "src/temp"


class DocumentProcessingState(TypedDict):
    document_index: int
    llm_output_content: str


class DocumentProcessor:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model=Config.MODEL_NAME)
        self.structured_llm = self.llm.with_structured_output(DocumentIssues)
        self._ensure_output_dir()

        logger.info(
            f"Initialized processor │ model={Config.MODEL_NAME} │ max_docs={Config.MAX_DOCUMENTS} │ delay={Config.API_DELAY_SECONDS}s"
        )

    def _ensure_output_dir(self):
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)

    def _generate_filename(self, index: int) -> str:
        return os.path.join(Config.OUTPUT_DIR, f"{index:03d}_doc.json")

    def _save_document(self, content: str, index: int) -> bool:
        file_path = self._generate_filename(index + 1)

        try:
            if isinstance(content, str):
                save_data = json.loads(content)
            else:
                save_data = content

            if (
                not isinstance(save_data, dict)
                or "doc" not in save_data
                or "issues" not in save_data
            ):
                logger.warning(f"Unexpected output structure │ index={index + 1}")

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            issues_count = len(save_data.get("issues", []))
            doc_length = len(save_data.get("doc", ""))
            logger.info(
                f"Saved document │ file={os.path.basename(file_path)} │ issues={issues_count} │ doc_length={doc_length}"
            )

            return True

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode failed │ index={index + 1} │ error={str(e)}")
            fallback_path = file_path.replace(".json", "_raw.txt")
            with open(fallback_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Saved raw content │ file={os.path.basename(fallback_path)}")
            return False

        except Exception as e:
            logger.error(f"Save failed │ index={index + 1} │ error={str(e)}")
            return False

    def initialize_processing(
        self, state: DocumentProcessingState
    ) -> DocumentProcessingState:
        logger.info("Processing initialized │ starting_index=0")
        return {"document_index": 0, "llm_output_content": ""}

    def invoke_llm_for_document(
        self, state: DocumentProcessingState
    ) -> DocumentProcessingState:
        current_index = state.get("document_index", 0)
        logger.info(
            f"Invoking LLM │ document_index={current_index + 1}/{Config.MAX_DOCUMENTS}"
        )

        try:
            llm_response = self.structured_llm.invoke(get_prompt(topics[current_index]))

            if hasattr(llm_response, "model_dump"):
                content = llm_response.model_dump()
            else:
                content = llm_response

            logger.info(f"LLM response received │ document_index={current_index + 1}")
            return {"llm_output_content": json.dumps(content)}  # type:ignore

        except Exception as e:
            logger.error(
                f"LLM invocation failed │ document_index={current_index + 1} │ error={str(e)}"
            )
            raise

    def decide_if_more_documents_needed(self, state: DocumentProcessingState) -> str:
        current_index = state.get("document_index", 0)

        if current_index >= Config.MAX_DOCUMENTS:
            logger.info(
                f"Processing complete │ processed={current_index}/{Config.MAX_DOCUMENTS}"
            )
            return "end_process"
        else:
            logger.info(
                f"Continuing processing │ next_index={current_index + 1}/{Config.MAX_DOCUMENTS}"
            )
            return "continue_processing"

    def save_and_increment_index(
        self, state: DocumentProcessingState
    ) -> DocumentProcessingState:
        current_index = state.get("document_index", 0)
        llm_content = state.get("llm_output_content", "")

        self._save_document(llm_content, current_index)

        logger.info(f"Rate limiting │ delay={Config.API_DELAY_SECONDS}s")
        time.sleep(Config.API_DELAY_SECONDS)

        new_index = current_index + 1
        logger.info(f"Index incremented │ {current_index} -> {new_index}")

        return {"document_index": new_index, "llm_output_content": ""}

    def build_graph(self):
        graph = StateGraph(DocumentProcessingState)

        graph.add_node("initialize", self.initialize_processing)
        graph.add_node("process_document", self.invoke_llm_for_document)
        graph.add_node("save_and_increment", self.save_and_increment_index)

        graph.set_entry_point("initialize")

        graph.add_edge("initialize", "process_document")
        graph.add_edge("process_document", "save_and_increment")

        graph.add_conditional_edges(
            "save_and_increment",
            self.decide_if_more_documents_needed,
            {
                "continue_processing": "process_document",
                "end_process": END,
            },
        )

        return graph.compile()

    def run(self):
        logger.info("Starting document processing pipeline")
        start_time = time.time()

        try:
            app = self.build_graph()
            app.invoke(
                {"document_index": 0, "llm_output_content": ""},
                {"recursion_limit": Config.MAX_DOCUMENTS + 5},
            )

            elapsed_time = time.time() - start_time
            logger.info(f"Pipeline completed │ duration={elapsed_time:.2f}s")

        except Exception as e:
            logger.error(f"Pipeline failed │ error={str(e)}")
            raise


def main():
    processor = DocumentProcessor()
    processor.run()


if __name__ == "__main__":
    main()
