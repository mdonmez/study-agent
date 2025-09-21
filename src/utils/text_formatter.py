import re


def format_text(text: str) -> str:
    pattern = re.compile(
        r"^## .*?\n\n"
        r"|(\* \*\*Cevap\*\*:)"
        r"|!\[.*?\]\(.*?\)(?:\s*!\[.*?\]\(.*?\))*"
        r"|\n\*\*10\. Sınıf .*? Sayfa \d+\*\*\n?",
        flags=re.MULTILINE | re.DOTALL,
    )

    def repl(m):
        if m.group(1):
            return "- **Cevap**:"
        if m.group(0).startswith("!"):
            return "***Sorunun cevabı üstteki fotoğraftadır.***"
        return ""

    return pattern.sub(repl, text).strip()
