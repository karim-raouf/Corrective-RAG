from components.web_search import tavily_search
from typing import List,Annotated
from typing_extensions import TypedDict
import pickle
from components.database_and_retriever import vectorstore_processing_and_retriever
from components.retrieval_evaluator import evaluate_retrieved_docs
from components.documents_refinement import refine_documents
from components.final_generation_chain import generation_chain
from langchain.schema import Document
from operator import add
from langgraph.types import Command
from langgraph.graph import StateGraph, END, START

class CRAGState(TypedDict):
    
    question: str
    final_output: str
    web_search: bool
    documents: List[Document]
    refined_documents: Annotated[List[Document], add]
    scores: List[str]
    
    

def retrieve(state: CRAGState) -> CRAGState:
    question = state["question"]
    # Retrieval
    retriever = vectorstore_processing_and_retriever()
    documents = retriever(question)
    return {"documents": documents}


def evaluate(state: CRAGState) -> CRAGState:
    question = state["question"]
    documents = state["documents"]
    scores = evaluate_retrieved_docs(question, documents)
    return {"scores": scores}


def web_search(state: CRAGState) -> CRAGState:
    print("---NODE: WEB SEARCH---")
    question = state["question"]
    search_output = tavily_search.invoke(question)
    search_results = [
        Document(page_content=result['content'], metadata={"source": result['url']})
        for result in search_output['results']
    ]
    print(search_results)
    return {"refined_documents": search_results}
    
    
def start_refine_documents(state: CRAGState) -> CRAGState:
    question = state["question"]
    documents = state["documents"]
    refined_docs = refine_documents(question, documents)
    return {"refined_documents": refined_docs}


def final_output(state: CRAGState) -> CRAGState:
    question = state["question"]
    refined_documents = state["refined_documents"]
    # print(refined_documents)
    
    generation_output = generation_chain.invoke({
        question: question,
        "context": refined_documents
    })

    return {"final_output": generation_output}
    

def post_evaluation(state: CRAGState) -> CRAGState:
    scores = state["scores"]
    LOW_THRESHOLD = 6
    HIGH_THRESHOLD = 9
    # Decide if web search is needed based on scores
    if all(int(score) < LOW_THRESHOLD for score in scores):
        return Command(
            update={"web_search": True, "documents": []},
            goto="Web_search"
        )
    elif any(int(score) >= HIGH_THRESHOLD for score in scores):
        return Command(
            update={"web_search": False},
            goto="Refine"
        )
    else:
        return Command(
            update={"web_search": True},
            goto=["Web_search", "Refine"]
        )
    

def join(state: CRAGState) -> CRAGState:
    print("---NODE: JOIN---")
    return {}



workflow = StateGraph(CRAGState)

workflow.add_node("Retrieve", retrieve)
workflow.add_node("Evaluate", evaluate)
workflow.add_node("Web_search", web_search)
workflow.add_node("Refine", start_refine_documents)
workflow.add_node("Generate", final_output)
workflow.add_node("Decide_next_step", post_evaluation)
workflow.add_node("Join", join)



workflow.add_edge(START, "Retrieve")
workflow.add_edge("Retrieve", "Evaluate")
workflow.add_edge("Evaluate", "Decide_next_step")

workflow.add_edge("Web_search", "Join")
workflow.add_edge("Refine", "Join")

workflow.add_edge("Join", "Generate")
workflow.add_edge("Generate", END)

# 5. Compile the Graph
graph = workflow.compile()
