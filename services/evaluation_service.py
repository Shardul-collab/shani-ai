
class EvaluationService:

    def __init__(self, repo):
        self.repo = repo

    def workflow_summary(self, workflow_id):

        papers = self.repo.fetch_all(
            "SELECT status FROM Paper WHERE workflow_id = ?",
            (workflow_id,)
        )

        knowledge = self.repo.fetch_all(
            """
            SELECT category, COUNT(*) as count
            FROM ResearchKnowledge
            WHERE paper_id IN (
                SELECT id FROM Paper WHERE workflow_id = ?
            )
            GROUP BY category
            """,
            (workflow_id,)
        )

        return {
            "papers_total": len(papers),
            "knowledge_distribution": knowledge
        }
