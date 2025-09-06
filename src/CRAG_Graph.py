from components.web_search import tavily_search
from typing import List,Annotated
from typing_extensions import TypedDict
import pickle
from components.database_and_retriever import vectorstore_processing_and_retriever
from components.retrieval_evaluator import evaluate_retrieved_docs
from components.documents_refinement import refine_documents
from components.final_generation_chain import generation_chain
from components.cite_before_finalize import check_for_sources
from components.query_decomposition import decompose_query
from langchain.schema import Document
from operator import add
from langgraph.types import Command
from langgraph.graph import StateGraph, END, START

class CRAGState(TypedDict):
    
    question: str
    decomposed_queries: List[str]
    final_output: str
    web_search: bool
    documents: List[Document]
    refined_documents: Annotated[List[Document], add]
    scores: List[str]
    
    
def query_decomposer(state: CRAGState) -> CRAGState:
    question = state["question"]
    decomposed_queries = decompose_query(question)
    return {"decomposed_queries": decomposed_queries}

def retrieve(state: CRAGState) -> CRAGState:
    decomposed_questions = state["decomposed_queries"]
    retriever = vectorstore_processing_and_retriever()
    
    print("Retrieving Documents...")
    all_documents = []
    for question in decomposed_questions:
        result = retriever(question)
        all_documents.extend(result)
    
    return {"documents": all_documents}


def evaluate(state: CRAGState) -> CRAGState:
    print("Starting Documnets Evaluation...")
    question = state["question"]
    documents = state["documents"]
    scores = evaluate_retrieved_docs(question, documents)
    return {"scores": scores}


def web_search(state: CRAGState) -> CRAGState:
    print("Searching the Web...")
    decomposed_questions = state["decomposed_queries"]
    all_search_results = []
    for question in decomposed_questions:    
        search_output = tavily_search.invoke(question)
        search_results = [
            Document(page_content=result['content'], metadata={"source": result['url']})
            for result in search_output['results']
        ]
        all_search_results.extend(search_results)
    # print(all_search_results)
    return {"refined_documents": all_search_results}
    
    
def start_refine_documents(state: CRAGState) -> CRAGState:
    print("Refining Documents...")
    question = state["question"]
    documents = state["documents"]
    refined_docs = refine_documents(question, documents)
    return {"refined_documents": refined_docs}


    
    

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

def final_output(state: CRAGState) -> CRAGState:
    print("Generating Final Output...")
    question = state["question"]
    refined_documents = state["refined_documents"]
    # print(refined_documents)
    
    generation_output = generation_chain.invoke({
        question: question,
        "context": refined_documents
    })

    return {"final_output": generation_output}    


def cite_sources_checker(state: CRAGState) -> CRAGState:
    print("Checking Citations...")
    question = state["question"]
    documents = state["refined_documents"]
    generated_answer = state["final_output"]
    valid_citations = check_for_sources(question, documents, generated_answer)
    
    if valid_citations == "False":
        print("Citations are missing or invalid.Retrying again...")
        improvment_question_part = (
            "\nPlease answer the question with proper citations from the provided documents only."
            "If the documents do not contain the answer,"
            "respond with 'The provided documents do not contain the answer to the question.'"
        )
        new_question = question + improvment_question_part
        return Command(
            update={"question": new_question},
            goto=["Generate"]
        )
    else:
        print("Citations are valid.")
        return Command(
            goto=END
        )


def join(state: CRAGState) -> CRAGState:
    print("Waiting for all previous nodes to complete...")
    return {}



workflow = StateGraph(CRAGState)

workflow.add_node("Retrieve", retrieve)
workflow.add_node("Query_decomposition", query_decomposer)
workflow.add_node("Evaluate", evaluate)
workflow.add_node("Web_search", web_search)
workflow.add_node("Refine", start_refine_documents)
workflow.add_node("Generate", final_output)
workflow.add_node("Decide_next_step", post_evaluation)
workflow.add_node("Cite_checker", cite_sources_checker)
workflow.add_node("Join", join)



workflow.add_edge(START, "Query_decomposition")
workflow.add_edge("Query_decomposition", "Retrieve")
workflow.add_edge("Retrieve", "Evaluate")
workflow.add_edge("Evaluate", "Decide_next_step")

workflow.add_edge("Web_search", "Join")
workflow.add_edge("Refine", "Join")

workflow.add_edge("Join", "Generate")
workflow.add_edge("Generate", "Cite_checker")


# 5. Compile the Graph
graph = workflow.compile()
