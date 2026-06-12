import pytest

from app.models.enums import AIProvider as ProviderEnum
from app.services.ai import ClaudeProvider, OpenAIProvider, get_provider
from app.services.ai.base import (
    JobSpec,
    ResumeDocument,
    ScoreResult,
    build_system_prompt,
)


def test_score_result_clamps_and_coerces():
    r = ScoreResult.from_payload({"match_percentage": 142.7, "recommended": "yes", "summary": "ok"})
    assert r.match_percentage == 100
    assert r.recommended is True
    assert r.summary == "ok"

    r2 = ScoreResult.from_payload({"match_percentage": -5})
    assert r2.match_percentage == 0
    assert r2.matched_skills == []


def test_score_result_roundtrip():
    r = ScoreResult(match_percentage=80, matched_skills=["php"], missing_skills=["aws"])
    d = r.to_dict()
    assert d["match_percentage"] == 80
    assert d["matched_skills"] == ["php"]
    assert set(d) >= {"verdict", "recommended", "strengths", "concerns", "summary"}


def test_build_system_prompt_includes_job_fields():
    job = JobSpec(title="PHP Dev", description="Build APIs", requirements="PHP, Laravel")
    prompt = build_system_prompt(job)
    assert "PHP Dev" in prompt
    assert "Build APIs" in prompt
    assert "Laravel" in prompt


def test_get_provider_factory():
    assert isinstance(get_provider(ProviderEnum.claude, "k"), ClaudeProvider)
    assert isinstance(get_provider(ProviderEnum.openai, "k"), OpenAIProvider)
    # default model resolution
    assert get_provider(ProviderEnum.claude, "k").model.startswith("claude")
    assert get_provider(ProviderEnum.openai, "k", "gpt-4o-mini").model == "gpt-4o-mini"


def test_resume_document_native_flag():
    assert ResumeDocument(data=b"x", media_type="application/pdf").is_native is True
    assert ResumeDocument(text="hello").is_native is False


@pytest.mark.asyncio
async def test_provider_interface_is_pluggable():
    """A fake provider implementing _assess powers both score_resume and evaluate_submission."""
    from app.services.ai.base import AIProvider

    class FakeProvider(AIProvider):
        async def _assess(self, system_prompt, document):
            return ScoreResult(match_percentage=73, verdict="ok", recommended=True)

    p = FakeProvider("key", "model")
    res = await p.score_resume(JobSpec(title="x"), ResumeDocument(text="cv"))
    assert res.match_percentage == 73 and res.recommended

    graded = await p.evaluate_submission(
        JobSpec(title="x"), ResumeDocument(text="solution"), "do X", "criteria Y"
    )
    assert graded.match_percentage == 73


def test_submission_prompt_includes_task_and_criteria():
    from app.services.ai.base import build_submission_prompt

    prompt = build_submission_prompt(JobSpec(title="PHP Dev"), "Build a CRUD API", "Clean code, tests")
    assert "Build a CRUD API" in prompt
    assert "Clean code, tests" in prompt


def test_recruiter_ai_instructions_included_in_prompt():
    from app.services.ai.base import build_system_prompt

    prompt = build_system_prompt(JobSpec(title="x", ai_instructions="Reject without 5+ years"))
    assert "Additional rules from the recruiter" in prompt
    assert "Reject without 5+ years" in prompt
    # No section when not provided
    assert "Additional rules from the recruiter" not in build_system_prompt(JobSpec(title="x"))


def test_language_instruction_added_for_non_english():
    from app.services.ai.base import build_system_prompt

    uz = build_system_prompt(JobSpec(title="x"), "uz")
    assert "Uzbek" in uz
    ru = build_system_prompt(JobSpec(title="x"), "ru")
    assert "Russian" in ru
    # English (or None) adds no language instruction
    assert "IMPORTANT: Write" not in build_system_prompt(JobSpec(title="x"), "en")
    assert "IMPORTANT: Write" not in build_system_prompt(JobSpec(title="x"))
