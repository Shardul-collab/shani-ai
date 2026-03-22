import repositories.paper_repo as paper_repo


def process_papers(repo, workflow_id, execution_attempt_id=None, **kwargs):

    papers = paper_repo.get_pending_papers(repo, workflow_id)

    if not papers:
        return {
            "status": "success",
            "data": [],
            "error": None
        }

    return {
        "status": "success",
        "data": [p["id"] for p in papers],
        "error": None
    }
