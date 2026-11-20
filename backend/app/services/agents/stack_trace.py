import re

PYTHON_FRAME = re.compile(r'File "([^"]+)", line \d+, in (\S+)')
JS_FRAME = re.compile(r"at\s+(?:(\S+)\s+\()?([^\s():]+):\d+(?::\d+)?\)?")
JAVA_FRAME = re.compile(r"at\s+[\w.$]+\.(\w+)\(([\w.$]+\.java):\d+\)")
GO_FRAME = re.compile(r"([\w./]+\.go):\d+")

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "when", "then", "and", "or",
    "to", "of", "in", "on", "for", "with", "it", "this", "that", "error",
    "exception", "fails", "failing", "failed", "crash", "crashes", "bug",
}


def extract_search_terms(bug_description: str, error_message: str | None, stack_trace: str | None) -> list[str]:
    """Pull symbol/file-name hints out of free-text bug reports and stack traces.

    Best-effort pattern matching across a few common trace formats (Python, JS/
    Node, Java, Go) -- not a full parser for every language's trace format. Falls
    back to keyword extraction from the bug description when nothing matches.
    """
    terms: set[str] = set()

    for text in (stack_trace, error_message):
        if not text:
            continue
        for match in PYTHON_FRAME.finditer(text):
            file_path, func_name = match.groups()
            terms.add(func_name)
            terms.add(file_path.replace("\\", "/").split("/")[-1])
        for match in JS_FRAME.finditer(text):
            func_name, file_path = match.groups()
            if func_name:
                terms.add(func_name)
            terms.add(file_path.replace("\\", "/").split("/")[-1])
        for match in JAVA_FRAME.finditer(text):
            func_name, file_name = match.groups()
            terms.add(func_name)
            terms.add(file_name)
        for match in GO_FRAME.finditer(text):
            terms.add(match.group(1).split("/")[-1])

    if not terms:
        words = re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", bug_description)
        terms = {w for w in words if w.lower() not in STOPWORDS}

    # Strip file extensions so "auth.py" and "auth" both work as search terms.
    cleaned = set()
    for term in terms:
        cleaned.add(term)
        cleaned.add(re.sub(r"\.(py|js|ts|tsx|java|go|cpp|h|hpp)$", "", term))

    return sorted(cleaned)[:12]
