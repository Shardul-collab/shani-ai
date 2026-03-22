import requests
import xml.etree.ElementTree as ET


ARXIV_API = "http://export.arxiv.org/api/query"


def search_arxiv(query, max_results=20):

    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results
    }

    response = requests.get(ARXIV_API, params=params)

    if response.status_code != 200:
        raise Exception("arXiv API request failed")

    root = ET.fromstring(response.text)

    papers = []

    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):

        title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip()

        summary = entry.find("{http://www.w3.org/2005/Atom}summary").text.strip()

        link = None
        for l in entry.findall("{http://www.w3.org/2005/Atom}link"):
            if l.attrib.get("title") == "pdf":
                link = l.attrib["href"]

        papers.append({
            "title": title,
            "summary": summary,
            "source": "arxiv",
            "pdf_url": link
        })

    return papers