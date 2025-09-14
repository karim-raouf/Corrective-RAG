from langchain_chroma import Chroma
from models import embeddings
from langchain.schema import Document
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers.document_compressors.base import DocumentCompressorPipeline
# from langchain.retrievers.merger_retriever import MergerRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain_core.documents import Document
from langchain.retrievers import EnsembleRetriever, MergerRetriever
import os
import pickle
from .loading_chunking_MD import parse_chunk_markdown_files
from typing import List, Dict, Any
from langchain_core.retrievers import BaseRetriever
import re


def build_retriever_components(
    ASPICE_PATH: str = "D:/Kinnovia documents/Code Implementations/CRAG-implementation/Corrective-RAG/src/documents/Automotive_SPICE_PAM_31_EN_LlamaIndex.md",
    AUTOSAR_PATH: str = "D:/Kinnovia documents/Code Implementations/CRAG-implementation/Corrective-RAG/src/documents/AUTOSAR_SWS_ECUStateManager-LlamaIndex.md",
    persist_dir: str = "D:/Kinnovia documents/Code Implementations/CRAG-implementation/Corrective-RAG/src/databases/"
):
    
    os.makedirs(persist_dir, exist_ok=True)

    
    if os.path.exists(persist_dir) and os.listdir(persist_dir):
        vector_store = Chroma(
            embedding_function=embeddings,
            persist_directory=persist_dir
        )
    else:
        
        chunks = parse_chunk_markdown_files([ASPICE_PATH,AUTOSAR_PATH])

       
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

    
    with open(os.path.join(persist_dir, "bm25.pkl"), "rb") as f:
        bm25_retriever = pickle.load(f)
    
    print("Retriever components are ready.")
    return vector_store, bm25_retriever

# --- Main Application Logic ---

vector_store, bm25_retriever = build_retriever_components()


def _create_chroma_filter(metadata_filter: Dict[str, Any]) -> Dict[str, Any]:
    if metadata_filter is None:
        return metadata_filter

    conditions = []
    for key, values in metadata_filter.items():
        if values:  # Ensure not empty
            # Lowercase all string values
            lowered_values = [v.lower() for v in values if isinstance(v, str)]
            
            if len(lowered_values) == 1:
                # Single value -> direct match
                conditions.append({key: {"$eq": lowered_values[0]}})
            else:
                # Multiple values -> OR across them
                or_conditions = [{key: {"$eq": val}} for val in lowered_values]
                conditions.append({"$or": or_conditions})

    # If only one condition, unwrap it
    if len(conditions) == 1:
        return conditions[0]

    return {"$and": conditions}



def filtered_hybrid_search(query: str, metadata_filter: Dict[str, Any] = None, top_k: int = 10) -> List[Document]:
   

    chroma_filter = _create_chroma_filter(metadata_filter)
    
    # print(f"Chroma filter applied: {chroma_filter}")
    # print("Performing pre-filtered dense search...")
    dense_retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={'k': top_k, 'filter': chroma_filter}
    )
    dense_results = dense_retriever.invoke(query)
    print(f"Found {len(dense_results)} docs from dense search.")

    # print("Performing sparse search and post-filtering...")
    bm25_results_unfiltered = bm25_retriever.invoke(query)
    # print(f"Found {len(bm25_results_unfiltered)} docs from sparse search before filtering.")
    
    
    # --- DEBUGGING BLOCK ---
    # print("\n--- Inspecting Metadata of Unfiltered BM25 Results ---")
    # for i, doc in enumerate(bm25_results_unfiltered):
    #     print(f"Doc {i+1} Metadata: {doc.metadata}")
    # print("-----------------------------------------------------\n")
    # --- END DEBUGGING BLOCK ---
    
    bm25_results_filtered = []
    if metadata_filter:
            for doc in bm25_results_unfiltered:
                # print(f"Checking document with metadata: {doc.metadata}")
                # print("second doc")
                match = True
                for k, values in metadata_filter.items():
                    if values:  
                        doc_value = doc.metadata.get(k)
                        # print("_________"*10)
                        # print("in document:", doc_value)
                        # print("in metadata:" ,[value.lower() for value in values])
                        # print("_________"*10)
                        if doc_value not in [value.lower() for value in values]:
                            match = False
                            break
                if match:
                    bm25_results_filtered.append(doc)
    else:

        bm25_results_filtered = bm25_results_unfiltered
        
    print(f"Found {len(bm25_results_filtered)} docs from sparse search after filtering.")

    if not dense_results and not bm25_results_filtered:
        return []

    # Create dummy retrievers that just return the pre-filtered results
    class StaticRetriever(BaseRetriever):
        """A dummy retriever that just returns a static list of documents."""
        docs: List[Document]

        def _get_relevant_documents(self, query: str) -> List[Document]:
            return self.docs

    merge_retriever = MergerRetriever(
        retrievers=[StaticRetriever(docs=dense_results), StaticRetriever(docs=bm25_results_filtered)],
        # weights=[0.6, 0.4] 
    )

    final_results = merge_retriever.invoke(query)
    
    return final_results[:top_k]
