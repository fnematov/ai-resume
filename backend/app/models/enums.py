import enum


class OrgStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    suspended = "suspended"


class UserRole(str, enum.Enum):
    superadmin = "superadmin"
    org_admin = "org_admin"
    org_member = "org_member"


class VacancyStatus(str, enum.Enum):
    draft = "draft"
    open = "open"
    closed = "closed"


class AIProvider(str, enum.Enum):
    claude = "claude"
    openai = "openai"


class ApplicationSource(str, enum.Enum):
    telegram = "telegram"
    manual = "manual"


class ApplicationStatus(str, enum.Enum):
    """AI-scoring lifecycle (orthogonal to pipeline stage)."""

    pending = "pending"
    processing = "processing"
    scored = "scored"
    failed = "failed"


class ApplicationStage(str, enum.Enum):
    """Position in the recruitment pipeline."""

    new = "new"
    screening = "screening"
    shortlisted = "shortlisted"
    test_task = "test_task"
    interview = "interview"
    offer = "offer"
    hired = "hired"
    rejected = "rejected"
    withdrawn = "withdrawn"


# Ordered list for the Kanban board (terminal stages handled separately in UI).
STAGE_ORDER: list[ApplicationStage] = [
    ApplicationStage.new,
    ApplicationStage.screening,
    ApplicationStage.shortlisted,
    ApplicationStage.test_task,
    ApplicationStage.interview,
    ApplicationStage.offer,
    ApplicationStage.hired,
]


class TemplateType(str, enum.Enum):
    test_task = "test_task"
    interview = "interview"
    offer = "offer"
    rejection = "rejection"
    custom = "custom"


class MessageDirection(str, enum.Enum):
    outbound = "outbound"
    inbound = "inbound"


class MessageChannel(str, enum.Enum):
    telegram = "telegram"


class MessageStatus(str, enum.Enum):
    sent = "sent"
    failed = "failed"
    received = "received"


class SubmissionStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    graded = "graded"
    failed = "failed"


class InterviewProvider(str, enum.Enum):
    calendly = "calendly"
    manual = "manual"


class InterviewStatus(str, enum.Enum):
    scheduled = "scheduled"
    canceled = "canceled"
    completed = "completed"


class AutomationTrigger(str, enum.Enum):
    on_scored = "on_scored"


class AutomationAction(str, enum.Enum):
    reject = "reject"
    shortlist = "shortlist"
    set_stage = "set_stage"
    send_template = "send_template"


class ActivityActor(str, enum.Enum):
    user = "user"
    system = "system"
    candidate = "candidate"


class ActivityType(str, enum.Enum):
    application_created = "application_created"
    ai_scored = "ai_scored"
    stage_changed = "stage_changed"
    message_sent = "message_sent"
    message_received = "message_received"
    test_submitted = "test_submitted"
    test_graded = "test_graded"
    interview_scheduled = "interview_scheduled"
    interview_canceled = "interview_canceled"
    offer_sent = "offer_sent"
    rejected = "rejected"
    note_added = "note_added"
    consent_given = "consent_given"
    data_erased = "data_erased"
