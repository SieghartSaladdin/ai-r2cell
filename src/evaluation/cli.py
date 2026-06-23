import argparse
import sys
import os

# Ensure the root of the project is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.evaluation.dataset import load_evaluation_dataset
from src.evaluation.pipeline import run_evaluation, generate_report

def main():
    parser = argparse.ArgumentParser(description="Automated Ragas RAG Validation Pipeline")
    parser.add_argument("--dataset-path", type=str, default=None, help="Path to evaluation JSON/CSV file")
    parser.add_argument("--provider", type=str, default=None, help="LLM provider: 'ollama' or 'openai'")
    parser.add_argument("--llm-model", type=str, default=None, help="Model name for LLM judge")
    parser.add_argument("--embed-model", type=str, default=None, help="Model name for embeddings client")
    parser.add_argument("--output-report", type=str, default="rag_eval_report.md", help="Path to write markdown validation report")
    parser.add_argument("--sample-limit", type=int, default=None, help="Maximum number of test cases to evaluate")
    
    args = parser.parse_args()
    
    print("--------------------------------------------------")
    print(" R2CELL RAG VALIDATION PIPELINE (RAGAS FRAMEWORK)")
    print("--------------------------------------------------")
    
    # 1. Load dataset
    try:
        dataset = load_evaluation_dataset(args.dataset_path)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        sys.exit(1)
        
    # Apply sample limit if specified
    if args.sample_limit is not None and args.sample_limit > 0:
        dataset = dataset.select(range(min(args.sample_limit, len(dataset))))
        
    print(f"Loaded evaluation dataset containing {len(dataset)} test cases.")
    
    # 2. Run evaluation pipeline
    results = run_evaluation(
        dataset=dataset,
        provider=args.provider,
        llm_model=args.llm_model,
        embed_model=args.embed_model
    )
    
    # 3. Generate report
    if results.get("success"):
        report = generate_report(results, output_path=args.output_report)
        print("\nEvaluation successfully completed! Final metrics Summary:")
        for metric, score in results["scores"].items():
            print(f"  - {metric}: {score:.4f}")
        print(f"Detailed diagnostics compiled and saved in: {args.output_report}")
    else:
        print(f"Evaluation pipeline encountered a failure: {results.get('error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
