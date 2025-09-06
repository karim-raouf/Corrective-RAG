from langchain_chroma import Chroma
from models import embeddings
from langchain.schema import Document 
from typing import List
from langchain.schema.vectorstore import VectorStoreRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from .documents_prepropcessing import split_documents, load_documents
import os
import pickle



def vectorstore_processing_and_retriever() -> Chroma:
    
    persist_dir = "src/databases/"
    
    if os.path.exists(persist_dir) and os.listdir(persist_dir):
        
        vector_store = Chroma(
            embedding_function=embeddings,
            persist_directory=persist_dir
        )
    else:
        docs = load_documents("D:/Kinnovia documents/Code Implementations/CRAG/Corrective-RAG/src/documents")
        chunks = split_documents(docs)
        
        bm25_retriever = BM25Retriever.from_documents(docs)
        bm25_retriever.k = 5
        
        with open("src/databases/bm25.pkl", "wb") as f:
            pickle.dump(bm25_retriever, f)
<<<<<<< HEAD
        print(f"Creating vector store...")
=======
        
>>>>>>> c9ad0afff5ffd4a929d3790d8f573263f0048b3b
        vector_store = Chroma.from_documents(
            documents=chunks, 
            embedding=embeddings,
            persist_directory=persist_dir
        )
<<<<<<< HEAD
=======
        # vector_store.persist()
>>>>>>> c9ad0afff5ffd4a929d3790d8f573263f0048b3b
        
    with open("src/databases/bm25.pkl", "rb") as f:
        bm25_retriever = pickle.load(f)
    dense_retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k":5})
    
    hybrid_retriever = EnsembleRetriever(
    retrievers=[dense_retriever, bm25_retriever],
<<<<<<< HEAD
    weights=[0.6, 0.4],  # tune weights based on testing
    )
    print("Hybdrid Retriever is ready.")
=======
    weights=[0.5, 0.5],  # tune weights based on testing
    )
    
>>>>>>> c9ad0afff5ffd4a929d3790d8f573263f0048b3b
    def limited_retriever(query):
        results = hybrid_retriever.invoke(query)
        return results[:5]   # only keep top 5 after re-ranking

    return limited_retriever



