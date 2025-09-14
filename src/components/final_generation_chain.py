from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema import Document
from typing import List
from models import llm


ANSWER_TEMPLATE = """
You are a precise and comprehensive assistant for question-answering tasks in the automotive industry. 
Your role is to generate a complete and detailed answer to the user’s question using ONLY the information contained in the provided context. 

- IMPORTANT RULES:
1. Do NOT use outside knowledge. If the context does not contain the information, explicitly state: "The provided context does not contain information to answer this part of the question."
2. Use ALL relevant details from the context. Do not summarize or compress—include every important point directly supported by the context.
3. For EVERY statement, fact, or detail you include, you MUST provide its source. 
   - Sources are found in the metadata of each document. 
   - Cite them in the format: [Source: file_name, Page: page_number].
4. If multiple documents give information, include ALL of them. Then at the end in a paragraph merge the information into a high-level summary.
5. Structure your answer clearly. If multiple aspects of the answer exist, use sections or bullet points.

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
        title = (doc.metadata.get('title') or "Unknown Title").split("\\")[-1]
        subtitle = (doc.metadata.get('subtitle') or "Unknown subtitle").split("\\")[-1]
        sub_subtitle = (doc.metadata.get('Sub_subtitle') or "Unknown Sub_subtitle").split("\\")[-1]
        page = doc.metadata.get('page', 'N/A')
        
        # Format the string for each document
        doc_string = f"--- Document {i+1} (title: {title}, subtitle: {subtitle}, sub_subtitle: {sub_subtitle}, page: {page}) ---\n{doc.page_content}"

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