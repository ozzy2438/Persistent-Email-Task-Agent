from __future__ import annotations

from pydantic import BaseModel, Field

from persistent_agent.tools.base import Tool


class ReadEmailsArgs(BaseModel):
    query: str | None = Field(default=None, description="Optional sender, subject, or body keyword")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum emails to return")


class ReadEmails(Tool):
    name = "read_emails"
    description = "Read locally stored emails for the matching sender, subject, or body text."
    args_schema = ReadEmailsArgs

    def run(self, args: ReadEmailsArgs, *, memory) -> str:
        emails = memory.search_email_text(args.query, k=args.limit) if args.query else memory.list_emails(limit=args.limit)
        if not emails:
            return "No matching emails found."
        return "\n".join(
            f"[{email.id}] From: {email.sender} | Subject: {email.subject} | Body: {email.body}"
            for email in emails
        )


class SummarizeThreadArgs(BaseModel):
    query: str = Field(description="Sender, subject, or keyword that identifies the thread")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum matching emails to summarize")


class SummarizeThread(Tool):
    name = "summarize_thread"
    description = "Summarize the local email thread that matches a sender, subject, or keyword."
    args_schema = SummarizeThreadArgs

    def run(self, args: SummarizeThreadArgs, *, memory) -> str:
        matches = memory.search_email_text(args.query, k=args.limit)
        if not matches:
            return "No matching email thread found."

        latest = matches[0]
        earliest = matches[-1]
        body_points = "; ".join(email.body for email in reversed(matches))
        return (
            f"Thread summary for {args.query}: {len(matches)} email(s). "
            f"Latest sender: {latest.sender}. "
            f"Subject: {latest.subject}. "
            f"Started with: {earliest.body} "
            f"Latest message: {latest.body} "
            f"Combined context: {body_points}"
        )


class DraftReplyArgs(BaseModel):
    query: str = Field(description="Sender, subject, or keyword that identifies the email thread")
    recipient: str | None = Field(default=None, description="Optional explicit reply recipient")
    guidance: str | None = Field(default=None, description="Optional instruction for the draft tone or content")


class DraftReply(Tool):
    name = "draft_reply"
    description = "Draft a reply from local email context only. This never sends email."
    args_schema = DraftReplyArgs

    def run(self, args: DraftReplyArgs, *, memory) -> str:
        matches = memory.search_email_text(args.query, k=1)
        if not matches:
            return "No matching email found to draft a reply from."

        latest = matches[0]
        recipient = args.recipient or latest.sender
        guidance = args.guidance or "Acknowledge the request and confirm the next step."
        return (
            "DRAFT ONLY - NOT SENT\n"
            f"To: {recipient}\n"
            f"Subject: Re: {latest.subject}\n\n"
            f"Hi,\n\n"
            f"I'm following up on your note about {latest.subject}. {guidance} "
            f"Context from the latest message: {latest.body}\n\n"
            "Best,\n"
            "Assistant"
        )
