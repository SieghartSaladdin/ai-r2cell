import json
import os
import pandas as pd
from datasets import Dataset
from typing import List, Dict, Any

QUESTIONS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions.json")


def build_rag_dataset(questions: List[Dict[str, str]]) -> Dataset:
    """
    Builds a Ragas dataset by running the real system on each question:
    - contexts: the chunks the knowledge-base tool would hand to the LLM (same relevance threshold),
    - answer: the final reply of the compiled main agent graph.
    `questions` items need `question` and `ground_truth`. Temporary eval threads are removed afterwards.
    """
    # Imported lazily: loading the graph opens the checkpoint DB and the vector store.
    from langchain_core.messages import HumanMessage
    from src.agents.main_agent import main_graph
    from src.agents.main_agent.graph import db_conn
    from src.core.vectorstore import get_vector_store
    from src.tools.search import MIN_RELEVANCE, SEARCH_K

    store = get_vector_store()
    data = {"question": [], "contexts": [], "answer": [], "ground_truth": []}
    thread_ids = []
    try:
        for i, item in enumerate(questions):
            question = item["question"]
            scored = store.similarity_search_with_relevance_scores(question, k=SEARCH_K)
            contexts = [doc.page_content for doc, score in scored if score >= MIN_RELEVANCE]

            thread_id = f"test_eval_{i}"
            thread_ids.append(thread_id)
            state = main_graph.invoke(
                {"messages": [HumanMessage(content=question)]},
                config={"configurable": {"thread_id": thread_id}, "recursion_limit": 12},
            )
            data["question"].append(question)
            data["contexts"].append(contexts)
            data["answer"].append(state["messages"][-1].content)
            data["ground_truth"].append(item["ground_truth"])
    finally:
        for thread_id in thread_ids:
            db_conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
            db_conn.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
        db_conn.commit()
    return Dataset.from_dict(data)


def get_fallback_dataset() -> Dataset:
    """
    Default dataset: the R2Cell business questions in questions.json, answered live by the system.
    """
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        return build_rag_dataset(json.load(f))


def load_evaluation_dataset(path: str = None, df: pd.DataFrame = None) -> Dataset:
    """
    Loads an evaluation dataset from a JSON, CSV, or DataFrame, ensuring Ragas schema compliance.
    """
    if df is not None:
        raw_data = df.to_dict(orient="list")
    elif path and path.endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            if isinstance(raw_data, list):
                df_temp = pd.DataFrame(raw_data)
                raw_data = df_temp.to_dict(orient="list")
    elif path and path.endswith(".csv"):
        df_temp = pd.read_csv(path)
        raw_data = df_temp.to_dict(orient="list")
    else:
        return get_fallback_dataset()
        
    mapping = {
        "question": ["question", "query", "input", "prompt"],
        "contexts": ["contexts", "context", "retrieved_context", "chunks"],
        "answer": ["answer", "response", "prediction", "output"],
        "ground_truth": ["ground_truth", "ground_truths", "target", "reference"]
    }
    
    standardized = {}
    for standard_col, synonyms in mapping.items():
        found = False
        for syn in synonyms:
            if syn in raw_data:
                standardized[standard_col] = raw_data[syn]
                found = True
                break
        if not found:
            num_samples = len(standardized.get("question", []))
            if standard_col == "contexts":
                standardized["contexts"] = [[] for _ in range(num_samples)]
            elif standard_col == "ground_truth":
                standardized["ground_truth"] = ["" for _ in range(num_samples)]
            else:
                raise ValueError(f"Required Ragas column equivalent for '{standard_col}' not found in dataset keys: {list(raw_data.keys())}")
                
    # Normalize contexts to List[List[str]]
    for i, ctx in enumerate(standardized["contexts"]):
        if isinstance(ctx, str):
            standardized["contexts"][i] = [ctx]
        elif not isinstance(ctx, list):
            standardized["contexts"][i] = [str(ctx)] if ctx else []
            
    # Normalize ground_truth to list of strings
    for i, gt in enumerate(standardized["ground_truth"]):
        if isinstance(gt, list):
            standardized["ground_truth"][i] = str(gt[0]) if gt else ""
        else:
            standardized["ground_truth"][i] = str(gt)
            
    return Dataset.from_dict(standardized)
