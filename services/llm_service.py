import re
import json
import subprocess


class LLMResponseError(Exception):
    pass


class OllamaClient:

    def __init__(self, model="mistral:7b-instruct", timeout=120):
        self.model = model
        self.timeout = timeout

    def generate(self, prompt, max_tokens=1500, temperature=0.7):

        try:
            result = subprocess.run(
                [
                    "ollama",
                    "run",
                    self.model
                ],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

        except FileNotFoundError:
            raise RuntimeError("Ollama not found in PATH")

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Ollama request timed out after {self.timeout} seconds")

        # Handle CLI failure
        if result.returncode != 0:
            raise RuntimeError(
                f"Ollama failed\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            )

        output = result.stdout.strip()

        # Prevent silent failures
        if not output:
            raise RuntimeError("Empty response from Ollama")

        return output


class LLMService:

    ALLOWED_CATEGORIES = {
        "material",
        "synthesis_method",
        "characterization",
        "application",
        "computational_method",
        "software",
        "exchange_correlation",
        "calculated_property"
    }

    def __init__(self, llm_client):
        self.llm = llm_client

    # -----------------------------
    # JSON Knowledge Extraction
    # -----------------------------
    def extract(self, prompt):

        try:
            raw = self.llm.generate(prompt)
        except Exception as e:
            raise LLMResponseError(f"LLM extraction failed: {e}")

        data = self._parse_json(raw)

        if data is None:
            raise LLMResponseError(
                f"Invalid JSON returned by LLM\nRaw output:\n{raw[:500]}"
            )

        return self._validate(data)

    # -----------------------------
    # Plain Text Generation
    # -----------------------------
    def generate_text(self, prompt):

        try:
            return self.llm.generate(prompt, max_tokens=1500, temperature=0.7)
        except Exception as e:
            print(f"[LLM ERROR] {e}")
            return "LLM generation failed."

    # -----------------------------
    # JSON Parsing with Recovery
    # -----------------------------
    def _parse_json(self, raw):

        try:
            return json.loads(raw)

        except Exception:
            match = re.search(r"\[.*\]", raw, re.DOTALL)

            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    return None

            return None

    # -----------------------------
    # Validate Extracted Knowledge
    # -----------------------------
    def _validate(self, data):

        if not isinstance(data, list):
            raise LLMResponseError("LLM output must be a list")

        validated = []

        for item in data:

            if "category" not in item or "value" not in item:
                raise LLMResponseError("Invalid knowledge format")

            category = item["category"]
            value = item["value"]

            if category not in self.ALLOWED_CATEGORIES:
                continue

            validated.append({
                "category": category,
                "value": str(value),
                "section_source": "llm"
            })

        return validated