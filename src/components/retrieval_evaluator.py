from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from models import llm
from langchain.schema import Document 
from typing import List

class RetrievalEvaluator(BaseModel):
    binary_score: str = Field(
        description="on a scale of 0 to 10, where 10 means the document is very relevant to the question, and 1 means it is not relevant at all.",
    )


def evaluate_retrieved_docs(query: str, documents: List[Document]) -> List[str]:
    scores = []
    structured_llm_evaluator = llm.with_structured_output(RetrievalEvaluator)

    system = """You are a meticulous evaluator tasked with scoring the relevance of retrieved documents to a user's query. Your goal is to provide a precise relevance score on a scale of 1 to 10.

            ### Instructions:
            1.  **Analyze the Query:** First, carefully analyze the user's query to understand the core question, its specific intent, and the type of information required.

            2.  **Evaluate Each Document:** For each document provided, perform the following two steps:
                - **A. Reasoning:** Briefly write down your step-by-step reasoning for why the document is or is not relevant. Consider if it provides a direct answer, useful context, tangential information, or is completely off-topic.
                - **B. Scoring:** After your reasoning, assign a single numerical score from 1 to 10 based on the detailed rubric below.

            ### Scoring Rubric:
            - **Highly Relevant (Score: 9-10):** The document contains a direct, precise, and comprehensive answer to the user's query. It is a primary source of information that requires little to no inference to be useful.
            - **Relevant & Useful (Score: 7-8):** The document contains substantial, direct information that answers a significant part of the query. It is a very helpful source but might not cover all aspects of the question.
            - **Somewhat Related / Background (Score: 5-6):** The document provides general background information or context around the main subject of the query but does not contain a specific answer to the question itself.
            - **Tangential (Score: 3-4):** The document mentions keywords or concepts from the query but in a different, unhelpful context. The information does not contribute to answering the question.
            - **Irrelevant (Score: 1-2):** The document is on a completely different topic and contains no information related to the query.

            ### Output Format:
            For each document, provide your reasoning first, then the score on a new line.
            ---
            Query: {query}
            ---
            Document: {document}
            ---
            Reasoning:
            <Your reasoning here>
            Score: <Your score here>
            """
    
    retrieval_evaluator_prompt = ChatPromptTemplate.from_template(system)
    retrieval_grader = retrieval_evaluator_prompt | structured_llm_evaluator
    for doc in documents:
        result = retrieval_grader.invoke({"document": doc.page_content, "query": query})
        # print(f"Document relevance: {result.binary_score}")
        scores.append(result.binary_score)
    
    return scores
        