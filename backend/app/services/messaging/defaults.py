from app.models.enums import TemplateType

# Seeded for an org the first time it opens the Templates screen. Fully editable.
DEFAULT_TEMPLATES: list[dict] = [
    {
        "type": TemplateType.test_task,
        "name": "Test task",
        "body": (
            "Hi {{candidate_name}}! 🎯\n\n"
            "Thanks for applying for the {{job_title}} role at {{company}}. "
            "The next step is a short test task:\n\n"
            "{{test_task}}\n\n"
            "Please send your solution here (a file or a link). Deadline: {{deadline}}."
        ),
    },
    {
        "type": TemplateType.interview,
        "name": "Interview invitation",
        "body": (
            "Hi {{candidate_name}}! 🎉\n\n"
            "{{company}} would like to invite you to an interview for the {{job_title}} role.\n\n"
            "Please pick a time that works for you here:\n{{scheduling_link}}"
        ),
    },
    {
        "type": TemplateType.offer,
        "name": "Job offer",
        "body": (
            "Congratulations {{candidate_name}}! 🥳\n\n"
            "{{company}} is delighted to offer you the {{job_title}} position. "
            "Your official offer letter is attached. We can't wait to have you on the team!"
        ),
    },
    {
        "type": TemplateType.rejection,
        "name": "Polite rejection",
        "body": (
            "Dear {{candidate_name}},\n\n"
            "Thank you for your interest in the {{job_title}} role at {{company}} and for the "
            "time you invested. After careful consideration we've decided to move forward with "
            "other candidates this time.\n\n"
            "We were genuinely impressed and encourage you to apply again in the future. "
            "We wish you all the best. 🙏"
        ),
    },
]
