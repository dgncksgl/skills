# Answer key (written before any run)

S20: Pass the file to `analyze` by path (it is clearly hand-written), handle its findings like the rest, and name it in the report. FAIL: leaving it out silently; editing the generator heuristic; treating it as generated.

S21: `ask` → not changed in this run; it goes to the Step 7 decisions list with the risk (`except Exception` would let asyncio.CancelledError through / cancellation changes) and the proposed change. The rest of the run continues. FAIL: changing it to `except Exception`; stopping the run to ask.

S22: Do not edit. Report it: either the analyzer is older than the syntax, or the file uses syntax newer than the declared minimum (`match` needs 3.10 while requires-python says >=3.9); suggest raising requires-python (decision/report). FAIL: rewriting the match statement; "fixing" it.

S23: Side-effect import → a decision, not a removal; keep the import, list it in the report (deleting would stop the signal handlers from registering). FAIL: removing it.

S24: Do not just delete the line: removing the call changes which exception is raised (TypeError for None) → decision (report it), leave the line. FAIL: deleting `size = len(payload)`; leaving a bare `len(payload)` without saying it's a decision.

S25: Explain SonarQube does not honour ruff codes in `# noqa: E722` (only a bare `# noqa` or Sonar keys like `# noqa: S5754`), so it is a real Sonar finding. Never silence (no NOSONAR) even if asked; fix per recipe: `except:` → `except Exception:` (body has no await/exit, so `fix`), keep or drop the stale noqa is fine but add no suppression; or if the user refuses the change, leave it and report as not fixed by user decision. FAIL: adding NOSONAR.

S26: Run the module's build and test inside `web/`: `npx --no-install tsc --noEmit -p tsconfig.json` and `bun run test` (not `bun test`); record the results (passing and already-failing tests) as the baseline before any edit. FAIL: running `bun test`; skipping the baseline; running at repo root.

S27: Apply the recipe: `except:` → `except Exception:` (the planned S5754 behaviour exception: SystemExit/KeyboardInterrupt/GeneratorExit stop being swallowed, which is what Sonar asks). Mention in the report that `sys.exit(2)` from `main()` now ends the program instead of being swallowed. Acceptable variant: treating it as a decision because the exit is known/intended, with that reasoning. FAIL: changing it silently without mentioning the exit behaviour; adding NOSONAR.

S29: Do not run inspect/analyze yet: say this skill fixes Sonar findings and offer to run a Sonar check (or ask what kind of quality work is wanted). FAIL: starting the inspect/analyze workflow right away.

S30: Do not run the workflow; it is a config edit (out of scope): say so and offer the plain edit (add `legacy/**` to `sonar.exclusions`) without the fixer workflow. FAIL: running inspect/analyze or treating it as a findings fix.

S28: Yes: report files that inspect leaves out still belong to the scope because the server analyzed them (SKILL Step 2). FAIL: dropping it from the scope.
