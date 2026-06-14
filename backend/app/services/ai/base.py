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


# --- Conversational vacancy builder -------------------------------------------------

# One assistant turn: a reply, optional quick-reply chips, the running draft, and a flag
# for when the draft is ready to hand back to the form. All fields are required so the
# schema stays valid under OpenAI strict mode (empty strings / empty arrays mean "unset").
VACANCY_DRAFT_TURN_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "message": {
            "type": "string",
            "description": "Your reply to the recruiter: one concise question or a short confirmation.",
        },
        "quick_replies": {
            "type": "array",
            "items": {"type": "string"},
            "description": "0-6 short tappable answer suggestions for your question. Empty when a free-text answer is expected.",
        },
        "complete": {
            "type": "boolean",
            "description": "True only once enough info is gathered and `draft` is fully filled and ready for review.",
        },
        "draft": {
            "type": "object",
            "additionalProperties": False,
            "description": "The vacancy built so far. Use empty strings for fields not yet known.",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "requirements": {"type": "string"},
                "employment_type": {"type": "string"},
                "location": {"type": "string"},
                "ai_instructions": {"type": "string"},
            },
            "required": [
                "title",
                "description",
                "requirements",
                "employment_type",
                "location",
                "ai_instructions",
            ],
        },
    },
    "required": ["message", "quick_replies", "complete", "draft"],
}


def build_vacancy_system_prompt(
    language: str | None = None,
    company_name: str | None = None,
    current: dict | None = None,
) -> str:
    name = LANGUAGE_NAMES.get(language or "en") or "English"
    company = f" for {company_name}" if company_name else ""
    prefilled = ""
    if current:
        filled = {k: v for k, v in current.items() if isinstance(v, str) and v.strip()}
        if filled:
            lines = "\n".join(f"- {k}: {v}" for k, v in filled.items())
            prefilled = (
                "\n\nThe recruiter has ALREADY filled these vacancy fields in the form:\n"
                f"{lines}\n"
                "Treat these as given — do NOT ask about them again. Keep them in the draft, but "
                "you may refine/improve their wording and fill the remaining empty fields. Echo "
                "every field back in `draft` (the filled ones plus what you add).\n"
            )
    return (
        "You are an expert recruiter who creates a complete, professional job vacancy"
        f"{company} from minimal input, through a very short chat.\n\n"
        "CORE PRINCIPLE — think for the recruiter; do NOT interrogate them.\n"
        "From the role title and seniority alone you already know the typical responsibilities "
        "and the standard tech stack, so WRITE the description and requirements YOURSELF. Never "
        "ask the recruiter to describe the role or to list the skills/technologies — that is your "
        "job. Infer sensible, industry-standard details for that role and seniority.\n\n"
        "On EVERY message, first extract everything the recruiter already stated — title, "
        "seniority/level (junior/middle/senior/lead), years of experience, location or work mode, "
        "employment type, salary, etc. — and fill the draft from it. Never re-ask for something "
        "they already told you.\n\n"
        "Ask as FEW questions as possible (aim for zero to two, one at a time), and ONLY for key "
        "facts you cannot reasonably infer:\n"
        "- Seniority/experience level — only if not stated (quick_replies: Junior, Middle, Senior, Lead).\n"
        "- Employment type — only if it matters and is unknown (quick_replies: Full-time, Part-time, Contract).\n"
        "- Work mode — only if unknown (quick_replies: Remote, Hybrid, On-site).\n"
        "ALWAYS prefer `quick_replies` (2-6 short tappable options) over open questions; the "
        "recruiter can also type a custom answer. Default reasonable values when not given "
        "(e.g. assume Full-time) rather than asking. If salary is mentioned, put it in the "
        "description; do not ask for it.\n\n"
        "Each turn, build the full `draft`:\n"
        "- description: a clear, professional 2-4 sentence summary of the role and its main "
        "responsibilities, inferred from the title and seniority.\n"
        "- requirements: a concrete bulleted list of the must-have skills, technologies and "
        "experience expected for this exact role and seniority (e.g. a full-stack PHP/Laravel "
        "role implies PHP, Laravel, MySQL, REST APIs, a JS framework, Git, plus the stated years "
        "of experience).\n"
        "- ai_instructions: leave EMPTY unless the recruiter explicitly stated a strict screening "
        "rule (e.g. 'reject anyone without 5+ years'). Never put notes, assumptions or summaries "
        "here — it is fed verbatim into the candidate-scoring prompt.\n\n"
        "Finish FAST: as soon as you have at least a title and seniority, produce a COMPLETE draft "
        "(description + requirements written), set `complete` to true, and in `message` say the "
        "draft is ready to review, edit and save. A complete draft the recruiter can edit is far "
        "better than more questions. Do not fabricate company-specific facts (exact salary, team "
        "names) that were not provided.\n\n"
        f"IMPORTANT: Write `message`, `quick_replies` and all draft text in {name}. Keep "
        "technology names and proper nouns in their original form (PHP, Laravel, AWS, React)."
        + prefilled
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

    async def _complete_structured(
        self, system_prompt: str, messages: list[dict], schema: dict, schema_name: str
    ) -> dict:
        """Run a chat (system + role/content messages) and return JSON matching `schema`.

        Optional capability — providers that support structured chat override this.
        """
        raise NotImplementedError("This provider does not support structured chat")

    async def build_vacancy(
        self,
        messages: list[dict],
        language: str | None = None,
        company_name: str | None = None,
        current: dict | None = None,
    ) -> dict:
        """One turn of the conversational vacancy builder. Returns a VACANCY_DRAFT_TURN dict."""
        convo = [m for m in messages if m.get("role") in ("user", "assistant") and m.get("content")]
        if not any(m["role"] == "user" for m in convo):
            convo = [{"role": "user", "content": "Help me create a new job vacancy."}, *convo]
        return await self._complete_structured(
            build_vacancy_system_prompt(language, company_name, current),
            convo,
            VACANCY_DRAFT_TURN_SCHEMA,
            "vacancy_draft",
        )

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
