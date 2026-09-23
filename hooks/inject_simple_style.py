"""UserPromptSubmit hook: kullanici 'anlat/aciklar/rapor' dediginde ilgili
anlatim skill'ini cagirmayi zorunlu kilan kisa bir yonlendirme enjekte eder.

Skill govdesini KOPYALAMAZ. Govde tek kaynakta kalir
(~/.claude/skills/<skill>/SKILL.md) ve skill cagrildiginda yuklenir; hook yalnizca
cagrinin atlanmamasini garanti eder. Boylece ayni metin iki kez baglama girmez.
"""

import json
import os
import re
import sys

SKILLS_DIR = os.environ.get(
    "CLAUDE_SKILLS_DIR",
    os.path.join(os.path.expanduser("~"), ".claude", "skills"),
)
DEBUG_FLAG = os.path.join(os.path.expanduser("~"), ".claude", "hooks", ".simple_style_debug")
DEBUG_LOG = os.path.join(os.path.expanduser("~"), ".claude", "hooks", "simple_style_debug.log")

# Turkce ek alabildigi icin govde (stem) eslesmesi yapiyoruz: "anlat" -> anlatir,
# anlatsana, anlatim. Kelime ortasinda yanlis eslesmeyi onlemek icin solda harf olmamali.
LEFT = r"(?<![0-9A-Za-zÀ-ɏ])"

EXPLAIN_PATTERN = re.compile(
    LEFT + r"(anlat|a[çc][ıi]kla|izah|[öo]zetle|explain|walk me through)",
    re.IGNORECASE,
)
REPORT_PATTERN = re.compile(
    LEFT + r"(rapor|report|dok[üu]man haz[ıi]rla)",
    re.IGNORECASE,
)

# "Anlamadim" bir anlatim istegi degil, onceki anlatimin basarisiz oldugunun bildirimi.
# Skill bu durumu ayrica ele aliyor (yeni aci, yeni ornek), o yuzden ayri desen.
# Govde eslesmesi degil tam ek eslesmesi: "anlamsiz", "anlama geliyor", "anlasma"
# yanlislikla tetiklenmesin diye.
CONFUSED_PATTERN = re.compile(
    LEFT + r"(anlamad[ıi]|anlam[ıi]yor|anla[şs][ıi]lm[ıi]yor|"
           r"(don'?t|didn'?t|can'?t|do not|did not) understand|not clear(?![A-Za-z]))",
    re.IGNORECASE,
)

LINE = "- {trigger} -> `{skill}` skill'ini cagir (Skill tool, skill=\"{skill}\").\n"

HEADER = (
    "Bu mesaj anlatim sozlesmesi gerektiren bir istek iceriyor. Cevabi yazmadan once:\n\n"
)

CONFUSED_NOTE = (
    "\nOnceki anlatim anlasilmadi: ayni metni uzatarak tekrarlama. Aciyi degistir, "
    "daha kucuk parcalara bol ve YENI bir ornek ver.\n"
)

FOOTER = (
    "\nSkill'i cagirmadan cevap yazma. Kullanici bu sadelestirmeyi defalarca istedi ve "
    "uyulmadigini soyledi; varsayilan ayrintili/teknik anlatim tarzini bu sozlesme "
    "gecersiz kilar. Skill zaten bu turda cagrildiysa tekrar cagirma, sozlesmeyi uygula."
)


def read_payload():
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def prompt_text(payload):
    for key in ("user_input", "prompt", "userInput"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def skill_installed(name):
    """Skill kurulu mu. Kurulu degilse olmayan bir skill'i cagirtmayiz."""
    return os.path.isfile(os.path.join(SKILLS_DIR, name, "SKILL.md"))


# Arka plan olaylari (subagent raporu, task bildirimi, sistem hatirlaticisi) kullanicinin
# yazdigi mesaj degildir; bunlarda sozlesmeyi enjekte etmiyoruz.
BACKGROUND_MARKERS = (
    "[Subagent hand-back]",
    "<task-notification>",
    "[SYSTEM NOTIFICATION - NOT USER INPUT]",
    "<agent-message from=",
    "<command-name>",
)


def is_background_event(text):
    return any(marker in text for marker in BACKGROUND_MARKERS)


def is_own_slash_command(text):
    first = text.strip().split()[0] if text.strip() else ""
    return first in ("/plain-language-explainer", "/plain-language-reporter")


def write_debug(payload, matched):
    if not os.path.exists(DEBUG_FLAG):
        return
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(
                {"keys": sorted(payload.keys()), "matched": matched,
                 "text_head": prompt_text(payload)[:120]},
                ensure_ascii=False) + "\n")
    except OSError:
        pass


def main():
    payload = read_payload()
    text = prompt_text(payload)
    if not text or is_own_slash_command(text) or is_background_event(text):
        write_debug(payload, [])
        sys.exit(0)

    matched = []
    confused = False
    if EXPLAIN_PATTERN.search(text):
        matched.append(("anlatma/aciklama istegi", "plain-language-explainer"))
    elif CONFUSED_PATTERN.search(text):
        confused = True
        matched.append(("onceki anlatim anlasilmadi", "plain-language-explainer"))
    if REPORT_PATTERN.search(text):
        matched.append(("rapor istegi", "plain-language-reporter"))

    write_debug(payload, [name for _, name in matched])
    if not matched:
        sys.exit(0)

    lines = [
        LINE.format(trigger=trigger, skill=name)
        for trigger, name in matched
        if skill_installed(name)
    ]
    if not lines:
        sys.exit(0)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": (
                HEADER + "".join(lines)
                + (CONFUSED_NOTE if confused else "")
                + FOOTER
            ),
        }
    }))
    sys.exit(0)


main()
