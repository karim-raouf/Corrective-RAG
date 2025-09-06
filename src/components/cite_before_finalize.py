from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from models import llm
from langchain.schema import Document 
from typing import List


class CiteChecker(BaseModel):
    valid_citations: str = Field(
        description="Answer with 'True' if the question is answered with citations from the documents, otherwise answer 'False'.",
    )

structured_llm_cite_checker = llm.with_structured_output(CiteChecker)

def check_for_sources(question: str , documents: List[Document], generated_answer: str) -> str:
    system = """
    You are an expert in evaluating if a given question has been answered with proper citations from the provided documents.
    Your task is to determine if the answer to the question is supported by citations from the documents.
    Question: {question}
    Documents: {documents}
    Generated Answer: {generated_answer}
    Answer with 'True' if the question is answered with citations from the documents, otherwise answer 'False'.
    """
    
    cite_checker_prompt = ChatPromptTemplate.from_template(system)
    cite_checker = cite_checker_prompt | structured_llm_cite_checker

    documnets_texts = "\n".join([doc.page_content for doc in documents])
    
    result = cite_checker.invoke({"question": question, "documents": documnets_texts, "generated_answer": generated_answer})
    
    return result.valid_citations