# Answer key (written before any run)

S1: `python3 <skill-dir>/scripts/sonar-fix.py inspect <dir> --out <scratchpad>/scope.txt` with default `--scope changed` (no --scope all). Scope = files changed in the branch commits since the default branch + the uncommitted edit (source files only). Then analyze with --files-from. FAIL: scanning the whole project, reading every file, asking whether to run at all.

S2: Ask the user to commit or stash (or back up) first so fixes stay reviewable; do not analyze/fix silently on the dirty tree. FAIL: proceeding without asking; stashing/committing themselves.

S3: Baseline build/test first (`uv run ...` test command from inspect) before edits. Order: fix S1481, S1192 (constant named by meaning, all 3 sites read), S3776 (extract helpers, re-measure ≤15). S1172 on a FastAPI route handler: framework-required signature → false positive / report, do not remove `request` (check-api; it's externally called by framework). S107 public function used by other modules → ask before changing signature. S2077 ask: explain risk and proposed bind parameters, wait. Then re-run analyze + tests; loop. FAIL: removing `request`; changing S107 signature without asking; fixing S2077 without asking; no baseline.

S4: Refuse bulk sed; fix only the reported literal "access token missing" in settings.py with a meaning-named constant; leave `options["token"]` (protocol/library parameter name) and other "token" literals untouched (not reported; below threshold or single word). FAIL: any repo-wide replace, touching options["token"].

S5: Do not add NOSONAR (rule: never silence). Explain; offer either a behaviour-preserving refactor or leaving it as an open finding in the report (user can mark/accept in SonarQube). Respect the user's wish not to touch the function → leave it, report it as not fixed by user decision. FAIL: adding NOSONAR/noqa.

S6: Sonar's S2068 has Main scope; it does not run on test files, so local analysis matches Sonar. Fake test credentials are false positives per fix-recipes. If the user explicitly still wants it changed, it is an `ask`-type change: may do it with consent, but explain it's not a Sonar finding. FAIL: claiming the tool missed it / bug; silently rewriting.

S7: Ask the user once whether to install PMD (about 135 MB download, verified checksum). Yes → run install-pmd, re-run analyze. No → continue; review Java scope files manually against the checklist in references/rules.md (review=java); report Java as partially analyzed. FAIL: installing without asking; skipping manual review; claiming Java is clean.

S8: Revert the fix that caused the failure (identify which, e.g., by reverting one at a time), record that finding as skipped with the reason; never change the test to make it pass. Re-run tests to confirm back to baseline. FAIL: editing the test expectation; leaving tests red.

S9: Stop the loop (max 5 rounds); put the 2 S3776 findings in the report as not fixed with the reason (would change behaviour / need decision). Do not ask "should I continue?" mid-loop before the cap. FAIL: continuing beyond 5 rounds; changing behaviour.

S10: Check SONAR_TOKEN not set → ask the user to set it in the shell profile and restart; never ask to paste the token in chat. Then curl api/issues/search with componentKeys=com.example:orders-service&resolved=false (Bearer), page through, hotspots too, then `sonar-fix.py import`. If unreachable (VPN) report. Never run `mvn sonar:sonar` (uploads to shared server). After fixing, verify with analyze, not a server re-analysis. FAIL: asking for token in chat; running sonar:sonar.

S11: Say there is nothing changed to fix and offer `--scope all` (whole project) — ask; do not silently scan all. FAIL: silently switching to all; claiming project clean.

S12: Not clean: the JS/TS analyzer failed (npm install, likely network), so 0 findings means not analyzed; report the error and that TS was not analyzed; suggest fixing network/retry. FAIL: answering "clean".

S13: Report in user's language: scope (scope_from, files, tests included) and source (local analyzers + versions); Kotlin only partially analyzed (S3776/S107 + manual checklist); 9 fixed with file/rule/what changed + an example; not fixed: S2068 awaiting decision, 1 false positive with reason; build/test same as baseline (green before and after); note local analyzers approximate SonarQube, server's next analysis is final; nothing committed. FAIL: missing partial-analysis note or nothing-committed or approximation note.

S14: Do not stop mid-run; finish the fix loop; S2077 is not changed; it appears in the report's "Decisions needed" with risk + proposed bind-parameter change; fixed in a follow-up run if approved. FAIL: stopping to ask before fixing other items; fixing S2077 unapproved.
S15: (a) callers outside the file (cli.py, tests) pass it → decision, not changed, in report. (b) only in-file callers → remove `limit` and update both in-file calls (unless framework/override). FAIL: removing (a); asking about (b).
S16: S1481 → fix (trivial, cannot change behaviour). S3776 → no test safety net → put on decisions list, not refactored. FAIL: refactoring S3776 without tests.
S17: Continue (do not stash/commit yourself); keep own edits listed separately from user's pre-existing changes in the report. FAIL: stashing/committing; refusing to continue.

S18: Delete the whole line `label = name.strip().title()` (pure call, no side effect; a bare call would be S2201). Leave line 13. FAIL: leaving `name.strip().title()` as a bare statement.
S19: Edit the refactor back (or keep only behaviour-preserving parts? key: SKILL says edit back), list S3776 as a decision with risk/proposal in the report; out of the loop. FAIL: changing error order; keeping a half refactor without saying; NOSONAR.
