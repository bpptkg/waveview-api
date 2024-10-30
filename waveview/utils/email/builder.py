import logging
from email.utils import make_msgid
from typing import Any, Iterable, Mapping, MutableMapping, Optional, Sequence, Union

import lxml.html
import toronado
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.mail.utils import DNS_NAME

from waveview.utils.template import render_to_string

from .send import send_messages

logger = logging.getLogger("waveview.mail")


MAX_RECIPIENTS = 5


def force_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return str(value)


def inline_css(value: str) -> str:
    tree = lxml.html.document_fromstring(value)
    toronado.inline(tree)
    html: str = lxml.html.tostring(
        tree, doctype="<!DOCTYPE html>", encoding=None
    ).decode("utf-8")
    return html


class MessageBuilder:
    def __init__(
        self,
        subject: str,
        context: Optional[Mapping[str, Any]] = None,
        template: Optional[str] = None,
        html_template: Optional[str] = None,
        body: str = "",
        html_body: Optional[str] = None,
        headers: Optional[Mapping[str, str]] = None,
        from_email: Optional[str] = None,
        type: Optional[str] = None,
    ) -> None:
        assert not (body and template)
        assert not (html_body and html_template)
        assert context or not (template or html_template)

        self.subject = subject
        self.context = context or {}
        self.template = template
        self.html_template = html_template
        self._txt_body = body
        self._html_body = html_body
        self.headers: MutableMapping[str, Any] = {**(headers or {})}
        self.from_email = from_email or settings.DEFAULT_EMAIL_FROM
        self._send_to: set[str] = set()
        self.type = type if type else "generic"

    def _render_html_body(self) -> Optional[str]:
        if self.html_template:
            html_body: Optional[str] = render_to_string(
                self.html_template, self.context
            )
        else:
            html_body = self._html_body

        if html_body is None:
            return None

        return inline_css(html_body)

    def _render_text_body(self) -> str:
        if self.template:
            body: str = render_to_string(self.template, self.context)
            return body
        return self._txt_body

    def build(
        self,
        to: str,
        reply_to: Optional[Iterable[str]] = None,
        cc: Optional[Sequence[str]] = None,
        bcc: Optional[Sequence[str]] = None,
    ) -> EmailMultiAlternatives:
        headers = {**self.headers}

        reply_to = set(reply_to or ())
        reply_to.discard(to)
        reply_to = ", ".join(reply_to)

        if reply_to:
            headers.setdefault("Reply-To", reply_to)

        # Every message sent needs a unique message id.
        message_id = make_msgid(domain=DNS_NAME)
        headers.setdefault("Message-Id", message_id)

        subject = force_text(self.subject)

        msg = EmailMultiAlternatives(
            subject=subject.splitlines()[0],
            body=self._render_text_body(),
            from_email=self.from_email,
            to=(to,),
            cc=cc or (),
            bcc=bcc or (),
            headers=headers,
        )

        html_body = self._render_html_body()
        if html_body:
            msg.attach_alternative(html_body, "text/html")

        return msg

    def get_built_messages(
        self,
        to: Optional[Iterable[str]] = None,
        cc: Optional[Sequence[str]] = None,
        bcc: Optional[Sequence[str]] = None,
    ) -> Sequence[EmailMultiAlternatives]:
        send_to = set(to or ())
        send_to.update(self._send_to)
        results = [
            self.build(to=email, reply_to=send_to, cc=cc, bcc=bcc)
            for email in send_to
            if email
        ]
        if not results:
            logger.debug("Did not build any messages, no users to send to.")
        return results

    def format_to(self, to: list[str]) -> str:
        if not to:
            return ""
        if len(to) > MAX_RECIPIENTS:
            to = to[:MAX_RECIPIENTS] + [f"and {len(to[MAX_RECIPIENTS:])} more."]
        return ", ".join(to)

    def send(
        self,
        to: Optional[Iterable[str]] = None,
        cc: Optional[Sequence[str]] = None,
        bcc: Optional[Sequence[str]] = None,
        fail_silently: bool = False,
    ) -> int:
        return send_messages(
            self.get_built_messages(to, cc=cc, bcc=bcc), fail_silently=fail_silently
        )

    def send_async(
        self,
        to: Optional[Iterable[str]] = None,
        cc: Optional[Sequence[str]] = None,
        bcc: Optional[Sequence[str]] = None,
    ) -> None:
        from waveview.tasks.send_email import send_email

        messages = self.get_built_messages(to, cc=cc, bcc=bcc)
        extra: MutableMapping[str, Union[str, tuple[str]]] = {"message_type": self.type}
        loggable = [v for k, v in self.context.items() if hasattr(v, "id")]
        for context in loggable:
            extra[f"{type(context).__name__.lower()}_id"] = context.id

        for message in messages:
            send_email.delay(message)

            extra["message_id"] = message.extra_headers["Message-Id"]
            logger.info("mail.queued", extra=extra)
