import os
import requests

import repositories.paper_repo as pr
import repositories.failure_repo as failure_repo


PAPERS_DIR = "papers"
MAX_RETRIES = 2
MIN_FILE_SIZE_KB = 50


# =========================================================
# DIRECTORY SETUP
# =========================================================

def ensure_papers_directory():
    if not os.path.exists(PAPERS_DIR):
        os.makedirs(PAPERS_DIR)


# =========================================================
# FETCH PENDING PAPERS
# =========================================================

def get_pending_papers(repo, workflow_id):
    query = """
        SELECT id, title, source, pdf_url
        FROM Paper
        WHERE workflow_id = ?
        AND status = 'pending';
    """
    return repo.fetch_all(query, (workflow_id,))


# =========================================================
# DOWNLOAD FUNCTION
# =========================================================

def download_pdf(url, filepath):

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/pdf",
        "Connection": "keep-alive"
    }

    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(f"Download failed: {url}")

    with open(filepath, "wb") as f:
        f.write(response.content)


# =========================================================
# VALIDATION FUNCTIONS
# =========================================================

def is_valid_pdf_file(filepath):
    try:
        with open(filepath, "rb") as f:
            return f.read(4) == b"%PDF"
    except:
        return False


def is_reasonable_size(filepath, min_kb=MIN_FILE_SIZE_KB):
    size_kb = os.path.getsize(filepath) / 1024
    return size_kb > min_kb


# =========================================================
# MAIN TOOL (S3)
# =========================================================

def download_papers(repo, workflow_id, execution_attempt_id=None, **kwargs):

    ensure_papers_directory()

    papers = get_pending_papers(repo, workflow_id)

    if not papers:
        print("No pending papers found.")
        return {"status": "success", "data": [], "error": None}

    print(f"Found {len(papers)} papers to download.")

    downloaded = []

    for paper in papers:

        paper_id = paper["id"]
        title = paper["title"]
        url = paper["pdf_url"]

        # 🚫 Skip known problematic domains
        if any(domain in url for domain in ["academic.oup.com", "sciencedirect.com"]):
            print(f"Skipping blocked source: {url}")
            pr.update_paper_status(repo, paper_id, "failed")
            continue

        filename = f"{paper_id}.pdf"
        filepath = os.path.join(PAPERS_DIR, filename)

        print(f"\nDownloading paper {paper_id}: {title}")

        pr.update_paper_status(repo, paper_id, "downloading")

        success = False
        error_msg = None

        # --------------------------------------------------
        # RETRY LOOP
        # --------------------------------------------------

        for attempt in range(MAX_RETRIES):
            try:
                print(f"Attempt {attempt + 1}...")

                download_pdf(url, filepath)

                if not is_valid_pdf_file(filepath):
                    raise RuntimeError("Invalid PDF format")

                if not is_reasonable_size(filepath):
                    raise RuntimeError("File too small (likely corrupted)")

                success = True
                break

            except Exception as e:
                error_msg = str(e)
                print(f"Retry {attempt + 1} failed: {error_msg}")

        # --------------------------------------------------
        # SUCCESS / FAILURE HANDLING
        # --------------------------------------------------

        if success:

            pr.update_paper_file_path(repo, paper_id, filepath)
            pr.update_paper_status(repo, paper_id, "processing")

            downloaded.append(filepath)

            print(f"Downloaded & validated → {filepath}")

        else:

            print(f"Failed to download paper {paper_id}")

            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass

            pr.update_paper_status(repo, paper_id, "failed")

            failure_repo.log_failure(
                repo,
                workflow_id,
                "DOWNLOAD_ERROR",
                error_msg or "Unknown download error",
                paper_id=paper_id
            )

    # --------------------------------------------------
    # FINAL RETURN
    # --------------------------------------------------

    if not downloaded:
        return {
            "status": "error",
            "data": [],
            "error": "No papers could be downloaded"
        }

    return {
        "status": "success",
        "data": downloaded,
        "error": None
    }