import re

from app.models import Application, Candidate, Organization, Vacancy

# Matches {{ variable }} with optional surrounding whitespace.
_VAR_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")

# Variables offered to template authors (shown in the UI helper).
AVAILABLE_VARIABLES = [
    "candidate_name",
    "job_title",
    "company",
    "scheduling_link",
    "test_task",
    "deadline",
    "salary",
    "start_date",
]


def render(body: str, context: dict[str, str]) -> str:
    """Safe `{{var}}` substitution. Unknown variables are left as-is."""
    return _VAR_RE.sub(lambda m: str(context.get(m.group(1), m.group(0))), body or "")


def build_context(
    *,
    application: Application | None = None,
    vacancy: Vacancy | None = None,
    candidate: Candidate | None = None,
    organization: Organization | None = None,
    extra: dict[str, str] | None = None,
) -> dict[str, str]:
    name = "there"
    if candidate:
        name = candidate.full_name or candidate.telegram_username or "there"

    # Per-application scheduling link so Calendly bookings map back via utm_content.
    scheduling_link = ""
    if organization and organization.calendly_scheduling_url:
        scheduling_link = organization.calendly_scheduling_url
        if application:
            sep = "&" if "?" in scheduling_link else "?"
            scheduling_link = f"{scheduling_link}{sep}utm_content=app_{application.id}"

    ctx: dict[str, str] = {
        "candidate_name": name,
        "job_title": vacancy.title if vacancy else "",
        "company": organization.name if organization else "",
        "scheduling_link": scheduling_link,
    }
    if extra:
        ctx.update({k: str(v) for k, v in extra.items() if v is not None})
    return ctx
