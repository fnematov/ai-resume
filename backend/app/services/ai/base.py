from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ResumeDocument:
    """A normalized resume ready to be handed to an AI provider.

    Exactly one of (image/pdf bytes) or `text` is the primary payload:
    - `media_type` + `data` for native PDF/image handling (vision models)
    - `text` as a plaintext fallback (extracted from DOC/DOCX or as backup)
    """

    text: str | None = None
    data: bytes | None = None
    media_type: str | None = None  # e.g. "application/pdf", "image/png"
    filename: str | None = None

    @property
    def is_native(self) -> bool:
        return self.data is not None and self.media_type is not None


@dataclass
class JobSpec:
    title: str
    description: str = ""
    requirements: str = ""
    employment_type: str | None = None
    location: str | None = None
    ai_instructions: str | None = None


@dataclass
class ScoreResult:
    match_percentage: int
    verdict: str = ""
    recommended: bool = False
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "match_percentage": self.match_percentage,
            "verdict": self.verdict,
            "recommended": self.recommended,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "strengths": self.strengths,
            "concerns": self.concerns,
            "summary": self.summary,
        }

    @classmethod
    def from_payload(cls, payload: dict) -> "ScoreResult":
        pct = int(round(float(payload.get("match_percentage", 0))))
        pct = max(0, min(100, pct))
        return cls(
            match_percentage=pct,
            verdict=str(payload.get("verdict", "")),
            recommended=bool(payload.get("recommended", False)),
            matched_skills=[str(x) for x in payload.get("matched_skills", []) or []],
            missing_skills=[str(x) for x in payload.get("missing_skills", []) or []],
            strengths=[str(x) for x in payload.get("strengths", []) or []],
            concerns=[str(x) for x in payload.get("concerns", []) or []],
            summary=str(payload.get("summary", "")),
        )


# JSON schema shared by both providers for structured output / tool calling.
SCORE_JSON_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "match_percentage": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
            "description": "How well the resume matches the job, 0-100.",
        },
        "verdict": {
            "type": "string",
            "description": "One short line, e.g. 'Strong match' or 'Not a fit'.",
        },
        "recommended": {
            "type": "boolean",
            "description": "Whether this candidate should advance.",
        },
        "matched_skills": {"type": "array", "items": {"type": "string"}},
        "missing_skills": {"type": "array", "items": {"type": "string"}},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "concerns": {"type": "array", "items": {"type": "string"}},
        "summary": {
            "type": "string",
            "description": "2-4 sentences explaining the score and the decision.",
        },
    },
    "required": [
        "match_percentage",
        "verdict",
        "recommended",
        "matched_skills",
        "missing_skills",
        "strengths",
        "concerns",
        "summary",
    ],
}


LANGUAGE_NAMES = {"uz": "Uzbek (O'zbekcha)", "ru": "Russian (Русский)", "en": "English"}


def _language_instruction(language: str | None) -> str:
    """Tell the model which language to write the natural-language fields in."""
    name = LANGUAGE_NAMES.get(language or "en")
    if not name or language in (None, "en"):
        return ""
    return (
        f"\n\nIMPORTANT: Write the `verdict`, `summary`, `strengths`, `concerns`, `matched_skills` "
        f"and `missing_skills` fields in {name}. Keep technology names, tools, frameworks and other "
        f"proper nouns in their original form (e.g. PHP, Laravel, AWS, React)."
    )


def build_system_prompt(job: JobSpec, language: str | None = None) -> str:
    parts = [
        "You are an expert technical recruiter screening candidates for a specific job.",
        "Evaluate the candidate's application (resume, and a cover letter if one is provided) "
        "STRICTLY against the job below.",
        "Be objective and evidence-based: base the score only on what the materials show. "
        "A strong, relevant cover letter can raise the score; a generic or missing one should not "
        "by itself lower it below what the resume warrants.",
        "If a required skill is absent, list it in missing_skills and lower the score accordingly.",
        "",
        f"# Job title\n{job.title}",
    ]
    if job.employment_type:
        parts.append(f"\n# Employment type\n{job.employment_type}")
    if job.location:
        parts.append(f"\n# Location\n{job.location}")
    if job.description.strip():
        parts.append(f"\n# Job description\n{job.description.strip()}")
    if job.requirements.strip():
        parts.append(f"\n# Requirements / must-haves\n{job.requirements.strip()}")
    if job.ai_instructions and job.ai_instructions.strip():
        parts.append(
            "\n# Additional rules from the recruiter (MUST be strictly followed)\n"
            f"{job.ai_instructions.strip()}"
        )
    parts.append(
        "\nReturn ONLY the structured result via the provided schema. "
        "match_percentage must reflect overall fit (skills, experience, seniority)."
        + _language_instruction(language)
    )
    return "\n".join(parts)


def build_submission_prompt(
    job: JobSpec, instructions: str, criteria: str, language: str | None = None
) -> str:
    parts = [
        "You are a senior engineer grading a candidate's submitted test task.",
        "Evaluate the submission STRICTLY and fairly against the task and the grading criteria.",
        "match_percentage is the overall quality/correctness score (0-100).",
        "Put what the submission did well in `strengths` and `matched_skills`, and problems or "
        "gaps in `concerns` and `missing_skills`. Give a concise justification in `summary`.",
        "",
        f"# Role being hired for\n{job.title}",
    ]
    if instructions.strip():
        parts.append(f"\n# Test task given to the candidate\n{instructions.strip()}")
    if criteria.strip():
        parts.append(f"\n# Grading criteria\n{criteria.strip()}")
    parts.append(
        "\nReturn ONLY the structured result via the provided schema."
        + _language_instruction(language)
    )
    return "\n".join(parts)


class AIProvider(ABC):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    async def _assess(self, system_prompt: str, document: ResumeDocument) -> ScoreResult:
        """Run the model with a system prompt + document, returning a structured ScoreResult."""
        raise NotImplementedError

    async def score_resume(
        self, job: JobSpec, document: ResumeDocument, language: str | None = None
    ) -> ScoreResult:
        return await self._assess(build_system_prompt(job, language), document)

    async def evaluate_submission(
        self,
        job: JobSpec,
        document: ResumeDocument,
        instructions: str,
        criteria: str,
        language: str | None = None,
    ) -> ScoreResult:
        return await self._assess(
            build_submission_prompt(job, instructions, criteria, language), document
        )
