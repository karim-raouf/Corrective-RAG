from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import os
from typing import List

def load_documents(directory_path: str) -> list[Document]:
<<<<<<< HEAD
    print(f"Loading documents...")
=======
    
>>>>>>> c9ad0afff5ffd4a929d3790d8f573263f0048b3b
    all_documents = []

    if not os.path.isdir(directory_path):
        print(f"Error: Directory not found at '{directory_path}'")
        return []

    for filename in os.listdir(directory_path):
        if filename.lower().endswith(".pdf"):
            file_path = os.path.join(directory_path, filename)
            try:
                loader = PyPDFLoader(file_path)
                documents = loader.load()
                all_documents.extend(documents)
                print(f"Successfully loaded {len(documents)} pages from {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")

    return all_documents


<<<<<<< HEAD
def split_documents(documents: list[Document], chunk_size: int=1000, chunk_overlap: int=100) -> list[Document]:
    print(f"Splitting documents into chunks...")
=======
def split_documents(documents: list[Document], chunk_size: int=500, chunk_overlap: int=50) -> list[Document]:
>>>>>>> c9ad0afff5ffd4a929d3790d8f573263f0048b3b
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap, 
        length_function=len
    )
    docs = text_splitter.split_documents(documents)
    return docs
    