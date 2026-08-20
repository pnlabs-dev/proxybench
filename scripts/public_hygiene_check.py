from __future__ import annotations

import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".toml", ".yml", ".yaml", ".txt", ".json", ".jsonl"}

# The checker reports only the rule and file path. It never prints a matched
# value, which avoids turning CI logs into a secondary disclosure path.
# Rules intentionally use vendor-neutral labels and context-aware secret shapes.
RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private-key material", re.compile("-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("cloud access-key shaped token", re.compile(r"\b[A-Z]{4}[0-9A-Z]{16}\b")),
    (
        "credential assignment shaped value",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|secret|password)"
            r"\s*[:=]\s*[\"'][A-Za-z0-9_./+=-]{16,}[\"']"
        ),
    ),
    (
        "bearer-token shaped value",
        re.compile(r"(?i)\bBearer\s+[A-Za-z0-9_./+=-]{20,}"),
    ),
    ("API key shaped value", re.compile(r"\bsk-(?:[A-Za-z0-9_-]{3,}-)?[A-Za-z0-9_-]{20,}\b")),
    (
        "credential-bearing proxy/HTTP URL",
        re.compile(r"(?:https?|socks5?)://[^\s/:@]+:[^\s/@]+@", re.IGNORECASE),
    ),
    (
        "IPv4 literal",
        re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)"),
    ),
    (
        "IPv6 literal",
        re.compile(r"(?<![0-9A-Fa-f:])(?:[0-9A-Fa-f]{1,4}:){2,7}[0-9A-Fa-f]{1,4}(?![0-9A-Fa-f:])"),
    ),
    (
        "internal-hostname shaped value",
        re.compile(r"\b[A-Za-z0-9](?:[A-Za-z0-9-]{0,62}\.)+(?:internal|local|lan)\b", re.IGNORECASE),
    ),
    (
        "email address",
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    ),
)

BANNED_FILENAMES = {
    ".env",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secrets.json",
}


def iter_text_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name == "LICENSE":
            files.append(path)
    return files


def main() -> int:
    failures: list[tuple[str, str]] = []

    for path in iter_text_files():
        rel = path.relative_to(ROOT).as_posix()
        if path.name in BANNED_FILENAMES:
            failures.append((rel, "banned sensitive filename"))
            continue

        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in RULES:
            if pattern.search(text):
                failures.append((rel, label))

    if failures:
        print("public hygiene check: FAIL")
        for rel, label in failures:
            print(f"- {rel}: {label}")
        print("Matched values are intentionally suppressed.")
        return 1

    print("public hygiene check: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
