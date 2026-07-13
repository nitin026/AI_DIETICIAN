import sys
import os
from backend.rag.retriever import retrieve

def test_search():
    queries = [
        "BMR equation for Indians",
        "energy requirement Indian adults",
        "Recommended Dietary Allowances BMR",
        "activity multiplier sedentary moderate heavy"
    ]
    for q in queries:
        print("="*60)
        print(f"QUERY: {q}")
        print("="*60)
        results = retrieve(q, k=3)
        for i, res in enumerate(results, 1):
            print(f"--- Chunk {i} ---")
            print(res)
            print()

if __name__ == "__main__":
    test_search()
