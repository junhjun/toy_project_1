# crossfit-wod-companion - Work Plan

## TL;DR (For humans)
<!-- Fill this LAST, after the detailed plan below is written, so it summarizes the REAL plan. -->
<!-- Plain English for a non-engineer: NO file paths, NO todo numbers, NO wave/agent/tool names. -->

**What you'll get:** A personal Mac agent that detects the allowlisted Kakao room's daily WOD, produces a Korean beginner/intermediate/advanced guide with short approved videos, publishes a polished public mobile page, and sends the stable daily URL at the correct time.

**Why this approach:** Keep all scheduling and state on the user's Mac, use deterministic parsing/catalog rules around a tightly constrained ChatGPT generation step, and deploy only static Astro output. This avoids a backend, paid OpenAI API usage, and fragile private Kakao protocols.

**What it will NOT do:** It will not scrape Kakao databases or private protocols, auto-invent unknown movements, provide medical or personalized loading advice, force three weak videos, or add accounts, payments, workout tracking, analytics, or a CMS.

**Effort:** Large
**Risk:** High - the macOS Accessibility/Kakao surface and unattended subscription-authenticated generation are operationally fragile even though the application architecture is small.
**Decisions to sanity-check:** Same-date corrections update one stable URL and send one correction notice; all embedded videos, including official ones, must be longer than 30 seconds and shorter than 5 minutes; unknown catalog movements fail closed.

Your next move: start execution or request the optional high-accuracy plan review. Full execution detail follows below.

---

> TL;DR (machine): Large/high-risk local-first Python + SQLite + Astro + launchd implementation with deterministic Kakao ingestion, bounded Codex generation, cached YouTube selection, Cloudflare Pages deployment, and fail-closed delivery.

## Scope
### Must have
- One macOS user, one exact Kakao room, one Korean WOD page per workout date, and one stable public URL per date.
- `openkakao-cli` v1.7.1 Accessibility-only adapter, pinned to a verified full commit SHA and limited to `ax-watch`, `ax-read`, and allowlisted `local-send`.
- Deterministic detection, privacy stripping, parsing, revision handling, SQLite transactional state, leases, retry/cutoff rules, and reboot/sleep reconciliation.
- Versioned movement catalog with canonical names, parser aliases, optional `youtube_search_name`, separate `youtube_title_aliases`, pinned official CrossFit source/video IDs, and source-backed coaching facts.
- YouTube selection: `CrossFit <canonical movement>` unless overridden; public/processed/embeddable; normalized title alias match; no Shorts; strict `30s < duration < 5m`; official pinned video promoted only if it also passes; unique video IDs; up to three; 30-day versioned cache.
- Beginner/intermediate/advanced Korean guidance generated only from parsed WOD data and catalog facts through a separate product `codex exec --output-schema` adapter using saved ChatGPT authentication, read-only sandboxing, timeouts, schema/provenance/safety validation, and no OpenAI API key.
- Bright coach-card Astro UI with workout overview, format glossary, timeline, level selector, movement cards, muscles/cues/scaling, video/source states, safety footer, `noindex`, responsive/keyboard/reduced-motion behavior, and minimal client JavaScript.
- Mac Keychain secret loading; direct `wrangler pages deploy`; public marker verification before any Kakao send; launchd watcher + 5-minute reconciliation; install/uninstall/doctor/runbook.
- Harness phase `phases/1-mvp/` whose steps and Acceptance Criteria mirror this plan and pass `python3 scripts/execute.py 1-mvp --check` before execution.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- No private Kakao server protocol, local Kakao DB/key extraction, patched client, credential replay, root requirement, notification bot, or commands outside the three allowlisted AX/local-send operations.
- No remote database, CMS, Workers/Cron scheduler, long-running cloud backend, OpenAI API billing, YouTube download/rehosting, modified player controls, per-page live search, AI video-vision scoring, or channel-reputation subsystem. Local SQLite is explicitly allowed only for orchestration state.
- No generated movement facts, unknown-movement auto-discovery, medical diagnosis, injury treatment, individualized weight prescription, or unreferenced source URLs. Catalog miss or validator failure stops publication.
- No participant names, sender identity, room name, surrounding chat, raw CSV, unrelated messages, API keys, tokens, auth state, or full WOD text in logs, fixtures, repository history, launchd plists, or analytics. Analytics are deferred entirely.
- No forced three-video quota: zero to three valid embeds are acceptable, with official source links retained when an official video fails the duration/availability filter.
- No multi-box tenancy, login, payments, social feed, workout log, leaderboard, native app, or generalized content editor.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: TDD. Python uses `pytest`; Astro uses Vitest/component tests plus `astro check`; adapters use executable fakes/fixtures first and one bounded real-surface smoke test; browser and authenticated UI work uses `aside-browser` only.
- Evidence: <attemptDir>/task-<N>-crossfit-wod-companion.<ext> (attemptDir = currentAttemptDir from 'omo ulw-loop status --json', .omo/evidence/ulw/<session>/<goalId>/a<attempt>; outside ulw-loop use .omo/evidence/)
- Each todo must first capture a failing assertion, then the passing command and decision-relevant output in its evidence artifact. Secrets and real chat identity must be redacted before evidence is persisted.
- Standard local gate: `python3 -m pytest -q && npm --prefix site test -- --run && npm --prefix site run check && npm --prefix site run build && python3 scripts/execute.py 1-mvp --check`.
- External gates: real YouTube API smoke with a non-secret result summary; authenticated `codex exec` schema smoke; Cloudflare public URL marker/noindex check; `openkakao-cli` AX room discovery and intended-message send only in the exact pinned room. If Aside/session/accessibility/auth is unavailable, mark the corresponding phase `blocked`; never substitute another browser or claim the surface passed.

## Execution strategy
### Parallel execution waves
> Target 5-8 todos per wave. Fewer than 3 (except the final) means you under-split.
- Wave 1, foundations (Todos 1-3 in parallel with path ownership): product/harness contracts; Python state/config boundary; Astro design-system shell.
- Wave 2, bounded capabilities (Todos 4-7 after relevant foundations): privacy-safe WOD parser; movement/video catalog; Codex content generator; Kakao AX adapter/provisioning.
- Wave 3, integration and operations (Todos 8-10): transactional daily pipeline; static deployment and verification; launchd/doctor/full real-surface QA.
- Final wave F1-F4 runs only after all ten implementation todos pass. All four must approve the exact same final state.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1 | none | 4,5,6,7,8,9,10 | 2,3 |
| 2 | none | 4,5,6,7,8,10 | 1,3 |
| 3 | none | 9,10 | 1,2 |
| 4 | 1,2 | 8,9,10 | 5,6,7 |
| 5 | 1,2 | 6,8,9,10 | 4,7 |
| 6 | 1,2,5 | 8,9,10 | 4,7 |
| 7 | 1,2 | 8,10 | 4,5,6 |
| 8 | 2,4,5,6,7 | 9,10 | none |
| 9 | 1,3,4,5,6,8 | 10 | none |
| 10 | 1-9 | F1-F4 | none |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [ ] 1. Freeze product contracts, architecture decisions, and harness phase
  What to do / Must NOT do: Replace placeholders in `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/UI_GUIDE.md`, and `ADR.md`; add `DESIGN.md`; create `phases/1-mvp/index.json` plus `step0.md` through `step8.md` mapping Todos 2-10 and their exact Acceptance Criteria. Record: remote DB excluded/local SQLite allowed; Mac launchd owns time; Pages direct upload only; unknown catalog movement stops; room pinning fails closed; same-date WOD is one logical document with revision hash; unsent revision replaces, sent revision rebuilds the same URL and emits at most one correction notice; no send after 23:59 KST; analytics deferred. Must not implement product code or copy real chat/secret data.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 4,5,6,7,8,9,10
  References (executor has NO interview context - be exhaustive): `.omo/drafts/crossfit-wod-companion.md:18-42,64-105`; `AGENTS.md:3-21`; `README.md:14-102`; `docs/PRD.md`; `docs/ARCHITECTURE.md`; `docs/UI_GUIDE.md`.
  Acceptance criteria (agent-executable): `python3 scripts/execute.py 1-mvp --check` exits 0; a Python assertion confirms nine sequential pending steps and matching `stepN.md` files; `rg -n '\{project\}|\{누구|\{선택|\{사용자' docs DESIGN.md ADR.md` returns no matches; architecture tree names `src/wod_companion`, `data`, `schemas`, `prompts`, `site`, `launchd`, `tests`, and `.runtime` boundaries.
  QA scenarios (name the exact tool + invocation): happy - run the harness check and render a contract matrix into Evidence `<attemptDir>/task-1-crossfit-wod-companion.md`; failure - validate a temporary malformed phase copy with a missing step/Acceptance command and capture the expected nonzero diagnostic without changing `phases/1-mvp`, same evidence path.
  Commit: Y | `docs(product): freeze MVP contracts and execution phase`

- [ ] 2. Build typed configuration, Keychain boundary, and transactional SQLite state machine
  What to do / Must NOT do: Add Python package/tooling (`pyproject.toml`, lock strategy, `src/wod_companion/config.py`, `domain.py`, `state.py`, migrations, CLI doctor skeleton, tests). Use stdlib SQLite with WAL, transactions, unique `workout_date`, `revision_hash`, states `detected -> parsed -> generated -> deployed -> sent` plus terminal `failed/expired`, a lease owner/expiry, per-stage attempts/`next_retry_at`, and revision-aware message ledger. Load YouTube/Cloudflare secrets from macOS Keychain into subprocess environment only; Codex uses its own saved auth. Config holds non-secret account/project/base URL and pinned Kakao room reference/display name. Never put secrets in argv, plist, SQLite, logs, fixtures, or repo.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 4,5,6,7,8,10
  References: `.omo/drafts/crossfit-wod-companion.md:33-42,79-82,95-101`; `AGENTS.md:5-9,17-21`; `README.md:104-124`.
  Acceptance criteria: `python3 -m pytest -q tests/test_config.py tests/test_state.py` passes on Python 3.9+; tests prove two workers cannot lease one revision, crash-after-deploy resumes before send, identical revision is idempotent, pre-send correction resets the same date row, post-send correction keeps URL and permits one correction message, expired date cannot send, and redacted diagnostics contain no supplied canary secrets/room names/raw body.
  QA scenarios: happy - drive the state API through one complete revision and a corrected revision using a temporary SQLite DB; failure - simulate concurrent leases, missing Keychain items, corrupt migration, and retry exhaustion, asserting fail-closed states. Evidence `<attemptDir>/task-2-crossfit-wod-companion.txt`.
  Commit: Y | `feat(core): add secure config and transactional WOD state`

- [ ] 3. Establish the bright coach-card design system and Astro state shell
  What to do / Must NOT do: Create `site/` with a locked npm package setup, Astro, minimal client JS, `astro check`, Vitest, global design tokens, fonts with Korean fallbacks, primitives, and a local showcase covering loading, normal, unknown movement, zero/one/three videos, failed embed, and long Korean text. Implement responsive layout, visible focus, 44px targets, reduced motion, contrast, and semantic landmarks. Do not hardcode screenshot pixels, paste a reference image, introduce a component framework, or build final data integration yet.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 9,10
  References: `.omo/drafts/crossfit-wod-companion.md:22,36,41,57,77,83`; `docs/UI_GUIDE.md`; `AGENTS.md:11-15`.
  Acceptance criteria: `npm --prefix site ci && npm --prefix site test -- --run && npm --prefix site run check && npm --prefix site run build` exits 0; token-lint/component tests prove all required showcase states, keyboard labels, reduced-motion CSS, and no horizontal overflow at 320/390/768/1280 widths.
  QA scenarios: happy - serve the showcase and use `aside-browser` snapshot-before/after plus screenshots at 390x844 and 1280x800, keyboard through level/video controls; failure - load zero-video, broken-thumbnail/embed, 200% zoom, and long Korean fixtures. Evidence `<attemptDir>/task-3-crossfit-wod-companion/` with redacted snapshots/screenshots; if Aside is unavailable mark blocked and do not substitute.
  Commit: Y | `feat(site): establish coach-card design system`

- [ ] 4. Implement privacy-first WOD detection and deterministic parsing
  What to do / Must NOT do: Add anonymized fixtures derived structurally, not verbatim, from the five observed formats; implement WOD block extraction, normalization, date precedence, protocol/blocks/rounds/reps/loads/team/synchronization parsing, canonical movement alias resolution, and strict rejection diagnostics. Strip sender, room, surrounding chat, joins/photos/announcements before persistence or Codex input; cap input size and treat all message text as untrusted data, never instructions. Do not store or commit the supplied real-name CSV.
  Parallelization: Wave 2 | Blocked by: 1,2 | Blocks: 8,9,10
  References: `.omo/drafts/crossfit-wod-companion.md:18-20,31-35,46-48,67-68,87-89,101`; user-supplied CSV only as read-only planning evidence, never as a fixture.
  Acceptance criteria: `python3 -m pytest -q tests/test_detection.py tests/test_parser.py tests/test_privacy.py` passes; golden tests cover EMOM, for-time team, AMRAP ladder, multi-block AMRAP, intervals, YYMMDD next-day date, late posting, noise, duplicate, malformed load, unknown movement, oversized input, and prompt-injection-like text; serialized/log outputs contain only workout date, normalized WOD structure, hashes, and catalog IDs.
  QA scenarios: happy - parse all anonymized representative fixtures to golden JSON; failure - feed ordinary chat, photo notice, malicious instruction, missing date, ambiguous movement, and canary names, asserting no detection/publication and no PII leakage. Evidence `<attemptDir>/task-4-crossfit-wod-companion.json`.
  Commit: Y | `feat(parser): add private deterministic WOD parsing`

- [ ] 5. Implement the versioned movement catalog and deterministic video selector
  What to do / Must NOT do: Add `data/movements.json`, schema/tests, and `catalog.py`, `youtube.py`, cache storage. Seed every movement seen in planning plus a documented common CrossFit set. Separate `aliases`, `youtube_search_name`, and `youtube_title_aliases`; seed `Row -> CrossFit Rowing`, generic `Snatch -> CrossFit Barbell Snatch`, generic `Clean -> CrossFit Barbell Clean`, generic `Press -> CrossFit Shoulder Press`. Official status comes only from catalog-pinned CrossFit source/video IDs. Apply Unicode NFKC/case/punctuation/whole-phrase normalization, public/processed/embeddable, title alias, no Shorts, strict `30 < seconds < 300` to every embed including official, dedupe by video ID, promote valid official, then numeric view count, maximum three. Cache key includes movement/catalog/selector version; degradation is fresh cache -> stale matching-version cache -> official source link/no embeds. Never force fillers, search at page view, score with AI, or treat channel display name alone as official.
  Parallelization: Wave 2 | Blocked by: 1,2 | Blocks: 6,8,9,10
  References: `.omo/drafts/crossfit-wod-companion.md:21,34,51-55,69-76,90,99,103-105`; YouTube docs linked at draft lines 51 and 55; CrossFit library linked at line 54.
  Acceptance criteria: `python3 -m pytest -q tests/test_catalog.py tests/test_youtube_selector.py tests/test_video_cache.py` passes; fixtures reproduce the rejected raw `Row`/`Snatch` false positives, accept `CrossFit Devil Press`, enforce boundaries at 30/31/299/300 seconds, exclude out-of-range official video but retain source link, exact numeric ranking, dedupe, optional override, zero-to-three output, cache version invalidation, quota/HTTP/empty-result degradation.
  QA scenarios: happy - run a real read-only YouTube API smoke for Power Clean/Rowing/Barbell Snatch/Devil Press and persist only IDs/titles/channels/counts/durations/statuses; failure - 403 quota, 500, timeout, missing statistics, deleted embed, stale cache, malicious title, and zero results. Evidence `<attemptDir>/task-5-crossfit-wod-companion.json`, with API key redacted.
  Commit: Y | `feat(video): add catalog-backed YouTube selection`

- [ ] 6. Add bounded Codex generation, content schema, provenance, and safety validation
  What to do / Must NOT do: Add `schemas/wod-content.schema.json`, `prompts/wod-content.md`, catalog fact projection, `adapters/codex.py`, `content.py`, and tests. Invoke a separate product adapter, not `scripts/execute.py`, with saved ChatGPT auth, `codex exec --output-schema`, read-only sandbox, fixed timeout, and bounded retry. Send only parsed structures and approved catalog facts in a clearly labeled untrusted-data envelope; disable/forbid tool/network instructions in the task prompt. Require workout intent, format glossary, per-level cues/scaling/emphasis, muscles, safety note, catalog/source IDs; reject unknown IDs/URLs, missing provenance, medical/diagnostic/personal-load language, overlong fields, schema drift, and any instruction-following artifact. Do not retain invalid raw model output or publish on failure.
  Parallelization: Wave 2 | Blocked by: 1,2,5 | Blocks: 8,9,10
  References: `.omo/drafts/crossfit-wod-companion.md:20,38-39,50,61-62,67-68,79,82,89,92,98`; `scripts/execute.py:137-156` proves the harness adapter is separate and must remain unchanged.
  Acceptance criteria: `python3 -m pytest -q tests/test_content_schema.py tests/test_safety.py tests/test_codex_adapter.py` passes with executable fake Codex processes for valid, timeout, rate-limit, nonzero exit, extra prose, invalid JSON/schema, invented movement/source, and prompt injection; `python3 -m wod_companion.cli doctor --check-codex` confirms saved auth without exposing credentials; one authenticated schema smoke returns valid catalog-bound Korean JSON or the phase is honestly blocked.
  QA scenarios: happy - generate from a known anonymized WOD and validate/render the accepted JSON; failure - inject “ignore prior instructions”, medical advice, invented URL/ID, personalized weights, timeout, auth expiry, and rate limit, asserting no deploy/send and only redacted failure state. Evidence `<attemptDir>/task-6-crossfit-wod-companion.json`.
  Commit: Y | `feat(content): add schema-bound Codex coaching generation`

- [ ] 7. Provision and constrain the Kakao Accessibility adapter
  What to do / Must NOT do: Resolve `openkakao-cli` v1.7.1 tag to a full upstream commit SHA, record install/source/checksum in `vendor/openkakao.lock.json`, and implement `adapters/kakao.py` plus provisioning doctor. Permit only `ax-watch`, `ax-read`, and `local-send`; use argv arrays/no shell; cap output; strip PII immediately. Provision an opaque room reference returned by the CLI plus expected exact display name; require both when supported, otherwise require exactly one discoverable exact-name match and record that degraded identity mode. Fail closed on duplicates, rename, Kakao logout/update, missing Accessibility, locked/sleeping UI, or unexpected CLI version. Do not use server login/DB commands and do not send during unit tests.
  Parallelization: Wave 2 | Blocked by: 1,2 | Blocks: 8,10
  References: `.omo/drafts/crossfit-wod-companion.md:40,49,58-60,66,78,80,87-88,91,97`; `AGENTS.md:11-15`.
  Acceptance criteria: `python3 -m pytest -q tests/test_kakao_adapter.py tests/test_room_allowlist.py` passes; static tests prove no forbidden subcommand/string/shell invocation and exact-room fail-closed behavior; `python3 -m wod_companion.cli doctor --check-kakao` verifies pinned version/SHA, Accessibility, Kakao session, and one unique allowlisted room via Aside-backed snapshot-before/after without sending.
  QA scenarios: happy - replay redacted `ax-watch`/`ax-read` transcripts and run real room discovery; failure - duplicate room names, renamed room, malformed output, excessive output, Kakao closed/logged out, permission denied, locked screen, wrong binary/SHA, and attempted forbidden command. Evidence `<attemptDir>/task-7-crossfit-wod-companion/`; browser evidence only from `aside-browser`.
  Commit: Y | `feat(kakao): add pinned fail-closed AX adapter`

- [ ] 8. Orchestrate the revision-aware daily pipeline and bounded recovery
  What to do / Must NOT do: Add `pipeline.py`, CLI commands `watch`, `reconcile`, `process`, scheduling policy, structured redacted logs, and integration tests. Event watcher records candidates; reconciliation runs every five minutes. Delivery: before 09:10 KST queues for 09:10; same-day after 09:10 publishes/sends immediately; prior-evening waits; no send after 23:59. Each invocation processes one leased stage transactionally. Retry with persisted exponential backoff capped at six attempts/stage and one hour, respecting cutoff; next boot resumes incomplete eligible work. Deploy must reach verified state before send; identical revision never repeats; correction rebuilds same date URL and at most one labeled correction notice. Unknown movement/content validation failure stops at failed; video outage may degrade and continue.
  Parallelization: Wave 3 | Blocked by: 2,4,5,6,7 | Blocks: 9,10
  References: `.omo/drafts/crossfit-wod-companion.md:31-35,47,75-82`; state/catalog/generator/Kakao contracts from Todos 2,4-7.
  Acceptance criteria: `python3 -m pytest -q tests/test_pipeline.py tests/test_scheduling.py tests/test_recovery.py` passes with frozen KST clock; integration tests cover before/after 09:10, prior evening, 17:09 late WOD, sleep through 09:10, reboot, duplicate watcher/reconciler, crash at every stage boundary, six-attempt cap, expiry, pre/post-send corrections, video degradation, unknown movement, Codex/deploy/send failures, and exactly-once message ledger.
  QA scenarios: happy - run an end-to-end fake-adapter pipeline from redacted chat event to `sent`, then correction to same URL; failure - inject each dependency failure/crash and concurrent reconciliation, asserting correct persisted resume state and zero premature/duplicate sends. Evidence `<attemptDir>/task-8-crossfit-wod-companion.jsonl`.
  Commit: Y | `feat(pipeline): orchestrate scheduled WOD publication`

- [ ] 9. Render date-stable Astro pages and deploy atomically to Cloudflare Pages
  What to do / Must NOT do: Connect validated content JSON to Astro routes at `/wod/YYYY-MM-DD/`; implement all level/video/source/error states and metadata (`noindex,nofollow`, date/revision marker, Korean title, no PII). Build from a gitignored `.runtime/site-data` projection, never raw chat/SQLite. Add `adapters/cloudflare.py` and CLI deploy using Keychain-loaded token + non-secret account/project config and `wrangler pages deploy site/dist`; scheduling remains on Mac, no Workers/Cron. After exit 0, poll the stable Pages URL with bounded timeout and require HTTP 200, expected date/revision marker, noindex, and absence of canaries before state becomes deployed. A failed deploy/verification never sends; same-date revision atomically replaces the stable path.
  Parallelization: Wave 3 | Blocked by: 1,3,4,5,6,8 | Blocks: 10
  References: `.omo/drafts/crossfit-wod-companion.md:22-23,37,41-42,56-57,76-77,82-83,91,101`; `AGENTS.md:11-15`.
  Acceptance criteria: `npm --prefix site test -- --run && npm --prefix site run check && npm --prefix site run build && python3 -m pytest -q tests/test_site_projection.py tests/test_cloudflare_adapter.py` passes; local output proves stable route/markers/noindex/zero-one-three videos/no PII. Aside provisions or verifies the Pages project/session; one direct upload returns a public stable URL whose fresh snapshot and HTTP check match the expected revision.
  QA scenarios: happy - build fixture page, direct-deploy, HTTP verify, and Aside snapshot at mobile/desktop plus keyboard/reduced-motion; failure - wrong marker, stale deployment, 404/5xx/timeout, leaked canary, token missing, wrangler nonzero, broken embed, zero videos, long Korean text. Evidence `<attemptDir>/task-9-crossfit-wod-companion/`; no alternative browser if Aside is unavailable.
  Commit: Y | `feat(deploy): publish verified static WOD pages`

- [ ] 10. Install launchd operations, finish runbook, and prove the real user journey
  What to do / Must NOT do: Add versioned plist templates without secrets, `scripts/install_launchd.py`, `uninstall_launchd.py`, doctor/status/log-rotation commands, operations/secret-rotation/catalog-maintenance/rollback docs, and full-system tests. Install one persistent watcher and one five-minute reconciler with explicit absolute paths, working directory, bounded logs, KeepAlive only where appropriate, and clean uninstall. Run the full harness/local gate, reboot-equivalent restart/resume test, real Kakao AX read, real authenticated generation, real YouTube selection/cache, real Pages deploy/verification, and exactly one intended current-WOD URL send to the pinned room. Do not send test spam: if no valid current WOD exists, do not fabricate one and do not claim the live-send gate passed; leave that single operational gate blocked until the next genuine WOD.
  Parallelization: Wave 3 | Blocked by: 1-9 | Blocks: F1-F4
  References: `AGENTS.md:5-15,17-29`; `README.md:86-124`; `.omo/drafts/crossfit-wod-companion.md:40,62,79-83,87-101`; every preceding todo contract.
  Acceptance criteria: `python3 scripts/execute.py 1-mvp --check`, the full standard local gate, `python3 -m wod_companion.cli doctor --all`, launchd install/list/restart/status/uninstall/reinstall checks, and an end-to-end evidence ledger all pass; plists/logs/repo/public output contain no secret/PII canaries; Mac sleep/restart reconciliation resumes; public marker is verified before the message ledger records one matching send; install and uninstall are idempotent.
  QA scenarios: happy - observe a genuine allowlisted WOD through watch -> parse -> generate -> select -> build -> deploy -> verify -> one Kakao URL, using Aside snapshots before/after the real browser/Kakao surfaces; failure - locked Mac, Accessibility revoked, Codex auth expired, YouTube quota, Cloudflare token missing, deploy stale, Kakao renamed/closed, crash-before/after-send, and uninstall/reinstall. Evidence `<attemptDir>/task-10-crossfit-wod-companion/`; any unavailable real surface is blocked, never substituted or waved through.
  Commit: Y | `feat(ops): install and verify unattended WOD delivery`

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE the exact final state. Per the user's execution directive, do not pause for an additional approval gate; continue through verified completion and report the result.
- [ ] F1. Plan compliance audit
  Independently map every Must have/Must NOT have and Todo acceptance item to exact files, commands, evidence, and final commit SHA. Re-run the harness check and standard local gate; reject missing real-surface receipts, secret/PII leakage, unverified claims, or state-machine gaps. Evidence `<attemptDir>/final-f1-plan-compliance.md`.
- [ ] F2. Code quality and security review
  Review Python/TypeScript/config diffs for strict types, modules kept below the project size ceiling, transaction/lease correctness, subprocess argv safety, prompt-injection isolation, Keychain-only secrets, redacted logs, pinned supply chain, dependency minimality, Astro accessibility, and no forbidden Kakao/cloud behavior. Run static/test gates against the exact SHA. Evidence `<attemptDir>/final-f2-code-security.md`.
- [ ] F3. Real manual QA
  Use the real Mac surfaces: Aside-only UI QA at 320/390/768/1280, keyboard/200% zoom/reduced motion, zero/one/three/broken video states, Korean wrapping, public date URL/noindex/marker; inspect Kakao AX room identity, the exact intended message, launchd sleep/restart recovery, and one genuine end-to-end delivery receipt. Any missing real surface is a failure/blocked result, not a simulated pass. Evidence `<attemptDir>/final-f3-real-qa/`.
- [ ] F4. Scope fidelity
  Compare final tree/dependencies/runtime services against the approved Scope. Reject analytics, Workers/Cron/backend/CMS, private Kakao access, OpenAI API key/billing, forced video fillers, unknown-movement generation, medical/personal-load claims, multi-user features, unrelated refactors, user files, or dirty-worktree overwrite. Evidence `<attemptDir>/final-f4-scope-fidelity.md`.

## Commit strategy
- One conventional commit per implementation todo, in dependency order, with only owned files and passing targeted acceptance criteria.
- Do not commit generated `.runtime/`, SQLite DBs, site build output, credentials, real chat, downloaded API responses, Aside screenshots containing identity, or `.omo/evidence` unless the execution workflow explicitly tracks redacted evidence.
- The harness does not create branches, commit, or push. `$start-work` owns execution; branch/PR publication requires the user's separate chosen handoff flags.
- Before every commit: inspect `git status --short`, preserve pre-existing unrelated changes, stage explicit paths, and record the exact commit SHA in the evidence ledger.

## Success criteria
- A genuine WOD in the pinned room produces exactly one date-stable public URL after deterministic parse, catalog/source/safety validation, static deploy, and HTTP marker verification; a correction updates that URL and sends no more than one labeled correction notice.
- Beginner/intermediate/advanced Korean explanations are catalog-bound, schema-valid, source-backed, free of medical/personal loading claims, and usable before class on mobile.
- Each movement shows zero to three unique valid videos; every embed, including official, is public/processed/embeddable, title-matched, non-Shorts, and strictly 31-299 seconds; official source links survive when the official video is invalid.
- Kakao access is Accessibility-only, pinned, exact-room allowlisted, fail-closed, and never reads/stores unrelated conversation beyond transient extraction.
- Mac sleep/restart, duplicate events, revisions, dependency outages, and crashes resume transactionally without premature/duplicate sends and stop after the defined bounds/cutoff.
- No paid OpenAI API is used; no remote DB/backend/Cron is deployed; Keychain/Codex auth secrets and participant data are absent from repo, plist, logs, SQLite diagnostics, evidence, and public output.
- All ten implementation todos and F1-F4 have passing, SHA-bound, agent-executed evidence; any genuine live-surface gate that could not run remains explicitly blocked rather than being declared complete.
