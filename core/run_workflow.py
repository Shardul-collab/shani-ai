from repositories.repository import Repository
import repositories.workflow_repo as wr
import repositories.stage_repo as sr
import repositories.execution_repo as er

from core.orchestrator import Orchestrator
from core.tool_executor import ToolExecutor

import sys




def get_workflow_by_name(repo, name):

    rows = repo.fetch_all(
        """
        SELECT id, name, current_stage, status
        FROM Workflow
        WHERE name = ?
        """,
        (name,)
    )

    if not rows:
        raise ValueError(f"Workflow '{name}' not found")

    return rows[0]


def run_workflow(workflow_name: str):

    repo = Repository()
    orch = Orchestrator(repo)
    executor = ToolExecutor(repo)

    stage_tools = {
        "S1": "generate_queries",
        "S2": "search_papers",
        "S3": "process_papers",
        "S4": "extract_paper_content",
        "S5": "extract_research_knowledge",
        "S6": "draft_sections",
        "S7": "synthesize_paper",
    }

    workflow = get_workflow_by_name(repo, workflow_name)
    workflow_id = workflow["id"]

    print(f"\nRunning workflow: {workflow_name} (ID {workflow_id})")

    # start workflow if paused
    if workflow["status"] == "paused":
        orch.start_workflow(workflow_id)
        print("Workflow started.")

    while True:

        workflow = wr.get_workflow(repo, workflow_id)

        if workflow["status"] == "completed":
            print("\nWorkflow completed.")
            break

        stage_name = workflow["current_stage"]

        stage = sr.get_stage_by_workflow_and_name(repo, workflow_id, stage_name)

        attempt = er.get_latest_attempt_for_stage(repo, stage["id"])

        print(f"\nExecuting {stage_name}")

             

        er.update_execution_attempt_status(
            repo,
            attempt["id"],
            "completed"
        )

        orch.complete_stage(stage["id"])

        if stage_name == "S7":
            print("\nWorkflow completed successfully.")
            break

        orch.advance_stage(workflow_id)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python run_workflow.py \"Workflow Name\"")
        sys.exit(1)

    workflow_name = sys.argv[1]

    run_workflow(workflow_name)
