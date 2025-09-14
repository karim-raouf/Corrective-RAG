from langchain_chroma import Chroma
from models import embeddings
from langchain.schema import Document
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
import os
import pickle
from .loading_chunking_MD import parse_markdown_to_documents
from typing import List, Dict, Any

def build_hybrid_retriever(
    markdown_path: str = "D:/Kinnovia documents/Code Implementations/CRAG-implementation/Corrective-RAG/src/documents/ASPICE_MD.md",
    persist_dir: str = "D:/Kinnovia documents/Code Implementations/CRAG-implementation/Corrective-RAG/src/databases/"
):
    # Ensure persist directory exists
    os.makedirs(persist_dir, exist_ok=True)

    # 1️⃣ Build/load vector store
    if os.path.exists(persist_dir) and os.listdir(persist_dir):
        vector_store = Chroma(
            embedding_function=embeddings,
            persist_directory=persist_dir
        )
    else:
        # Load documents from markdown and parse
        chunks = parse_markdown_to_documents(markdown_path)

        # Build BM25 retriever once and persist it
        bm25_retriever = BM25Retriever.from_documents(chunks)
        bm25_retriever.k = 10
        with open(os.path.join(persist_dir, "bm25.pkl"), "wb") as f:
            pickle.dump(bm25_retriever, f)

        print("Creating vector store...")
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=persist_dir
        )

    # Load BM25 retriever
    with open(os.path.join(persist_dir, "bm25.pkl"), "rb") as f:
        bm25_retriever = pickle.load(f)

    # Dense retriever
    dense_retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 10})

    # Hybrid ensemble retriever
    hybrid_retriever = EnsembleRetriever(
        retrievers=[dense_retriever, bm25_retriever],
        weights=[0.6, 0.4]
    )

    print("Hybrid Retriever is ready.")

    def filtered_retriever(query: str, metadata_filter: Dict[str, Any] = None, top_k: int = 10) -> List[Document]:

        # 1. Retrieve documents using hybrid retriever
        results = hybrid_retriever.invoke(query)
        # for doc in results:
            # print("____________"*10)
            # print(f"Retrieved metadata{doc.metadata}, Retrieved content {doc.page_content} documents")
            # print("____________"*10)
        # 2. Apply metadata filter if provided
        if metadata_filter:
            print(f"Applying metadata filter inside retriever: {metadata_filter}")
            filtered = []
            for doc in results:
                print(f"Checking document with metadata: {doc.metadata}")
                match = True
                for k, values in metadata_filter.items():
                    if values:  # only check if list is non-empty
                        doc_value = doc.metadata.get(k)
                        if doc_value not in values:  # must match one of the allowed values
                            match = False
                            break
                if match:
                    filtered.append(doc)
            results = filtered
            print(f"Number of documents after filtering: {len(results)}")
        # Return top_k
        return results[:top_k]

    return filtered_retriever
