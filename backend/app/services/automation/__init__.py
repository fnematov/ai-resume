from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ActivityActor,
    ActivityType,
    Application,
    ApplicationStage,
    ApplicationStatus,
    AutomationAction,
    AutomationRule,
    MessageTemplate,
    Organization,
    Vacancy,
)
from app.services.activities import log_activity
from app.services.messaging import build_context, render, send_to_candidate

_ACTION_STAGE = {
    AutomationAction.reject: ApplicationStage.rejected,
    AutomationAction.shortlist: ApplicationStage.shortlisted,
}


async def run_automation_for_application(db: AsyncSession, application_id: int) -> None:
    """Evaluate enabled rules against a just-scored application; apply the first match.

    Hybrid automation: rules can move the stage and/or send a templated message. Commits.
    """
    app_row = await db.get(Application, application_id)
    if (
        app_row is None
        or app_row.status != ApplicationStatus.scored
        or app_row.match_percentage is None
    ):
        return

    rules = (
        await db.execute(
            select(AutomationRule)
            .where(
                AutomationRule.org_id == app_row.org_id,
                AutomationRule.enabled.is_(True),
                or_(
                    AutomationRule.vacancy_id.is_(None),
                    AutomationRule.vacancy_id == app_row.vacancy_id,
                ),
            )
            .order_by(AutomationRule.priority.desc(), AutomationRule.id)
        )
    ).scalars().all()

    score = app_row.match_percentage
    for rule in rules:
        if not (rule.min_score <= score <= rule.max_score):
            continue

        new_stage = _ACTION_STAGE.get(rule.action)
        if new_stage:
            app_row.stage = new_stage

        if rule.action == AutomationAction.send_template or rule.template_id:
            tpl = await db.get(MessageTemplate, rule.template_id) if rule.template_id else None
            if tpl and tpl.org_id == app_row.org_id:
                org = await db.get(Organization, app_row.org_id)
                vacancy = await db.get(Vacancy, app_row.vacancy_id)
                from app.models import Candidate

                candidate = (
                    await db.get(Candidate, app_row.candidate_id)
                    if app_row.candidate_id
                    else None
                )
                ctx = build_context(
                    application=app_row, vacancy=vacancy, candidate=candidate, organization=org
                )
                await send_to_candidate(
                    db, app_row, render(tpl.body, ctx),
                    template_id=tpl.id, actor=ActivityActor.system,
                    activity_summary="Automated message sent",
                )

        await log_activity(
            db,
            application=app_row,
            type=ActivityType.stage_changed if new_stage else ActivityType.message_sent,
            actor=ActivityActor.system,
            summary=f"Automation: {rule.name or rule.action.value} (score {score}%)",
            payload={"rule_id": rule.id, "action": rule.action.value},
        )
        await db.commit()
        return  # first matching rule wins

    return
