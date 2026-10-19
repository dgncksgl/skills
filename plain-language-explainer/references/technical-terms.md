# Technical Terms

Read this when deciding whether to translate a technical word, define it, or
leave it alone.

## The one test

> Would the user type this word themselves?

The user is a backend developer. If a word appears in their message, in a command
they ran, in a log line, in a file name, or in the code on the screen, they
already own it. Keep it in English, spelled the way it is spelled, and **do not
define it**. Defining a word someone uses every day reads as condescension and
costs a line that a real example could have used.

If it is a word they would not use — something from a library's internals, an
architecture pattern, a statistic — then it does need unpacking. Unpack it by
saying what it does. Never by inventing a translation.

## Translation is not simplification

These are examples, not a closed list; the test above decides the rest.

| Write this | Never write this |
|---|---|
| script | betik |
| thread, thread pool | iplik, iş parçacığı, havuz |
| cache | önbellek |
| commit, branch, rebase, merge | işleme, dal, yeniden temellendirme |
| deploy, pod, container | konuşlandırma, bölmece, kap |
| endpoint, request, response | uç nokta, talep, karşılık |
| log | günlük, kütük |
| lock, retry, timeout, queue | kilit, yeniden deneme, zaman aşımı, kuyruk |
| stack trace | çağrı yığını, yığın izi |
| proxy, instance, session | vekil sunucu, örnek, oturum |

A Turkish coinage nobody says ("betik", "iplik") forces the reader to translate
it back before they can think about it. That is the opposite of plain language.

Some of these words are also ordinary Turkish ones. The rule is about naming:
the component keeps its English name (`lock'u bekliyor`, `havuz değil pool`),
while the same word in its everyday sense stays Turkish — "kuyrukta 147 iş
birikti" is fine, and a market queue in an analogy is still a kuyruk.

## Unpacking a concept the user has no word for

Say what it does, in half a sentence, the first time it appears. Do not open a
dictionary entry for it, and do not give it a Turkish name of your own.

- `lifespan` → "uygulama açılırken ve kapanırken bir kez çalışan bölüm"
- idempotent → "aynı isteği iki kez göndersen de sonuç değişmiyor"
- p95 → "en yavaş yüz istekten beşi bundan da yavaş"

One short clause, then carry on. If the clause is growing into a paragraph, the
idea belongs in its own sentence with its own example.

## Turkish around an English term

Attach the suffix with an apostrophe and let the sentence stay Turkish:
`cache'e yazılıyor`, `thread'ler`, `commit'i aldım`, `branch'ten`, `pod'lar`,
`log'larda`, `endpoint'e`.

Keep the English to the term itself. "Cache disable edildi" is as wrong as
"önbellek devre dışı bırakıldı"; the sentence is "cache'i kapattık".

## What is quoted exactly, never translated

Code identifiers, file names, flags, commands, and error strings are copied as
they are: `search_listing.py`, `--runs 3`, `connection refused`,
`initialDelaySeconds`. Translating one of these makes it impossible to search
for, and the user usually wants to search for it.

## Other languages

The same test applies whatever language the user writes in: everyday tool
vocabulary keeps its English form, and the sentence around it follows the user.
