def build_prompt(
    source_text: str = "",
    role: str = "General Development Task",
    title: str | None = None,
    links: str | None = None,
    context: str | None = None,
) -> str:
    lines = [
        "You are an experienced technical task writer for a software project.",
        "",
        "Rewrite the rough task input below into TWO equivalent, well-structured task descriptions:",
        "",
        "1. RUSSIAN VERSION",
        "2. ENGLISH VERSION",
        "",
        "Requirements:",
        "- Both versions must have exactly the same structure and exactly the same meaning.",
        "- The English version must be clear, professional working English suitable for an English-speaking developer.",
        "- The Russian version is used by the project manager to verify the meaning.",
        "- Acceptance criteria are MANDATORY in both versions.",
        "",
        f"Target role: {role}",
    ]

    if title:
        lines.append(f"Suggested task title: {title}")
    if links:
        lines.append(f"Relevant links: {links}")
    if context:
        lines.append(f"Additional project context: {context}")

    lines += [
        "",
        "Each version must contain the following sections:",
        "- Task title",
        "- Context",
        "- Goal",
        "- Problem / current behavior",
        "- Expected result",
        "- Scope",
        "- Functional requirements",
        "- Acceptance criteria (mandatory)",
        "- Edge cases",
        "- Risks / dependencies",
        "- Open questions",
        "- Suggested subtasks (where useful)",
        "",
        "Return the two versions clearly separated with the headings 'RUSSIAN VERSION' and 'ENGLISH VERSION'.",
        "",
        "ROUGH TASK INPUT:",
        source_text or "(no input provided)",
    ]
    return "\n".join(lines)
