import repositories.paper_repo


def ingest_search_results(repo, workflow_id, papers):
    """
    Save search results into Paper table
    """

    ids = []

    for p in papers:

        title = p.get("title")
        source = p.get("source", "SemanticScholar")

        if not title:
            continue

        paper_id = paper_repo.create_paper(
            repo=repo,
            workflow_id=workflow_id,
            title=title,
            source=source,
            status="pending"
        )

        ids.append(paper_id)

    return ids