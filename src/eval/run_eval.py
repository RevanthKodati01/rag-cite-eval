import json
import re
from typing import List, Dict

from src.rag.qa import retrieve, answer_with_citations

def extract_citation_numbers(text: str) -> List[int]:
    nums = re.findall(r"\[(\d+)\]", text)
    return sorted(set(int(n) for n in nums))

def keyword_coverage(answer: str, keywords: List[str]) -> float:
    a = answer.lower()
    if not keywords:
        return 1.0
    hit = sum(1 for k in keywords if k.lower() in a)
    return hit / len(keywords)

def citation_keyword_coverage(hits: List[Dict], cited: List[int], keywords: List[str]) -> float:
    if not cited or not keywords:
        return 0.0 if keywords else 1.0

    cited_text = " ".join(
        hits[i - 1]["text"].lower()
        for i in cited
        if 1 <= i <= len(hits)
    )
    hit = sum(1 for k in keywords if k.lower() in cited_text)
    return hit / len(keywords)

def unsupported_claim_check(answer: str, hits: List[Dict], cited: List[int]) -> float:
    """
    Returns 1.0 if answer seems supported, 0.0 if it contains likely unsupported expansions like 'stands for'.
    Simple heuristic for MVP.
    """
    ans = answer.lower()
    if "stands for" not in ans:
        return 1.0

    cited_text = " ".join(
        hits[i - 1]["text"].lower()
        for i in cited
        if 1 <= i <= len(hits)
    )
    # if answer tries to define acronym, require that cited text also contains "stands for"
    return 1.0 if "stands for" in cited_text else 0.0

def main():
    total = 0
    ans_kw_sum = 0.0
    cite_kw_sum = 0.0

    with open("eval_set.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            ex = json.loads(line)
            q = ex["question"]
            keywords = ex.get("must_include", [])
            k = ex.get("k", 4)

            hits = retrieve(q, k=k)
            ans = answer_with_citations(q, hits)
            cited = extract_citation_numbers(ans)

            ans_kw = keyword_coverage(ans, keywords)
            cite_kw = citation_keyword_coverage(hits, cited, keywords)

            total += 1
            ans_kw_sum += ans_kw
            cite_kw_sum += cite_kw

            print("\n==============================")
            print("Q:", q)
            print("\nAnswer:\n", ans)
            print("\nCited chunks:", cited)
            print(f"Keyword coverage in answer: {ans_kw:.2f}")
            print(f"Keyword coverage in cited sources: {cite_kw:.2f}")
    support = unsupported_claim_check(ans, hits, cited)
    print(f"Support check (heuristic): {support:.2f}")

    print("\n========== SUMMARY ==========")
    print("Examples:", total)
    if total:
        print(f"Avg keyword coverage (answer): {ans_kw_sum/total:.2f}")
        print(f"Avg keyword coverage (citations): {cite_kw_sum/total:.2f}")

if __name__ == "__main__":
    main()
