import spacy
import subprocess


# -----------------------------------
# Load NLP model safely
# -----------------------------------

def load_spacy_model():
    try:
        return spacy.load("en_core_web_sm")
    except:
        subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
        return spacy.load("en_core_web_sm")


nlp = load_spacy_model()


# -----------------------------------
# Verb categories
# -----------------------------------

SYNTHESIS_VERBS = {"synthesize", "prepare", "fabricate", "grow", "deposit"}
CHAR_VERBS = {"characterize", "analyze", "measure", "investigate"}
APP_VERBS = {"use", "apply", "employ"}


# -----------------------------------
# Relation Extraction (SAFE VERSION)
# -----------------------------------

def extract_relations(text, entities):
    """
    Minimal safe relation extractor.
    Does not break pipeline.
    """

    relations = []

    try:
        doc = nlp(text)

        # Temporary simple logic
        materials = [e["value"] for e in entities if e["category"] == "material"]

        for sent in doc.sents:
            sent_text = sent.text.lower()

            for m in materials:
                if m.lower() in sent_text:
                    relations.append({
                        "subject": m,
                        "relation": "mentioned_in",
                        "object": sent.text[:100]
                    })

    except Exception as e:
        print("Relation extraction error:", e)

    return relations