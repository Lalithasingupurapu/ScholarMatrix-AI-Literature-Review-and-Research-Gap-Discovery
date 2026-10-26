import math
import re
from typing import List, Dict, Any
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


CLUSTER_COLORS = [
    {"bg": "#6366f1", "border": "#4f46e5", "highlight": "#818cf8"}, # Indigo
    {"bg": "#06b6d4", "border": "#0891b2", "highlight": "#22d3ee"}, # Cyan
    {"bg": "#10b981", "border": "#059669", "highlight": "#34d399"}, # Emerald
    {"bg": "#f59e0b", "border": "#d97706", "highlight": "#fbbf24"}, # Amber
    {"bg": "#ec4899", "border": "#db2777", "highlight": "#f472b6"}, # Pink
    {"bg": "#8b5cf6", "border": "#7c3aed", "highlight": "#a78bfa"}, # Violet
    {"bg": "#14b8a6", "border": "#0d9488", "highlight": "#2dd4bf"}, # Teal
]


class CitationGraphBuilder:
    def __init__(self):
        pass

    def build_graph(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Builds a comprehensive citation & semantic network graph from papers.
        """
        if not papers:
            return {"nodes": [], "edges": [], "stats": {}}

        G = nx.DiGraph()
        paper_lookup = {p["id"]: p for p in papers}

        # 1. Add all nodes
        for p in papers:
            G.add_node(p["id"], **p)

        # 2. Check for explicit citation / reference overlaps
        edges_set = set()
        openalex_map = {}
        for p in papers:
            if p.get("openalex_id"):
                openalex_map[p["openalex_id"]] = p["id"]

        for p in papers:
            ref_works = set(p.get("referenced_works", []))
            for other in papers:
                if p["id"] == other["id"]:
                    continue

                # Direct OpenAlex ID match
                other_oa_id = other.get("openalex_id")
                if other_oa_id and other_oa_id in ref_works:
                    edge_key = (p["id"], other["id"])
                    if edge_key not in edges_set:
                        edges_set.add(edge_key)
                        G.add_edge(p["id"], other["id"], type="citation", weight=2.0)

                # Author & Title heuristic citation match
                other_first_author = other.get("authors", [""])[0].split()[-1].lower() if other.get("authors") else ""
                other_year = str(other.get("year", ""))
                other_title_terms = set(re.findall(r'\b[a-z]{4,}\b', other.get("title", "").lower()))

                for raw_ref in p.get("raw_references", []):
                    ref_lower = raw_ref.lower()
                    if other_first_author and len(other_first_author) > 2 and other_first_author in ref_lower:
                        if other_year in ref_lower:
                            edge_key = (p["id"], other["id"])
                            if edge_key not in edges_set:
                                edges_set.add(edge_key)
                                G.add_edge(p["id"], other["id"], type="citation", weight=2.0)
                            break

        # 3. Add semantic similarity links using TF-IDF on paper abstracts
        corpus = []
        for p in papers:
            text = f"{p.get('title', '')} {p.get('abstract', '')}"
            corpus.append(text)

        try:
            vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
            tfidf_matrix = vectorizer.fit_transform(corpus)
            sim_matrix = cosine_similarity(tfidf_matrix)

            n = len(papers)
            for i in range(n):
                # Find top 2 most semantically related papers for each paper
                sim_scores = [(j, sim_matrix[i][j]) for j in range(n) if i != j]
                sim_scores.sort(key=lambda x: x[1], reverse=True)

                for j, score in sim_scores[:2]:
                    if score > 0.18:
                        p1_id = papers[i]["id"]
                        p2_id = papers[j]["id"]
                        # Treat older paper as target or undirected
                        if papers[i].get("year", 2024) >= papers[j].get("year", 2024):
                            source, target = p1_id, p2_id
                        else:
                            source, target = p2_id, p1_id

                        edge_key = (source, target)
                        rev_key = (target, source)
                        if edge_key not in edges_set and rev_key not in edges_set:
                            edges_set.add(edge_key)
                            G.add_edge(source, target, type="semantic", weight=float(score))
        except Exception as e:
            print(f"[Warning] TF-IDF semantic link building error: {e}")

        # If graph is too sparse, connect sequential chronologically related papers
        if len(G.edges) < len(papers) - 1:
            sorted_by_year = sorted(papers, key=lambda x: (x.get("year", 2024), x.get("citation_count", 0)), reverse=True)
            for i in range(len(sorted_by_year) - 1):
                p1_id = sorted_by_year[i]["id"]
                p2_id = sorted_by_year[i + 1]["id"]
                if (p1_id, p2_id) not in edges_set and (p2_id, p1_id) not in edges_set:
                    edges_set.add((p1_id, p2_id))
                    G.add_edge(p1_id, p2_id, type="thematic", weight=1.0)

        # 4. Community detection / Clustering
        G_undirected = G.to_undirected()
        communities = []
        try:
            # Greedy modularity communities
            from networkx.algorithms.community import greedy_modularity_communities
            comms = list(greedy_modularity_communities(G_undirected))
            for c in comms:
                communities.append(list(c))
        except Exception:
            # Fallback to connected components
            for c in nx.connected_components(G_undirected):
                communities.append(list(c))

        if not communities:
            communities = [[p["id"] for p in papers]]

        # Cluster label heuristic generator
        cluster_labels = self._generate_cluster_labels(communities, paper_lookup)

        # 5. Graph centrality metrics
        try:
            centrality = nx.degree_centrality(G)
        except Exception:
            centrality = {p["id"]: 0.5 for p in papers}

        # 6. Format nodes for Vis.js
        vis_nodes = []
        for i, comm in enumerate(communities):
            color_scheme = CLUSTER_COLORS[i % len(CLUSTER_COLORS)]
            c_label = cluster_labels.get(i, f"Research Cluster {i + 1}")

            for pid in comm:
                p = paper_lookup.get(pid)
                if not p:
                    continue

                c_count = p.get("citation_count", 1)
                # Node size based on citations & centrality
                node_size = max(18, min(48, int(16 + math.log(max(c_count, 1) + 1) * 4.5)))

                first_author = p.get("authors", ["Author"])[0].split()[-1] if p.get("authors") else "Author"
                short_label = f"{first_author} ({p.get('year', '')})"

                vis_nodes.append({
                    "id": pid,
                    "label": short_label,
                    "title": f"<b>{p.get('title')}</b><br><i>{', '.join(p.get('authors', [])[:3])} ({p.get('year')})</i><br>Citations: {c_count}<br>Cluster: {c_label}",
                    "full_title": p.get("title"),
                    "authors": p.get("authors", []),
                    "year": p.get("year"),
                    "citations": c_count,
                    "venue": p.get("venue"),
                    "url": p.get("url"),
                    "pdf_url": p.get("pdf_url"),
                    "abstract": p.get("abstract"),
                    "cluster_id": i,
                    "cluster_name": c_label,
                    "value": node_size,
                    "color": {
                        "background": color_scheme["bg"],
                        "border": color_scheme["border"],
                        "highlight": {
                            "background": color_scheme["highlight"],
                            "border": "#ffffff"
                        }
                    },
                    "font": {
                        "color": "#f8fafc",
                        "size": 13,
                        "face": "Inter, system-ui, sans-serif"
                    },
                    "shape": "dot"
                })

        # 7. Format edges for Vis.js
        vis_edges = []
        for u, v, data in G.edges(data=True):
            edge_type = data.get("type", "citation")
            is_citation = edge_type == "citation"

            vis_edges.append({
                "from": u,
                "to": v,
                "arrows": "to" if is_citation else "",
                "dashes": not is_citation,
                "color": {
                    "color": "#94a3b8" if is_citation else "#475569",
                    "highlight": "#60a5fa",
                    "opacity": 0.7 if is_citation else 0.4
                },
                "width": 2 if is_citation else 1,
                "title": "Direct Citation Link" if is_citation else "Semantic / Methodological Similarity",
                "smooth": {
                    "type": "curvedCW",
                    "roundness": 0.15
                }
            })

        # 8. Summary statistics
        stats = {
            "total_nodes": len(vis_nodes),
            "total_edges": len(vis_edges),
            "clusters_count": len(communities),
            "clusters": [{"id": i, "name": cluster_labels.get(i, f"Cluster {i+1}"), "size": len(c)} for i, c in enumerate(communities)],
            "most_influential_papers": sorted(
                [{"id": p["id"], "title": p["title"], "citations": p.get("citation_count", 0), "year": p.get("year")} for p in papers],
                key=lambda x: x["citations"],
                reverse=True
            )[:5]
        }

        return {
            "nodes": vis_nodes,
            "edges": vis_edges,
            "stats": stats
        }

    def _generate_cluster_labels(self, communities: List[List[str]], paper_lookup: Dict[str, Any]) -> Dict[int, str]:
        labels = {}
        theme_keywords = {
            "Verification & Self-Reflection": ["self", "reflection", "corrective", "crag", "verif", "critique"],
            "Architectures & Graph Retrieval": ["graph", "dense", "sparse", "retriev", "index", "vector", "hybrid"],
            "Hallucination & Benchmarking": ["hallucinat", "benchmark", "faithfulness", "factuality", "evaluat", "metric", "ragas"],
            "Context Optimization & Re-ranking": ["lost", "middle", "re-rank", "rerank", "context", "window", "compress"],
            "Agentic & Multi-hop Reasoning": ["agent", "multi-hop", "reasoning", "chain", "workflow", "crud"]
        }

        for idx, comm in enumerate(communities):
            combined_text = ""
            for pid in comm:
                p = paper_lookup.get(pid, {})
                combined_text += f" {p.get('title', '')} {p.get('abstract', '')}".lower()

            best_label = None
            best_count = 0
            for label, kw_list in theme_keywords.items():
                count = sum(len(re.findall(r'\b' + re.escape(kw), combined_text)) for kw in kw_list)
                if count > best_count:
                    best_count = count
                    best_label = label

            labels[idx] = best_label if best_label else f"Thematic Synthesis Focus {idx + 1}"

        return labels
