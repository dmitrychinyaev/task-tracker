import io
import os
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib import fonts as rl_fonts
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer

from app.enums import SprintStatus, TaskStatus, utcnow
from app.models import Image as ImageModel

FONT_REGULAR_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/Library/Fonts/Arial.ttf",
]

FONT_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/Library/Fonts/Arial Bold.ttf",
]

_fonts_registered = False


def _register_fonts() -> None:
    global _fonts_registered
    if _fonts_registered:
        return
    regular = next((p for p in FONT_REGULAR_CANDIDATES if os.path.exists(p)), None)
    bold = next((p for p in FONT_BOLD_CANDIDATES if os.path.exists(p)), None)
    if regular:
        pdfmetrics.registerFont(TTFont("appfont", regular))
        rl_fonts.addMapping("appfont", 0, 0, "appfont")
    if bold:
        pdfmetrics.registerFont(TTFont("appfont-bold", bold))
        rl_fonts.addMapping("appfont-bold", 1, 0, "appfont-bold")
    if regular and bold:
        pdfmetrics.registerFontFamily(
            "appfont",
            normal="appfont",
            bold="appfont-bold",
            italic="appfont",
            boldItalic="appfont-bold",
        )
    _fonts_registered = True


def _styles() -> dict:
    _register_fonts()
    return {
        "title": ParagraphStyle("title", fontName="appfont", fontSize=18, leading=22, spaceAfter=10),
        "h2": ParagraphStyle("h2", fontName="appfont-bold", fontSize=13, leading=17, spaceBefore=10, spaceAfter=6),
        "body": ParagraphStyle("body", fontName="appfont", fontSize=10, leading=14, alignment=TA_LEFT),
        "small": ParagraphStyle("small", fontName="appfont", fontSize=9, leading=12, textColor=colors.HexColor("#444444")),
        "mono": ParagraphStyle("mono", fontName="appfont", fontSize=9, leading=12, textColor=colors.HexColor("#333333")),
    }


def _esc(text) -> str:
    if text is None:
        return ""
    return escape(str(text))


def _para(text: str, style_name: str = "body", styles: dict | None = None) -> Paragraph:
    styles = styles or _styles()
    text = _esc(text).replace("\n", "<br/>")
    return Paragraph(text, styles[style_name])


def _image_to_png_bytes(path: str) -> bytes:
    with PILImage.open(path) as im:
        im = im.convert("RGB")
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        return buf.getvalue()


def _image_flowable(image_record: ImageModel, max_width: float):
    png_bytes = _image_to_png_bytes(image_record.storage_path)
    with PILImage.open(io.BytesIO(png_bytes)) as im:
        width, height = im.size
    scale = min(1.0, max_width / width)
    return Image(io.BytesIO(png_bytes), width=width * scale, height=height * scale)


def _build_pdf(title: str, story: list) -> bytes:
    _register_fonts()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=title,
    )
    doc.build(story)
    return buf.getvalue()


def _empty_if_none(value, placeholder="-") -> str:
    return placeholder if value is None else str(value)


STATUS_LABELS = {
    TaskStatus.BACKLOG: "Backlog",
    TaskStatus.TODO: "To Do",
    TaskStatus.IN_PROGRESS: "In Progress",
    TaskStatus.REVIEW: "Review",
    TaskStatus.QA: "QA",
    TaskStatus.BLOCKED: "Blocked",
    TaskStatus.DONE: "Done",
}

PRIORITY_LABELS = {
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "critical": "Critical",
}


def _status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def _priority_label(priority: str | None) -> str:
    return PRIORITY_LABELS.get(priority or "", priority or "-")


def _fmt_date(value) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d")


def _fmt_datetime(value) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


def generate_task_pdf(task, images_by_id: dict) -> bytes:
    styles = _styles()
    max_width = A4[0] - 32 * mm
    story = [Paragraph(_esc(task.title), styles["title"])]

    meta_lines = [
        f"<b>Assignee:</b> {_esc(task.assignee.name if task.assignee else '-')}",
        f"<b>Status:</b> {_esc(_status_label(task.status))}",
        f"<b>Priority:</b> {_esc(_priority_label(task.priority))}",
        f"<b>Sprint:</b> {_esc(task.sprint.name if task.sprint else '-')}",
        f"<b>Deadline:</b> {_esc(_fmt_date(task.deadline))}",
        f"<b>Created:</b> {_esc(_fmt_datetime(task.created_at))}",
        f"<b>Completed:</b> {_esc(_fmt_datetime(task.completed_at))}",
    ]
    if task.blocked_reason:
        meta_lines.append(f"<b>Blocking reason:</b> {_esc(task.blocked_reason)}")

    tags = ", ".join(t.name for t in task.tags) or "-"
    meta_lines.append(f"<b>Tags:</b> {_esc(tags)}")

    for line in meta_lines:
        story.append(Paragraph(line, styles["body"]))
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("Description", styles["h2"]))
    if task.description:
        for block in task.description:
            if block.get("type") == "text":
                story.append(_para(block.get("content", ""), "body", styles))
                story.append(Spacer(1, 2 * mm))
            elif block.get("type") == "image":
                image_record = images_by_id.get(block.get("image_id"))
                if image_record and os.path.exists(image_record.storage_path):
                    story.append(_image_flowable(image_record, max_width))
                    story.append(Spacer(1, 3 * mm))
    else:
        story.append(_para("-", "body", styles))

    if task.links:
        story.append(Paragraph("Links", styles["h2"]))
        for link in sorted(task.links, key=lambda l: l.id):
            label = link.label or link.url
            story.append(_para(f"{label}: {link.url}", "body", styles))

    if task.comments:
        story.append(Paragraph("Comments", styles["h2"]))
        for comment in sorted(task.comments, key=lambda c: c.created_at):
            story.append(_para(f"[{_fmt_datetime(comment.created_at)}] {comment.text}", "body", styles))

    story.append(Paragraph("Change history", styles["h2"]))
    for event in sorted(task.history, key=lambda h: (h.created_at, h.id)):
        details = _event_text(event)
        story.append(_para(f"[{_fmt_datetime(event.created_at)}] {details}", "small", styles))

    return _build_pdf(f"Task {task.id} - {task.title}", story)


def _event_text(event) -> str:
    parts = [event.event_type.replace("_", " ").title()]
    if event.field_name:
        parts.append(f"field={event.field_name}")
    if event.old_value is not None:
        parts.append(f"old={event.old_value}")
    if event.new_value is not None:
        parts.append(f"new={event.new_value}")
    return " | ".join(parts)


def generate_kanban_pdf(tasks) -> bytes:
    styles = _styles()
    story = [Paragraph("Kanban Snapshot", styles["title"])]
    story.append(_para(f"Generated: {_fmt_datetime(utcnow())}", "small", styles))
    story.append(Spacer(1, 4 * mm))

    statuses = [TaskStatus.BACKLOG, TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.REVIEW, TaskStatus.QA, TaskStatus.BLOCKED, TaskStatus.DONE]
    by_status = {s: [] for s in statuses}
    for task in tasks:
        by_status.setdefault(task.status, []).append(task)

    for status in statuses:
        items = by_status.get(status, [])
        story.append(Paragraph(_status_label(status), styles["h2"]))
        if not items:
            story.append(_para("(no tasks)", "small", styles))
        for task in items:
            assignee = task.assignee.name if task.assignee else "-"
            priority = _priority_label(task.priority)
            story.append(_para(f"• {task.title}  —  {assignee}  —  {priority}", "body", styles))
    return _build_pdf("Kanban Snapshot", story)


def _sprint_summary(task) -> str:
    text = (task.description_text or "").strip()
    if not text:
        return "-"
    return text[:200] + ("…" if len(text) > 200 else "")


def generate_sprint_pdf(sprint, tasks) -> bytes:
    styles = _styles()
    story = [Paragraph(f"Sprint Report: {_esc(sprint.name)}", styles["title"])]
    story.append(_para(
        f"Period: {_fmt_date(sprint.start_date)} – {_fmt_date(sprint.end_date)}  |  Status: {sprint.status}",
        "body", styles,
    ))
    if sprint.description:
        story.append(_para(sprint.description, "small", styles))
    story.append(Spacer(1, 4 * mm))

    groups = {
        "Completed": [t for t in tasks if t.status == TaskStatus.DONE],
        "In progress": [t for t in tasks if t.status in (TaskStatus.IN_PROGRESS, TaskStatus.REVIEW, TaskStatus.QA)],
        "Blocked": [t for t in tasks if t.status == TaskStatus.BLOCKED],
        "Not started": [t for t in tasks if t.status in (TaskStatus.BACKLOG, TaskStatus.TODO)],
    }

    for group_name, group_tasks in groups.items():
        story.append(Paragraph(group_name, styles["h2"]))
        if not group_tasks:
            story.append(_para("(no tasks)", "small", styles))
            continue
        for task in group_tasks:
            assignee = task.assignee.name if task.assignee else "-"
            story.append(Paragraph(
                f"• {_esc(task.title)} — {_esc(_status_label(task.status))} — {_esc(assignee)} — {_esc(_priority_label(task.priority))}",
                styles["body"],
            ))
            story.append(_para(f"  {_sprint_summary(task)}", "small", styles))

    return _build_pdf(f"Sprint Report - {sprint.name}", story)


def generate_activity_pdf(start_date, end_date, events_with_titles) -> bytes:
    styles = _styles()
    story = [Paragraph("Activity Report", styles["title"])]
    story.append(_para(f"Period: {_fmt_date(start_date)} – {_fmt_date(end_date)}", "body", styles))
    story.append(Spacer(1, 4 * mm))

    sections = [
        ("Created", "task_created"),
        ("Completed", "task_completed"),
        ("Status changed", "status_changed"),
        ("Blocked", "task_blocked"),
        ("Unblocked", "task_unblocked"),
        ("Assignee changes", "assignee_changed"),
        ("Sprint changes", "sprint_changed"),
    ]

    for section_title, event_type in sections:
        items = [(title, ev) for ev, title in events_with_titles if ev.event_type == event_type]
        story.append(Paragraph(section_title, styles["h2"]))
        if not items:
            story.append(_para("(no events)", "small", styles))
            continue
        for title, ev in items:
            details = []
            if ev.field_name:
                details.append(f"field={ev.field_name}")
            if ev.old_value is not None:
                details.append(f"old={ev.old_value}")
            if ev.new_value is not None:
                details.append(f"new={ev.new_value}")
            suffix = " | ".join(details)
            line = f"[{_fmt_datetime(ev.created_at)}] {title}"
            if suffix:
                line += f" ({suffix})"
            story.append(_para(line, "body", styles))

    return _build_pdf("Activity Report", story)


