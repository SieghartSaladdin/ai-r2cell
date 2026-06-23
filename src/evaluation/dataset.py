import json
import pandas as pd
from datasets import Dataset
from typing import List, Dict, Any

def get_fallback_dataset() -> Dataset:
    """
    Returns a Ragas-compliant Hugging Face Dataset containing sample RAG outputs 
    for validation.
    """
    data = {
        "question": [
            "What is a R2CELL bot signature?",
            "How does ChromaDB persist vector embeddings?",
            "What is the LangGraph checkpointer SQLite database used for?"
        ],
        "contexts": [
            [
                "R2CELL uses bot signatures to uniquely identify cell signatures and conversation states on the WhatsApp network. This allows multi-user chat routing."
            ],
            [
                "ChromaDB is a vector database that persists documents and their embeddings on disk. By default, it stores index structures in a persistently mapped DB folder."
            ],
            [
                "LangGraph checkpointers act as persistence layers. The SQLite checkpointer saves conversational state threads, messages, and variables, allowing bots to resume history."
            ]
        ],
        "answer": [
            "A R2CELL bot signature is a unique identifier used to manage cell signatures and user session states on WhatsApp for multi-user chat routing.",
            "ChromaDB persists vector embeddings on disk. It saves both the indexed document chunks and their generated vector mappings inside a persistent DB directory.",
            "The LangGraph SQLite checkpointer database is used to store active session history, message logs, and state variables across conversations."
        ],
        "ground_truth": [
            "R2CELL bot signatures identify cell signatures and user states on WhatsApp to perform multi-user chat routing.",
            "ChromaDB persists documents and embeddings on disk in a persistent DB folder.",
            "LangGraph SQLite checkpointer saves thread message history and state variables so the chatbot can resume conversations."
        ]
    }
    return Dataset.from_dict(data)

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
