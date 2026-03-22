def generate_queries(repo, workflow_id, execution_attempt_id=None, **kwargs):

    # --------------------------------------------------
    # FETCH WORKFLOW TITLE (fallback)
    # --------------------------------------------------

    workflow = repo.fetch_one(
        "SELECT name FROM Workflow WHERE id = ?",
        (workflow_id,)
    )

    topic = workflow["name"] if workflow and workflow["name"] else "research topic"

    # --------------------------------------------------
    # FETCH CONFIG
    # --------------------------------------------------

    config = repo.fetch_one(
        """
        SELECT
            material,
            structure,
            focus,
            method,
            properties,
            characterization
        FROM WorkflowResearchConfig
        WHERE workflow_id = ?
        """,
        (workflow_id,)
    )

    # --------------------------------------------------
    # FALLBACK
    # --------------------------------------------------

    if not config:

        queries = [
            f'"{topic}" research paper',
            f'"{topic}" review article',
            f'"{topic}" experimental study'
        ]

        return {
            "status": "success",
            "data": queries,
            "error": None
        }

    # --------------------------------------------------
    # PRIMARY KEYWORD
    # --------------------------------------------------

    material = config["material"] if config["material"] else topic
    primary = f'"{material}"'

    # --------------------------------------------------
    # HELPER FUNCTION
    # --------------------------------------------------

    def parse_keywords(value):

        if not value or value == "ALL":
            return []

        return [v.strip() for v in value.split(",") if v.strip()]

    # --------------------------------------------------
    # SECONDARY / TERTIARY
    # --------------------------------------------------

    secondary = []
    secondary += parse_keywords(config["structure"])
    secondary += parse_keywords(config["focus"])

    tertiary = []
    tertiary += parse_keywords(config["method"])
    tertiary += parse_keywords(config["properties"])
    tertiary += parse_keywords(config["characterization"])

    # --------------------------------------------------
    # GENERATE QUERIES
    # --------------------------------------------------

    queries = []

    # primary only
    queries.append(primary)

    # primary + secondary
    for s in secondary:
        queries.append(f"{primary} {s}")

    # primary + tertiary
    for t in tertiary:
        queries.append(f"{primary} {t}")

    # primary + secondary + tertiary
    for s in secondary:
        for t in tertiary:
            queries.append(f"{primary} {s} {t}")

    # --------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------

    queries = sorted(queries, key=lambda x: len(x.split()), reverse=True)
    queries = list(dict.fromkeys(queries))[:12]

    # limit total queries
    queries = queries[:12]

    return {
        "status": "success",
        "data": queries,
        "error": None
    }
