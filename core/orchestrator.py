from repositories.repository import Repository
import repositories.workflow_repo as workflow_repo
import repositories.stage_repo as stage_repo
import repositories.execution_repo as execution_repo
import repositories.failure_repo as failure_repo

from core.tool_executor import ToolExecutor
from datetime import datetime
import os


class OrchestrationError(Exception):
    pass


class WorkflowNotFoundError(OrchestrationError):
    pass


class InvalidTransitionError(OrchestrationError):
    pass


class StageNotFoundError(OrchestrationError):
    pass


class Orchestrator:

    STAGE_SEQUENCE = ("S1", "S2", "S3", "S4", "S5", "S5_5", "S6", "S7")

    def __init__(self, repo: Repository):
        self.repo = repo
        self.tools = ToolExecutor(repo)

    # =====================================================
    # LOCAL PAPER INGESTION
    # =====================================================

    def ingest_local_papers(self, workflow_id: int):

        papers_dir = "papers"

        if not os.path.exists(papers_dir):
            print("No papers directory found.")
            return

        files = os.listdir(papers_dir)
        count = 0

        for f in files:
            if not f.endswith(".pdf"):
                continue

            title = f.replace(".pdf", "")

            existing = self.repo.fetch_one(
                """
                SELECT id FROM Paper
                WHERE workflow_id = ? AND title = ?
                """,
                (workflow_id, title)
            )

            if existing:
                continue

            timestamp = datetime.utcnow().isoformat()

            with self.repo.transaction() as cursor:
                cursor.execute(
                    """
                    INSERT INTO Paper (
                        workflow_id,
                        title,
                        source,
                        pdf_url,
                        status,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        workflow_id,
                        title,
                        "local",
                        os.path.join("papers", f),
                        "pending",
                        timestamp,
                        timestamp
                    )
                )

            count += 1

        print(f"Ingested {count} local papers.")

    # =====================================================
    # STAGE EXECUTION
    # =====================================================

    def execute_stage(self, stage):

        workflow_id = stage["workflow_id"]
        stage_name = stage["stage_name"]

        print(f"\nExecuting {stage_name}")

        try:

        # ---------------------------
        # STAGE EXECUTION
        # ---------------------------

            if stage_name == "S1":
                result = self.tools.execute("generate_queries", workflow_id)

            elif stage_name == "S2":
                result = self.tools.execute("search_papers", workflow_id)

            elif stage_name == "S3":
                # ✅ FIX 2: REMOVE process_papers (it is useless)
                result = self.tools.execute("download_papers", workflow_id)

            elif stage_name == "S4":
                result = self.tools.execute("extract_paper_content", workflow_id)

            elif stage_name == "S5":
                result = self.tools.execute("extract_research_knowledge", workflow_id)
            elif stage_name == "S5_5":
                result = self.tools.execute("generate_review_direction", workflow_id)

            elif stage_name == "S6":
                result = self.tools.execute("draft_sections", workflow_id)

            elif stage_name == "S7":
                result = self.tools.execute("synthesize_paper", workflow_id)

            else:
                return

            print(f"{stage_name} result:", result)

        # ---------------------------
        # EXECUTION ATTEMPT FETCH
        # ---------------------------

            latest_attempt = execution_repo.get_latest_attempt_for_stage(
                self.repo,
                stage["id"]
            )

        # ---------------------------
        # ERROR CHECK
        # ---------------------------

            if result["status"] == "error":
                raise Exception(result.get("error"))

        # ---------------------------
        # ✅ FIX 1: SAFE UPDATE
        # ---------------------------

            if latest_attempt:
                execution_repo.update_execution_attempt_status(
                    self.repo,
                    latest_attempt["id"],
                    "completed"
                )
            else:
                print(f"[WARN] No execution attempt found for {stage_name}")

            stage_repo.update_stage_status(self.repo, stage["id"], "completed")

        except Exception as e:

            error_msg = str(e)

            print(f"❌ Stage {stage_name} failed:", e)

            latest_attempt = execution_repo.get_latest_attempt_for_stage(
                self.repo,
                stage["id"]
            )

        # ---------------------------
        # ✅ FIX 1 (FAILURE SAFE)
        # ---------------------------

            if latest_attempt:
                execution_repo.update_execution_attempt_status(
                    self.repo,
                    latest_attempt["id"],
                    "failed",
                    error_msg
                )

                failure_repo.log_failure(
                    self.repo,
                    workflow_id,
                    "SYSTEM_ERROR",
                    error_msg,
                    stage_id=stage["id"],
                    execution_attempt_id=latest_attempt["id"]
                )
            else:
                print(f"[WARN] Failure but no execution attempt found for {stage_name}")

            raise OrchestrationError(error_msg)

    # =====================================================
    # START WORKFLOW (LOOP EXECUTION)
    # =====================================================

    def start_workflow(self, workflow_id: int):

        workflow = workflow_repo.get_workflow(self.repo, workflow_id)

        if workflow is None:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found.")

        if workflow["status"] != "paused":
            raise InvalidTransitionError(
                f"Workflow must be paused to start. Current status: {workflow['status']}"
            )

        workflow_repo.update_workflow_status(self.repo, workflow_id, "running")

        config = self.repo.fetch_one(
            """
            SELECT use_local FROM WorkflowResearchConfig
            WHERE workflow_id = ?
            """,
            (workflow_id,)
        )

        if config and config["use_local"]:
            current_stage_name = "S4"
            self.ingest_local_papers(workflow_id)
        else:
            current_stage_name = "S1"

        workflow_repo.update_current_stage(self.repo, workflow_id, current_stage_name)

        # 🔥 LOOP THROUGH STAGES (NO RECURSION)
        while True:

            stage_id = stage_repo.create_stage(
                self.repo,
                workflow_id,
                current_stage_name,
                "running"
            )

            execution_repo.create_execution_attempt(
                self.repo,
                stage_id,
                1,
                "running"
            )

            stage = stage_repo.get_stage_by_id(self.repo, stage_id)

            self.execute_stage(stage)

            if current_stage_name == "S7":
                print("\n✅ Workflow completed.")
                workflow_repo.update_workflow_status(self.repo, workflow_id, "completed")
                break

            # move to next stage
            index = self.STAGE_SEQUENCE.index(current_stage_name)
            current_stage_name = self.STAGE_SEQUENCE[index + 1]

            workflow_repo.update_current_stage(self.repo, workflow_id, current_stage_name)