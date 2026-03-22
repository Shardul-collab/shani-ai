import traceback

import repositories.execution_repo as execution_repo

from tools.generate_review_direction import generate_review_direction
from tools.generate_queries import generate_queries
from tools.search_papers import search_papers
from tools.process_papers import process_papers
from tools.download_papers import download_papers
from tools.extract_paper_content import extract_paper_content
from tools.extract_research_knowledge import extract_research_knowledge
from tools.draft_sections import draft_sections
from tools.synthesize_paper import synthesize_paper


class ToolExecutor:

    def __init__(self, repo):
        self.repo = repo

        self.tools = {
            "generate_queries": generate_queries,
            "search_papers": search_papers,
            "process_papers": process_papers,
            "download_papers": download_papers,
            "extract_paper_content": extract_paper_content,
            "extract_research_knowledge": extract_research_knowledge,
            "generate_review_direction": generate_review_direction, 
            "draft_sections": draft_sections,
            "synthesize_paper": synthesize_paper,
        }

    def execute(self, tool_name, workflow_id, kwargs=None):

        if kwargs is None:
            kwargs = {}

        if tool_name not in self.tools:
            raise ValueError(f"Tool not registered: {tool_name}")

        tool = self.tools[tool_name]

        try:
            return tool(self.repo, workflow_id, **kwargs)

        except Exception as e:

            # 🔥 FULL TRACEBACK (VERY IMPORTANT)
            error_trace = traceback.format_exc()

            print(f"\n❌ TOOL FAILURE: {tool_name}")
            print(error_trace)

            return {
                "status": "error",
                "data": None,
                "error": str(e),
                "traceback": error_trace
            }