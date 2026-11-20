from app.services.agents.stack_trace import extract_search_terms


def test_extracts_terms_from_python_traceback() -> None:
    trace = (
        'Traceback (most recent call last):\n'
        '  File "app/auth.py", line 12, in authenticate\n'
        "    return check_password(user)\n"
        '  File "app/db.py", line 40, in check_password\n'
        "    raise ValueError('bad hash')\n"
    )
    terms = extract_search_terms("login is broken", "ValueError: bad hash", trace)
    assert "authenticate" in terms
    assert "check_password" in terms
    assert "auth.py" in terms
    assert "auth" in terms  # extension stripped


def test_extracts_terms_from_js_stack() -> None:
    trace = (
        "TypeError: Cannot read property 'id' of undefined\n"
        "    at getUser (src/services/userService.js:22:10)\n"
        "    at src/routes/users.js:8:5\n"
    )
    terms = extract_search_terms("user route crashes", None, trace)
    assert "getUser" in terms
    assert "userService.js" in terms
    assert "users.js" in terms


def test_falls_back_to_keywords_when_no_trace_matches() -> None:
    terms = extract_search_terms("the payment webhook handler silently drops events", None, None)
    assert "payment" in terms
    assert "webhook" in terms
    assert "handler" in terms
    assert "the" not in terms
