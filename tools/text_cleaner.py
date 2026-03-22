import re


def clean_scientific_text(text: str) -> str:
    """
    Clean raw PDF text before knowledge extraction.
    Removes noise commonly present in scientific PDFs.
    """

    # --------------------------------
    # 1 Remove emails
    # --------------------------------
    text = re.sub(r"\S+@\S+", " ", text)

    # --------------------------------
    # 2 Remove URLs
    # --------------------------------
    text = re.sub(r"http\S+", " ", text)

    # --------------------------------
    # 3 Remove figure references
    # Example: Fig. 1, Figure 2
    # --------------------------------
    text = re.sub(r"Fig\.\s*\d+", " ", text)
    text = re.sub(r"Figure\s*\d+", " ", text)

    # --------------------------------
    # 4 Remove citations
    # Example: [1], [2,3], (Smith 2020)
    # --------------------------------
    text = re.sub(r"\[\d+(,\s*\d+)*\]", " ", text)
    text = re.sub(r"\([A-Za-z]+,\s*\d{4}\)", " ", text)

    # --------------------------------
    # 5 Remove keywords section
    # --------------------------------
    text = re.sub(
        r"Keywords?:.*?(Introduction|1\.)",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    # --------------------------------
    # 6 Remove references section
    # --------------------------------
    text = re.sub(
        r"References.*",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    # --------------------------------
    # 7 Remove page numbers
    # --------------------------------
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

    # --------------------------------
    # 8 Normalize whitespace
    # --------------------------------
    text = re.sub(r"\s+", " ", text)

    # --------------------------------
    # 9 Fix broken words
    # --------------------------------
    text = text.replace("- ", "")

    return text.strip()