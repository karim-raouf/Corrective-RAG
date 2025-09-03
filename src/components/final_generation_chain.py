from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema import Document
from typing import List
from models import llm


ANSWER_TEMPLATE = """
You are a helpful assistant for question-answering tasks. Your task is to synthesize an answer to the user's question based exclusively on the context provided.
Do not use any information outside of the provided context.
The context contains documents with their sources. 
For every piece of information you use, you MUST cite the source. The source is found in the metadata of each document.
Cite the source using the format [Source: file_name, Page: page_number].
If the context does not contain the answer to the question, you must state that you cannot answer the question with the provided information.
---
CONTEXT:
{context}
---
QUESTION:
{question}
---
ANSWER:
"""

def _format_docs_with_sources(docs: List[Document]) -> str:
    if not docs:
        return "No context provided."

    formatted_strings = []
    for i, doc in enumerate(docs):
        source = doc.metadata.get('source', 'Unknown Source').split("\\")[-1]
        page = doc.metadata.get('page', 'N/A')
        
        # Format the string for each document
        doc_string = f"--- Document {i+1} (Source: {source}, Page: {page}) ---\n{doc.page_content}"
        formatted_strings.append(doc_string)
        
    return "\n\n".join(formatted_strings)


def create_rag_chain():
    
    prompt = ChatPromptTemplate.from_template(ANSWER_TEMPLATE)

    final_chain = (
        {
            "context": lambda x: _format_docs_with_sources(x["context"]),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return final_chain


generation_chain = create_rag_chain()