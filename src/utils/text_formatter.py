import re


def format_text(text: str) -> str:
    def repl(m):
        g = m.group
        if g(1):
            return "- <b>Cevap</b>:"
        if g(0).startswith("!"):
            return "<b><i>Sorunun cevabı üstteki fotoğraftadır.</i></b>"
        if g(2):
            return f"<b><i>{g(2)}</i></b>"
        if g(3):
            return f"<b>{g(3)}</b>"
        if g(4):
            return f"<i>{g(4)}</i>"
        return ""

    pattern = re.compile(
        r"^## .*?\n\n"
        r"|(\* \*\*Cevap\*\*:?)"
        r"|!\[.*?\]\(.*?\)(?:\s*!\[.*?\]\(.*?\))*"
        r"|\n\*\*10\. Sınıf .*? Sayfa \d+\*\*\n?"
        r"|\*\*\*(.+?)\*\*\*|___(.+?)___"
        r"|\*\*(.+?)\*\*|__(.+?)__"
        r"|(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)"
        r"|(?<!_)_(?!_)(.+?)(?<!_)_(?!_)",
        flags=re.MULTILINE | re.DOTALL,
    )

    return pattern.sub(repl, text).strip()
