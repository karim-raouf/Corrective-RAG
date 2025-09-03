from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import Document
from typing import List
from models import llm


REFINEMENT_TEMPLATE = """
Your task is to extract the most relevant information from a given document based on a user's query.

Here is the user's query:
"{query}"

Here is the document:
"{document_text}"

Please extract *only* the sentences or paragraphs from the document that are relevant to answering the query.
If no part of the document is relevant to the query, return an empty string.
Do not add any of your own explanations, introductions, or conclusions. Just provide the extracted text.
"""


def refine_documents(query: str, documents: List[Document]) -> List[Document]:
    
    prompt = ChatPromptTemplate.from_template(REFINEMENT_TEMPLATE)
    refinement_chain = prompt | llm | StrOutputParser()

    refined_documents = []

    for i, doc in enumerate(documents):
        
        refined_text = refinement_chain.invoke({
            "query": query,
            "document_text": doc.page_content
        })

        if refined_text:
            # Create a new Document object with the refined text but keep the original metadata
            new_doc = Document(page_content=refined_text, metadata=doc.metadata)
            refined_documents.append(new_doc)
        else:
            print(f"  -> No relevant content found in document {i+1}. Discarding.")

    return refined_documents
