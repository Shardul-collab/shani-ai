from collections import defaultdict


class KnowledgeCompressor:

    def __init__(self, max_clusters=12, max_evidence_per_cluster=12):
        self.max_clusters = max_clusters
        self.max_evidence_per_cluster = max_evidence_per_cluster

    def build_clusters(self, knowledge_rows, citation_map, paper_lookup):

        clusters = defaultdict(list)

        for r in knowledge_rows:

            category = r["category"]
            value = r["value"]
            sentence = r["sentence"]
            paper_id = r["paper_id"]

            subject = r["subject"] if "subject" in r.keys() else None
            relation = r["relation"] if "relation" in r.keys() else None
            obj = r["object"] if "object" in r.keys() else None

            if not sentence:
                continue

            citation_num = citation_map.get(paper_id, "?")

            if subject and relation and obj:
                key = f"{subject} → {relation} → {obj}"
            else:
                key = f"{value}"

            clusters[key].append({
                "sentence": sentence.strip(),
                "citation": f"{citation_num}",
                "paper_id": paper_id
            })

        filtered_clusters = {}

        for key, items in clusters.items():

            seen_papers = set()
            unique_items = []

            for item in items:
                if item["paper_id"] in seen_papers:
                    continue
                seen_papers.add(item["paper_id"])
                unique_items.append(item)

            filtered_clusters[key] = unique_items[:self.max_evidence_per_cluster]

        return list(filtered_clusters.items())[:self.max_clusters]

    def format_cluster(self, key, items):

        lines = [
            "Scientific Claim:",
            f"{key}",
            "",
            "Supporting Evidence:"
        ]

        for item in items:
            lines.append(f"[{item['citation']}] {item['sentence']}")

        return "\n".join(lines)

    def summarize_cluster(self, cluster_text, llm_service):

        prompt = f"""
You are analyzing scientific literature evidence.

Your task:
Summarize the findings across multiple studies.

STRICT CITATION RULES:
- ONLY use numbers inside square brackets like [1], [2]
- DO NOT generate any other format
- DO NOT use letters like [a], [b]
- DO NOT use placeholders like [X]
- DO NOT create new citations
- ONLY reuse citations exactly as provided

STRICT CONTENT RULES:
- Use ONLY the provided sentences
- Do NOT invent any new information
- Combine studies into coherent insights

Write 4–6 sentences.

Data:
{cluster_text}
"""

        return llm_service.generate_text(prompt)

    def build_cluster_summaries(self, knowledge_rows, citation_map, paper_lookup, llm_service):

        cluster_items = self.build_clusters(
            knowledge_rows,
            citation_map,
            paper_lookup
        )

        summaries = []

        for key, items in cluster_items:
            cluster_text = self.format_cluster(key, items)
            summary = self.summarize_cluster(cluster_text, llm_service)

            if summary:
                summaries.append(summary.strip())

        return summaries