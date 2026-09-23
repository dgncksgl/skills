import json, subprocess, sys

import os
HOOK = os.environ.get(
    "HOOK",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "inject_simple_style.py"),
)

def run(payload, env=None):
    p = subprocess.run([sys.executable, HOOK], input=json.dumps(payload),
                       capture_output=True, text=True,
                       env={**os.environ, **(env or {})})
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def which(out):
    if not out:
        return set()
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    got = set()
    if "plain-language-explainer" in ctx: got.add("anlat")
    if "plain-language-reporter" in ctx: got.add("rapor")
    if "ayni metni uzatarak" in ctx: got.add("yeni-aci")
    return got

CASES = [
    ("bana açıkla",                                   {"anlat"}),
    ("bana anlat",                                    {"anlat"}),
    ("bunu kısaca anlatır mısın",                     {"anlat"}),
    ("sade basit örneklerle anlatsana",               {"anlat"}),
    ("aciklama yap lutfen",                           {"anlat"}),
    ("explain this flow",                             {"anlat"}),
    ("walk me through the code",                      {"anlat"}),
    ("özetle bana",                                   {"anlat"}),
    ("izah et",                                       {"anlat"}),
    ("bana rapor ver",                                {"rapor"}),
    ("rapor oluştur",                                 {"rapor"}),
    ("bulguları raporla",                             {"rapor"}),
    ("write a report",                                {"rapor"}),
    ("doküman hazırla",                               {"rapor"}),
    ("raporu güncelle ve bana kısaca anlat", {"anlat","rapor"}),
    # negatifler
    ("bu ne anlama geliyor",                          set()),
    ("anlaşma metnini oku",                           set()),
    ("kodu düzelt ve testleri çalıştır",              set()),
    ("faz 2'ye başla",                                set()),
    ("hangi dosyayı değiştirdin",                     set()),
    ("commit mesajı yaz",                             set()),
    ("kanlatma bunu kimseye",                         set()),
    ("xrapor diye bir sey yok",                       set()),
    ("/plain-language-explainer",                     set()),
    ("/plain-language-reporter extra arg",             set()),
    ("[Subagent hand-back] rapor hazir, anlat diyor",  set()),
    ("<task-notification> rapor bitti </task-notification>", set()),
    ("[SYSTEM NOTIFICATION - NOT USER INPUT] anlat",   set()),
    # "anlamadim" ailesi: anlatim istegi degil, onceki anlatimin basarisiz oldugu bildirimi
    ("anlamadım",                                     {"anlat","yeni-aci"}),
    ("anlamadim",                                     {"anlat","yeni-aci"}),
    ("anlamıyorum",                                   {"anlat","yeni-aci"}),
    ("hiçbir şey anlamadım",                          {"anlat","yeni-aci"}),
    ("hala anlamiyorum bunu",                         {"anlat","yeni-aci"}),
    ("anlaşılmıyor",                                  {"anlat","yeni-aci"}),
    ("anlasilmiyor bu kisim",                         {"anlat","yeni-aci"}),
    ("I don't understand",                            {"anlat","yeni-aci"}),
    ("I do not understand this part",                 {"anlat","yeni-aci"}),
    ("didn't understand the diff",                    {"anlat","yeni-aci"}),
    ("this is not clear",                             {"anlat","yeni-aci"}),
    # ikisi birlikte: acik anlatim istegi varsa "yeni aci" notu eklenmez
    ("anlamadım tekrar anlat",                        {"anlat"}),
    ("anlamadım, raporu tekrar ver",         {"anlat","rapor","yeni-aci"}),
    # yanlis tetiklememesi gerekenler
    ("anlamsız olmuş",                                set()),
    ("bu ne anlama geliyor",                          set()),
    ("anlaşma metnini oku",                           set()),
    ("bu şu anlamına gelir",                          set()),
    ("anlamak istiyorum",                             set()),
    ("kanlamadım diye bir kelime",                    set()),
    ("the cache is not cleared yet",                  set()),
    ("bu kod anlamlı değil",                          set()),
]

fail = 0
for text, expected in CASES:
    rc, out, err = run({"hook_event_name":"UserPromptSubmit","user_input":text})
    got = which(out)
    ok = rc == 0 and got == expected
    if not ok:
        fail += 1
    print(f"{'OK ' if ok else 'FAIL'} rc={rc} {text!r} -> {sorted(got) or '-'} (beklenen {sorted(expected) or '-'})")

# fallback alan adi ve bozuk girdi
for payload, label in [({"prompt":"bana anlat"}, "prompt alani fallback"),
                       ({}, "bos payload"),
                       ({"user_input": ""}, "bos metin")]:
    rc, out, err = run(payload)
    print(f"{label}: rc={rc} cikti={'var' if out else 'yok'}")

rc, out, err = subprocess.run([sys.executable, HOOK], input="bozuk-json",
                              capture_output=True, text=True).returncode, "", ""
print(f"bozuk json: rc={rc}")

# skill kurulu degilse olmayan skill cagrilmamali
rc, out, _ = run({"user_input": "bana anlat"}, env={"CLAUDE_SKILLS_DIR": "/nonexistent-skills"})
ok_missing = rc == 0 and out == ""
if not ok_missing:
    fail += 1
print(f"{'OK ' if ok_missing else 'FAIL'} skill kurulu degil -> enjeksiyon yok (rc={rc}, cikti={'var' if out else 'yok'})")

rc, out, _ = run({"user_input": "raporu guncelle ve anlat"},
                 env={"CLAUDE_SKILLS_DIR": os.path.expanduser("~/.claude/skills")})
ok_both = rc == 0 and which(out) == {"anlat", "rapor"}
if not ok_both:
    fail += 1
print(f"{'OK ' if ok_both else 'FAIL'} skills dizini env ile verildi -> iki skill de geldi")

# icerik dogrulugu
rc, out, _ = run({"user_input":"bana anlat"})
ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
print(f"\nenjekte edilen metin: {len(ctx)} karakter")
print("skill govdesi kopyalandi mi (olmamali):", "## Overview" in ctx or "description:" in ctx)
print("Skill tool cagrisi var mi:", "Skill tool" in ctx)
print("baslik:", ctx.splitlines()[0][:60])
print(f"\nTOPLAM HATA: {fail}")
