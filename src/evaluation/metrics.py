from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

def get_configured_metrics(judge_llm, judge_embeddings) -> list:
    """
    Binds the configured judge LLM and embeddings to each of the evaluation metrics
    and returns the list of active metrics.
    """
    # Bind LLM judge and embeddings to Ragas metrics
    faithfulness.llm = judge_llm
    
    answer_relevancy.llm = judge_llm
    answer_relevancy.embeddings = judge_embeddings
    
    context_precision.llm = judge_llm
    
    context_recall.llm = judge_llm
    
    return [faithfulness, answer_relevancy, context_precision, context_recall]
