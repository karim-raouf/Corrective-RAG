import re
from langchain.schema import Document
from typing import List
import os


def parse_chunk_markdown_files(md_file_paths: List[str]) -> List[Document]:
    chunks = []
    chunk_counter = 1  # sequential counter for chunk codes

    for md_file_path in md_file_paths:
        # Load the Markdown content
        with open(md_file_path, "r", encoding="utf-8") as f:
            markdown_text = f.read()

        source_name = os.path.basename(md_file_path)
        
        current_level1_title = None
        current_level2_title = None
        current_level3_title = None
        current_level4_title = None
        current_page = None
        buffer = []  # accumulate lines for the current chunk

        def flush_buffer():
            """Create a chunk from buffered lines if buffer is not empty"""
            nonlocal chunk_counter
            if buffer:
                chunk_id = f"CHUNK-{chunk_counter:04d}"  # e.g., CHUNK-0001
                chunks.append({
                    "chunk_id": chunk_id,
                    "level1_title": current_level1_title,
                    "level2_title": current_level2_title,
                    "level3_title": current_level3_title,
                    "level4_title": current_level4_title,
                    "page_number": current_page,
                    "source": source_name,
                    "content": "\n".join(buffer).strip()
                })
                buffer.clear()
                chunk_counter += 1

        for line in markdown_text.splitlines():
            # Manual split for large tables
            if line.strip() == "-- split --":
                flush_buffer()
                continue

            # Detect page breaks
            page_match = re.match(r"-- page (.*?) --", line)
            if page_match:
                current_page = str(page_match.group(1))
                continue

            # Detect titles
            if line.startswith("# "):
                flush_buffer()
                current_level1_title = line[2:].strip()
                current_level2_title = None
                current_level3_title = None
                current_level4_title = None
                continue

            if line.startswith("## "):
                flush_buffer()
                current_level2_title = line[3:].strip()
                current_level3_title = None
                current_level4_title = None
                continue

            if line.startswith("### "):
                flush_buffer()
                current_level3_title = line[4:].strip()
                current_level4_title = None
                continue

            if line.startswith("#### "):
                flush_buffer()
                current_level4_title = line[5:].strip()
                continue

            # Normal text → add to buffer
            buffer.append(line)

        # Flush remaining buffer for this file
        flush_buffer()

    # Convert to LangChain Document objects
    documents = [
    Document(
        page_content=chunk["content"],
        metadata={
            "chunk_id": chunk["chunk_id"],
            "level1_title": chunk["level1_title"].lower() if chunk["level1_title"] else None,
            "level2_title": chunk["level2_title"].lower() if chunk["level2_title"] else None,
            "level3_title": chunk["level3_title"].lower() if chunk["level3_title"] else None,
            "level4_title": chunk["level4_title"].lower() if chunk["level4_title"] else None,
            "page_number": chunk["page_number"],
            "source": chunk["source"]
        }
    )
    for chunk in chunks
]


    # Remove empty content documents
    filtered_documents = [doc for doc in documents if doc.page_content.strip()]
    return filtered_documents
