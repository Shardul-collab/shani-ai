from collections import Counter


def generate_review_direction(repo, workflow_id, execution_attempt_id=None, **kwargs):

    # -----------------------------------
    # FETCH RESEARCH KNOWLEDGE
    # -----------------------------------
    rows = repo.fetch_all(
        """
        SELECT category, value
        FROM ResearchKnowledge
        JOIN Paper ON ResearchKnowledge.paper_id = Paper.id
        WHERE Paper.workflow_id = ?
        """,
        (workflow_id,)
    )

    if not rows:
        return {
            "status": "success",
            "data": "No research knowledge found.",
            "error": None
        }

    # -----------------------------------
    # EXTRACT MATERIALS & APPLICATIONS
    # -----------------------------------
    materials = []
    applications = []

    for row in rows:
        category = row["category"]
        value = row["value"]

        if category == "material":
            materials.append(value)

        elif category == "application":
            applications.append(value)

    # -----------------------------------
    # COUNT FREQUENCY
    # -----------------------------------
    material_counts = Counter(materials)
    application_counts = Counter(applications)

    top_materials = [m for m, _ in material_counts.most_common(3)]
    top_applications = [a for a, _ in application_counts.most_common(3)]

    # -----------------------------------
    # FORMAT FOR LLM
    # -----------------------------------
    materials_text = ", ".join(top_materials) if top_materials else "Not identified"
    applications_text = ", ".join(top_applications) if top_applications else "Not identified"

    print("\n🔬 Review Direction Analysis")
    print("----------------------------------")
    print(f"Top Materials: {materials_text}")
    print(f"Top Applications: {applications_text}")

    # -----------------------------------
    # LLM GENERATION
    # -----------------------------------
    from services.llm_service import LLMService, OllamaClient

    llm = OllamaClient()
    service = LLMService(llm)

    prompt = f"""
Generate EXACTLY 3 possible scientific review paper titles.

Base them strictly on:

Top materials: {materials_text}
Top applications: {applications_text}

Rules:
- Make them distinct
- Keep them realistic academic titles
- No explanations, only titles
"""

    response = service.generate_text(prompt)

    # -----------------------------------
    # FORMAT TITLES
    # -----------------------------------
    titles = [t.strip() for t in response.split("\n") if t.strip()]

    print("\n📄 Suggested Review Titles")
    print("----------------------------------")

    for i, t in enumerate(titles, start=1):
        print(f"{i}. {t}")

    # -----------------------------------
    # USER INPUT
    # -----------------------------------
    while True:
        choice = input("\nSelect a title (1/2/3): ").strip()

        if choice in {"1", "2", "3"} and int(choice) <= len(titles):
            selected_title = titles[int(choice) - 1]
            break

        print("Invalid input. Please enter 1, 2, or 3.")

    print(f"\n✅ Selected Title:\n{selected_title}")

    # -----------------------------------
    # STORE IN WORKFLOW
    # -----------------------------------
    with repo.transaction() as cursor:
        cursor.execute(
            """
            UPDATE Workflow
            SET name = ?
            WHERE id = ?
            """,
            (selected_title, workflow_id)
        )

    return {
        "status": "success",
        "data": selected_title,
        "error": None
    }