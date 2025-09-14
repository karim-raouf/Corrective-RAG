from langchain_community.document_loaders import PyPDFLoader
from langchain_docling import DoclingLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import os
from typing import List

def load_documents(directory_path: str) -> list[Document]:
    print(f"Loading documents...")
    all_documents = []

    if not os.path.isdir(directory_path):
        print(f"Error: Directory not found at '{directory_path}'")
        return []

    for filename in os.listdir(directory_path):
        if filename.lower().endswith(".pdf"):
            file_path = os.path.join(directory_path, filename)
            try:
                # loader = PyPDFLoader(file_path)
                # documents = loader.load()
                
                # - Trying docling loader for better performance by making documnets structured
                loader = DoclingLoader(file_path, output_format="markdown")  
                documents = loader.load()
                all_documents.extend(documents)
                print(f"Successfully loaded {len(documents)} pages from {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")

    return all_documents


def split_documents(documents: list[Document], chunk_size: int=1500, chunk_overlap: int=150) -> list[Document]:
    print(f"Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap, 
        length_function=len
    )
    docs = text_splitter.split_documents(documents)
    return docs
    