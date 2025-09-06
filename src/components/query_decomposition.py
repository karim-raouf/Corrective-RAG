from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from models import llm
from langchain.schema import Document 
from typing import List

class QueryDecomposer(BaseModel):
    decomposed_queries: List[str] = Field(
        description="A list of sub-questions that together answer the main question.",
    )
    
system = """
        You are an expert query decomposer. Your task is to break down complex questions into simpler,
        more manageable sub-questions that can be answered individually.
        Each sub-question should be clear, concise, and directly related to the main question.
        
        Question: {question}
        """

def decompose_query(question: str) -> List[str]:
    structured_llm_decomposer = llm.with_structured_output(QueryDecomposer)
    decomposer_prompt = ChatPromptTemplate.from_template(system)
    decomposer = decomposer_prompt | structured_llm_decomposer
    print("Decomposing Query...")
    result = decomposer.invoke({"question": question})
    questions = result.decomposed_queries
    return questions