from services.evaluation_service import EvaluationService
from repositories.repository import Repository


def run(workflow_id):

    repo = Repository("research_workflow.db")

    evaluator = EvaluationService(repo)

    report = evaluator.workflow_summary(workflow_id)

    print("\nWORKFLOW REPORT")
    print("---------------------")

    print("Total Papers:", report["papers_total"])

    print("\nKnowledge Distribution")

    for row in report["knowledge_distribution"]:
        print(row["category"], ":", row["count"])


if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:
        print("Usage: python evaluation_cli.py <workflow_id>")
        exit()

    run(int(sys.argv[1]))