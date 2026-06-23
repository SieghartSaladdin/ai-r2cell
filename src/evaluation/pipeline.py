import os
import pandas as pd
from typing import Dict, Any
from ragas import evaluate
from .config import get_ragas_wrappers
from .metrics import get_configured_metrics
from datasets import Dataset

def run_evaluation(
    dataset: Dataset,
    provider: str = None,
    llm_model: str = None,
    embed_model: str = None,
) -> Dict[str, Any]:
    """
    Executes the Ragas evaluation pipeline on the provided dataset.
    Returns a dictionary with the raw results DataFrame and calculated aggregate scores.
    """
    # 1. Initialize wrapped models
    judge_llm, judge_embeddings = get_ragas_wrappers(provider, llm_model, embed_model)
    
    # 2. Configure metrics with these models
    metrics = get_configured_metrics(judge_llm, judge_embeddings)
    
    print("Starting evaluation execution. This might take a moment as the LLM-as-a-judge processes the dataset...")
    
    try:
        # Run evaluation
        result = evaluate(dataset=dataset, metrics=metrics)
        
        # Convert results to DataFrame
        df_results = result.to_pandas()
        
        # Safely calculate aggregate scores from the DataFrame
        scores = {}
        for col in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
            if col in df_results.columns:
                scores[col] = float(df_results[col].mean())
        
        return {
            "success": True,
            "results_df": df_results,
            "scores": scores,
            "error": None
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error during Ragas evaluation: {e}")
        return {
            "success": False,
            "results_df": pd.DataFrame(),
            "scores": {},
            "error": str(e)
        }

def generate_report(results: Dict[str, Any], output_path: str = "rag_eval_report.md") -> str:
    """
    Generates a scanned Markdown report from the evaluation results.
    """
    if not results.get("success"):
        return f"### RAG Evaluation Failed\nError: {results.get('error')}"
        
    scores = results["scores"]
    df = results["results_df"]
    
    report = []
    report.append("# RAG Evaluation Validation Report\n")
    report.append(f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Aggregate Scores table
    report.append("## Aggregate Metrics Summary\n")
    report.append("| Metric | Score | Validation Status |")
    report.append("| :--- | :--- | :--- |")
    
    weak_components = []
    
    # Thresholds: standard threshold is 0.8
    threshold = 0.8
    
    metrics_display = {
        "faithfulness": ("Faithfulness (No Hallucinations)", "Generator"),
        "answer_relevancy": ("Answer Relevance (Semantic Fit)", "Generator"),
        "context_precision": ("Context Precision (Chunk Ranking)", "Retriever"),
        "context_recall": ("Context Recall (Information Retrieval)", "Retriever")
    }
    
    for metric_key, val in scores.items():
        display_name, component = metrics_display.get(metric_key, (metric_key, "Unknown"))
        status = "PASSED ✅" if val >= threshold else "WARNING ⚠️"
        report.append(f"| {display_name} | {val:.4f} | {status} |")
        
        if val < threshold:
            weak_components.append({
                "metric": display_name,
                "score": val,
                "component": component,
                "issue": f"Low score on {display_name} indicates issues in the {component} module."
            })
            
    report.append("\n")
    
    # Diagnostics & Recommendations
    report.append("## Component Diagnostics & Recommendations\n")
    if not weak_components:
        report.append("All components passed validation threshold (> 0.80). The RAG pipeline is performing excellently! 🎉\n")
    else:
        report.append("The following weaknesses were detected in the pipeline:\n")
        for weak in weak_components:
            report.append(f"### Weakness in {weak['component']} ({weak['metric']}: {weak['score']:.4f})")
            if "Faithfulness" in weak["metric"]:
                report.append("- **Diagnosis**: The LLM is generating facts not grounded in the provided context (hallucinating).")
                report.append("- **Recommendation**: Lower the LLM temperature, tune system prompt constraints, or improve context chunking clarity.")
            elif "Answer Relevance" in weak["metric"]:
                report.append("- **Diagnosis**: The LLM response is generic or does not directly answer the user's query.")
                report.append("- **Recommendation**: Refine prompt instruction alignment or verify that the user's query intent is correctly captured.")
            elif "Precision" in weak["metric"]:
                report.append("- **Diagnosis**: The retriever is fetching noise. Relevant chunks are ranked too low.")
                report.append("- **Recommendation**: Optimize vector store retrieval parameters (tune top-k, use a cross-encoder reranker, or refine metadata filters).")
            elif "Recall" in weak["metric"]:
                report.append("- **Diagnosis**: The retriever failed to fetch all required facts to answer the ground truth.")
                report.append("- **Recommendation**: Increase chunk size, adjust overlap ratio, or check if the target knowledge document is fully ingested in ChromaDB.")
            report.append("\n")
            
    # Sample Test Cases Table
    report.append("## Detailed Evaluation Matrix\n")
    report.append("| Question | Answer | Faithfulness | Answer Relevance | Context Precision | Context Recall |")
    report.append("| :--- | :--- | :---: | :---: | :---: | :---: |")
    
    for _, row in df.iterrows():
        question = row.get("user_input") or row.get("question") or ""
        question_short = question[:40] + "..." if len(question) > 40 else question
        answer = row.get("response") or row.get("answer") or ""
        answer_short = answer[:40] + "..." if len(answer) > 40 else answer
        
        f_score = row.get("faithfulness", 0.0)
        ar_score = row.get("answer_relevancy", 0.0)
        cp_score = row.get("context_precision", 0.0)
        cr_score = row.get("context_recall", 0.0)
        
        report.append(f"| {question_short} | {answer_short} | {f_score:.3f} | {ar_score:.3f} | {cp_score:.3f} | {cr_score:.3f} |")
        
    report_content = "\n".join(report)
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"Validation report saved successfully to {output_path}")
    except Exception as e:
        print(f"Error saving markdown report: {e}")
        
    return report_content
