import json


class LLMResponseError(Exception):
    pass


class LLMMediator:

    REQUIRED_FIELDS = ["intent", "reasoning", "parameters"]

    def __init__(self, llm_client):
        self.llm = llm_client

    def request(self, prompt):

        # first attempt
        raw = self.llm.generate(prompt)

        data = self._parse_json(raw)

        if data is not None:
            return self._validate_schema(data)

        # correction attempt
        correction_prompt = (
            "Your previous response was not valid JSON.\n"
            "Return the SAME information but formatted as valid JSON.\n"
            "Do not change meaning. Only fix formatting.\n\n"
            f"Original response:\n{raw}"
        )

        raw_retry = self.llm.generate(correction_prompt)

        data_retry = self._parse_json(raw_retry)

        if data_retry is None:
            raise LLMResponseError("LLM returned invalid JSON after correction attempt.")

        return self._validate_schema(data_retry)

    # -----------------------------
    # JSON parsing
    # -----------------------------

    def _parse_json(self, raw):

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    # -----------------------------
    # schema validation
    # -----------------------------

    def _validate_schema(self, data):

        for field in self.REQUIRED_FIELDS:

            if field not in data:
                raise LLMResponseError(f"Missing field in LLM response: {field}")

        return data