import argparse
import shutil
from pathlib import Path

from core.orchestrator import Orchestrator
from repositories.repository import Repository

import repositories.workflow_repo as wr
import repositories.stage_repo as sr
import repositories.execution_repo as er

from services.evaluation_service import EvaluationService


# -----------------------------
# Helpers
# -----------------------------
def prompt_input(label):
    value = input(f"{label}: ").strip()
    return value if value else None


# -----------------------------
# Commands
# -----------------------------
def create_cmd(repo, args):

    print("\nEnter research configuration (leave blank to skip):\n")

    material = args.material or prompt_input("Material")
    structure = args.structure or prompt_input("Structure (comma-separated)")
    focus = args.focus or prompt_input("Focus")
    method = args.method or prompt_input("Method")
    properties = args.properties or prompt_input("Properties")
    characterization = args.characterization or prompt_input("Characterization")

    use_local = 1 if args.use_local else 0

    print("\n--- Confirm Research Configuration ---")
    print(f"Material: {material}")
    print(f"Structure: {structure}")
    print(f"Focus: {focus}")
    print(f"Method: {method}")
    print(f"Properties: {properties}")
    print(f"Characterization: {characterization}")
    print(f"use_local: {use_local}")

    confirm = input("\nProceed? (y/n): ").strip().lower()

    if confirm != "y":
        print("\nAborted by user. Resetting system...\n")
        reset_cmd(repo)
        return

    # --------------------------------
    # CREATE WORKFLOW
    # --------------------------------
    workflow_id = wr.create_workflow(
        repo=repo,
        name=args.name,
        current_stage="S1",
        status="paused"
    )

    print(f"\nWorkflow created with ID {workflow_id}")

    # --------------------------------
    # ALWAYS INSERT CONFIG (FIXED)
    # --------------------------------
    with repo.transaction() as cursor:
        cursor.execute(
            """
            INSERT INTO WorkflowResearchConfig (
                workflow_id,
                material,
                structure,
                focus,
                method,
                properties,
                characterization,
                use_local
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                workflow_id,
                material,
                structure,
                focus,
                method,
                properties,
                characterization,
                use_local
            )
        )

    print("\nResearch configuration saved.")

    # --------------------------------
    # SHOW CONFIG
    # --------------------------------
    config = repo.fetch_one(
        """
        SELECT *
        FROM WorkflowResearchConfig
        WHERE workflow_id = ?
        """,
        (workflow_id,)
    )

    if config:
        print("\nResearch Configuration")
        print("----------------------")

        for k in config.keys():
            if k not in ("id", "workflow_id") and config[k] is not None:
                print(f"{k}: {config[k]}")


def start_cmd(orch, args):

    print("\nStarting workflow...\n")

    orch.start_workflow(args.workflow_id)

    print(f"\nWorkflow {args.workflow_id} started.")


def complete_cmd(orch, args):
    orch.complete_stage(args.stage_id)
    print(f"Stage {args.stage_id} completed.")


def fail_cmd(orch, args):
    orch.fail_stage(args.stage_id, args.message)
    print(f"Stage {args.stage_id} failed: {args.message}")


def retry_cmd(orch, args):
    orch.retry_stage(args.stage_id)
    print(f"Retry attempt created for Stage {args.stage_id}.")


def advance_cmd(orch, args):
    orch.advance_stage(args.workflow_id)
    print(f"Workflow {args.workflow_id} advanced.")


def status_cmd(repo, args):

    workflow = wr.get_workflow(repo, args.workflow_id)

    if workflow is None:
        print("Workflow not found.")
        return

    print("\nWorkflow:")
    print(workflow)

    config = repo.fetch_one(
        """
        SELECT *
        FROM WorkflowResearchConfig
        WHERE workflow_id = ?
        """,
        (args.workflow_id,)
    )

    if config:
        print("\nResearch Keywords")
        print("-----------------")

        for k in config.keys():
            if k not in ("id", "workflow_id") and config[k] is not None:
                print(f"{k}: {config[k]}")

    print("\nStages:")

    for stage_name in Orchestrator.STAGE_SEQUENCE:
        stage = sr.get_stage_by_workflow_and_name(repo, args.workflow_id, stage_name)

        if stage:
            print(stage)

            attempt = er.get_latest_attempt_for_stage(repo, stage["id"])
            print("Latest Attempt:", attempt)


def reset_cmd(repo):

    with repo.transaction() as cursor:
        cursor.execute("DELETE FROM FailureLog")
        cursor.execute("DELETE FROM ExecutionAttempt")
        cursor.execute("DELETE FROM Stage")
        cursor.execute("DELETE FROM Paper")
        cursor.execute("DELETE FROM Workflow")
        cursor.execute("DELETE FROM WorkflowResearchConfig")

    print("\nSystem reset complete. Database cleared.")


def delete_records_cmd(repo):

    project_root = Path(__file__).resolve().parents[1]

    papers_dir = project_root / "papers"
    results_dir = project_root / "results"

    with repo.transaction() as cursor:
        cursor.execute("DELETE FROM FailureLog")
        cursor.execute("DELETE FROM ExecutionAttempt")
        cursor.execute("DELETE FROM Stage")
        cursor.execute("DELETE FROM Paper")
        cursor.execute("DELETE FROM Workflow")
        cursor.execute("DELETE FROM PaperContent")
        cursor.execute("DELETE FROM ResearchKnowledge")
        cursor.execute("DELETE FROM DraftSection")
        cursor.execute("DELETE FROM FinalPaperSection")
        cursor.execute("DELETE FROM WorkflowResearchConfig")

    if papers_dir.exists():
        for f in papers_dir.glob("*"):
            if f.is_file():
                f.unlink()

    if results_dir.exists():
        shutil.rmtree(results_dir)

    results_dir.mkdir()

    print("\nAll records and cached outputs deleted.")


def evaluate_cmd(repo, args):

    evaluator = EvaluationService(repo)

    report = evaluator.workflow_summary(args.workflow_id)

    print("\nWORKFLOW REPORT")
    print("---------------------")

    print("Total Papers:", report["papers_total"])

    print("\nKnowledge Distribution")

    for row in report["knowledge_distribution"]:
        print(row["category"], ":", row["count"])


# -----------------------------
# CLI
# -----------------------------
def main():

    parser = argparse.ArgumentParser(
        description="SHANI CLI — Deterministic Research Workflow Controller"
    )

    subparsers = parser.add_subparsers(dest="command")

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("name")
    create_parser.add_argument("--use-local", action="store_true")
    create_parser.add_argument("--material")
    create_parser.add_argument("--structure")
    create_parser.add_argument("--focus")
    create_parser.add_argument("--method")
    create_parser.add_argument("--properties")
    create_parser.add_argument("--characterization")

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("workflow_id", type=int)

    complete_parser = subparsers.add_parser("complete")
    complete_parser.add_argument("stage_id", type=int)

    fail_parser = subparsers.add_parser("fail")
    fail_parser.add_argument("stage_id", type=int)
    fail_parser.add_argument("--message", required=True)

    retry_parser = subparsers.add_parser("retry")
    retry_parser.add_argument("stage_id", type=int)

    advance_parser = subparsers.add_parser("advance")
    advance_parser.add_argument("workflow_id", type=int)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("workflow_id", type=int)

    subparsers.add_parser("reset")
    subparsers.add_parser("del_r")

    evaluate_parser = subparsers.add_parser("evaluate")
    evaluate_parser.add_argument("workflow_id", type=int)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    repo = Repository()
    orch = Orchestrator(repo)

    try:

        if args.command == "create":
            create_cmd(repo, args)

        elif args.command == "start":
            start_cmd(orch, args)

        elif args.command == "complete":
            complete_cmd(orch, args)

        elif args.command == "fail":
            fail_cmd(orch, args)

        elif args.command == "retry":
            retry_cmd(orch, args)

        elif args.command == "advance":
            advance_cmd(orch, args)

        elif args.command == "status":
            status_cmd(repo, args)

        elif args.command == "reset":
            reset_cmd(repo)

        elif args.command == "del_r":
            delete_records_cmd(repo)

        elif args.command == "evaluate":
            evaluate_cmd(repo, args)

    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    main()