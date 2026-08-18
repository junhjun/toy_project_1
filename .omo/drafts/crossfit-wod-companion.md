---
slug: crossfit-wod-companion
status: execution-approved
intent: clear
review_required: false
pending-action: commit the planning baseline, migrate Todo 1 into the project harness, then execute the remaining plan in a fresh Luna High session without additional approval gates
approach: macOS openkakao-cli AX watcher + Python orchestration + ChatGPT-authenticated codex exec structured generation + Astro static UI + Cloudflare Pages + allowlisted Kakao local-send
---

# Draft: crossfit-wod-companion

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->

| id | outcome | status | evidence path |
|---|---|---|---|
| C1-ingestion | WOD 원문을 개인정보 없이 안정적으로 접수하고 중복을 제거한다 | active | attached CSV analysis; Kakao Talk Message official docs |
| C2-parse | 날짜, 프로토콜, 라운드, 반복수, 중량, 팀/동기화 조건을 정규화한다 | active | attached CSV: 5 representative WOD rows |
| C3-content | 용어·레벨별 큐·스케일·주의사항을 스키마 검증되는 카탈로그와 일일 콘텐츠로 조립한다 | active | CrossFit movement references; user brief |
| C4-video | CrossFit 공식 영상을 최우선으로 두고 YouTube에서 정확한 동작명 검색 결과를 조회수 순으로 받아 동작별 최대 3개를 캐시한다 | active | CrossFit movement library; YouTube Data API |
| C5-experience | 모바일 우선 WOD 페이지를 밝은 코치 카드 디자인으로 제공한다 | active | docs/UI_GUIDE.md; frontend design research |
| C6-publish | 저비용 호스팅에서 검증된 URL을 발행하고 허용된 카카오 방에 한 번만 전달한다 | active | Cloudflare Pages docs; openkakao-cli AX path |

## Open assumptions (announced defaults)
<!-- Record any default you adopt instead of asking, so the user can veto it at the gate. -->
<!-- assumption | adopted default | rationale | reversible? -->

| assumption | adopted default | rationale | reversible? |
|---|---|---|---|
| WOD 판별 | 본문 규칙을 1차 신호로 쓰고 코치 발신자는 선택적 가중치로만 사용 | 표본은 같은 발신자지만 계정 변경 가능 | yes |
| 날짜 | 메시지 안의 YYMMDD를 운동일로 우선하고 채팅 시각은 원본 메타데이터로 분리 | 표본 5건 모두 게시일의 다음 날 코드 | yes |
| 중복 | 정규화 본문 해시 + 운동일을 idempotency key로 사용 | 재수집/재게시 비용과 중복 URL 방지 | yes |
| 영상 | 기본 `CrossFit <canonical movement>` 검색 + 선택적 카탈로그 검색명 + 30초 초과·5분 미만 길이 제한 | two live stress-test rounds; user duration decision | yes |
| 개인정보 | WOD 본문과 운동일만 저장하고 참가자 이름·전체 대화는 저장하지 않음 | 데이터 최소화 | yes |
| 테스트 | 파서·스키마는 TDD, UI는 컴포넌트 상태 테스트 + 실제 브라우저 시각 QA | AGENTS.md와 UI 품질 요구 | yes |
| 기술 방향 | 정적 Pages 배포와 Mac 로컬 SQLite 상태만 사용하고 원격 DB·CMS·마이크로서비스는 배제 | 가벼운 구현과 $0에 가까운 운영 | yes |
| 콘텐츠 검수 | 개인용이므로 별도 승인 상태 없이 생성 완료 후 바로 발행 | user decision 3C | yes |
| 생성 비용 | API key 없이 ChatGPT-managed Codex 인증과 로컬 scheduled task/non-interactive run 사용 | user decision 1A; official Codex auth/automation docs | yes |
| 에이전트 기기 | Mac `openkakao-cli` + launchd + `codex exec` | user decision 1A | yes |
| 시각 방향 | 밝은 코치 카드: 높은 가독성, 친근한 운동 정보 계층, 과도한 다크/공격적 표현 배제 | user decision 2C | yes |
| URL 공개 | 로그인 없는 공개 URL, 단 검색 노출은 기본 `noindex` | user decision 3A; public sharing with data minimization | yes |

## Findings (cited - path:lines)

- Repository is a bootstrap harness, not an existing application: `README.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/UI_GUIDE.md`.
- Attached CSV has 36 rows from 2026-08-10 through 2026-08-18 and 5 clear WOD posts. Their post times are 06:53, 06:55, 09:03, 17:09, and 06:37; all five embed the next workout date. A same-morning-only 09:00 job is therefore unsafe.
- The five WODs cover EMOM, team/for-time, AMRAP ladder, multi-block AMRAP, and team interval formats. Noise includes photos, join/leave notices, announcements, and ordinary chat.
- Kakao official docs expose user-driven Share, My Chatroom, and consented same-service friend messages, not a documented API to read an ordinary group room and post back automatically: https://developers.kakao.com/docs/en/kakaotalk-message/common and https://developers.kakao.com/docs/en/kakaotalk-message/rest-api.
- ChatGPT subscription and API billing are separate. The pilot therefore does not call the OpenAI API: it uses ChatGPT-managed Codex CLI authentication locally, accepting subscription rate limits and session availability rather than an API SLA: https://help.openai.com/en/articles/8156019-is-api-usage-included-in-chatgpt-subscriptions-even-if-i-have-a-paid-chatgpt-account and https://learn.chatgpt.com/docs/auth.
- YouTube Search API supports `order=viewCount` together with a movement-name query and `videoEmbeddable=true`. A live `q=Power Clean` test returned unrelated high-view music above exercise videos, so raw ordering requires a minimal normalized-title containment filter before selection: https://developers.google.com/youtube/v3/docs/search/list and https://developers.google.com/youtube/v3/docs/videos/list.
- Live stress testing of the proposed title-containment + Shorts exclusion rule showed it is not stable. `Row` selected three nursery-rhyme videos; `Snatch` promoted the official CrossFit movement video but filled slots 2-3 with unrelated gun-snatching clips; `Devil Press` returned three exercise demonstrations. The rule therefore passed only 1 of 3 additional movements and must not be approved as-is.
- A second live API stress test added `CrossFit` to each query while retaining the complete title/availability/duration filter. All six API calls returned HTTP 200. `CrossFit Devil Press` returned three directly relevant exercise videos; `CrossFit Snatch` returned the official foundational demonstration plus two genuine snatch competition/highlight videos; `CrossFit Row` still failed because its top results were a barbell-row tutorial, rowing-machine promotion, and competition footage rather than rowing instruction. Adding `CrossFit` is therefore a useful default disambiguator, but not a sufficient universal rule.
- CrossFit maintains an official movement and exercise-demonstration library, so it is the first source for standard CrossFit movement identity and mechanics: https://www.crossfit.com/crossfit-movements and https://www.crossfit.com/faq/exercises.
- YouTube view counts for Shorts changed in 2025 and are not directly comparable with ordinary instructional-video views, so supplementary candidates exclude Shorts/very short clips before ranking: https://developers.google.com/youtube/v3/docs/videos.
- Cloudflare Workers offers a free request tier and Cron Triggers, making it a plausible low-cost single-deployment target; Cron is UTC: https://developers.cloudflare.com/workers/platform/pricing/ and https://developers.cloudflare.com/workers/configuration/cron-triggers/.
- UI research recommends content-first, high-contrast, 16px+ mobile reading, visible focus, 44px targets, reduced motion, and a greenfield `DESIGN.md` + primitive showcase before screens.
- `JungHoonGhae/openkakao-cli` is an active macOS agent/CLI path. Its current recommended path is Accessibility-based `ax-watch`, `ax-read`, and allowlisted `local-send`; its README warns that recent KakaoTalk builds broke server login and local DB key derivation: https://github.com/JungHoonGhae/openkakao-cli.
- Live GitHub verification on 2026-08-18: `openkakao-cli` had 112 stars, 36 forks, and a 2026-07-25 latest push; `silver-flight-group/kakaocli` had 139 stars but its DB-based path predates the later key-breakage finding; `bssm-oss/kakao-talk-auto-bot` had 76 stars and a 2026-06-08 latest push.
- Android Kakao bots commonly use `NotificationListenerService` to receive KakaoTalk notification text and `RemoteInput`/`PendingIntent` to reply into the notification's originating room. Concrete implementations include https://github.com/wnduqrla/NotificationBot and https://github.com/bssm-oss/kakao-talk-auto-bot.
- ChatGPT-managed Codex auth is available to the desktop app and CLI for subscription access, while API-key auth is separately usage-billed: https://learn.chatgpt.com/docs/auth.
- ChatGPT desktop scheduled tasks can run against local projects when the Mac is on and the app is running, and `codex exec` supports scheduled jobs plus structured output while reusing saved CLI auth: https://learn.chatgpt.com/docs/automations and https://learn.chatgpt.com/docs/non-interactive-mode.

## Decisions (with rationale)

- Do not plan private Kakao protocol access or chat database scraping. The selected unattended desktop automation is restricted to pinned `openkakao-cli` Accessibility commands and one exact room allowlist.
- Separate deterministic parsing from editorial content. Known movements resolve from a versioned catalog; an unknown movement must resolve to schema-valid, source-backed content or publication stops and records the reason locally.
- Treat beginner/intermediate/advanced as different coaching emphasis within the same factual movement entry, not three independently generated articles.
- Resolve WOD aliases to a canonical English movement name. If the CrossFit Movement Library has an exact or explicitly mapped entry, pin its embedded video as slot 1 and retain the CrossFit source URL.
- Keep the API mechanics that were verified live: on a cache miss, use one `search.list` request with `order=viewCount`, `type=video`, `videoEmbeddable=true`, and `maxResults=50`, followed by one batched `videos.list` request; re-sort by the current numeric `statistics.viewCount` and cache the result.
- Reject the previously proposed raw-name relevance rule as insufficient: normalized title containment plus Shorts/very-short exclusion cannot disambiguate generic movement names such as `Row` or `Snatch`. Use the catalog-backed search-name rule below instead.
- Separate parsing aliases from YouTube search disambiguation. Chat abbreviations and variants such as `HSPU`, `TTB`, and `DB Snatch` first resolve to full canonical names (`Handstand Push-Up`, `Toes-to-Bar`, `Dumbbell Snatch`). Every catalog entry may then optionally define `youtube_search_name`; the selector uses that value when present, otherwise `CrossFit <canonical movement>`. This is data, not a Row-specific code branch.
- Seed obvious semantic collisions conservatively: `Row` -> `CrossFit Rowing`; generic `Snatch` -> `CrossFit Barbell Snatch`; generic `Clean` -> `CrossFit Barbell Clean`; generic `Press` -> `CrossFit Shoulder Press`. Already-specific movements such as `Power Clean`, `Squat Snatch`, and `Dumbbell Snatch` use the default query.
- Accept supplementary YouTube videos only when duration is strictly greater than 30 seconds and strictly less than 5 minutes. Continue excluding titles containing Shorts, non-public/unprocessed/non-embeddable videos, and titles lacking the canonical movement or approved title alias.
- Apply the same strict `(30s, 5m)` duration and availability rules to catalog-pinned official videos. If an official video fails, keep the official source link but do not embed the video.
- Build exactly up to three unique slots: official CrossFit first when present, then the highest-ranked YouTube candidates until three; if no official video exists, use the top three filtered YouTube candidates. Cache the selected IDs and ranking metadata for 30 days so repeated WODs are stable and free of repeated searches.
- If an embed later fails, hide that card and keep the remaining videos plus the CrossFit source link when available. Do not run a live fallback search during page viewing.
- Use a content-first mobile page: workout overview first, then format glossary, intent/scaling, movement cards, level tabs/segmented control, video, muscles/notes, and source/safety footer.
- Replace the earlier "no unofficial automation" assumption with a controlled personal-agent boundary: Accessibility/notification automation is allowed, but private Kakao server protocol writes, patched clients, rooted DB extraction, and credential replay remain excluded.
- Because this is a single-user service, generated content publishes without a reviewer state. Failed schema validation, unknown movement parsing, duplicate WODs, or deployment failure still stop publication automatically; fewer than three valid videos does not block the page.
- Pin the Kakao adapter to `openkakao-cli` v1.7.1 for implementation and verify its SHA during setup; use only `ax-watch`, `ax-read`, and allowlisted `local-send`, not server login or local DB decryption.
- Use event-driven ingestion and a 09:10 KST delivery rule. A WOD received before 09:10 on its workout date is delivered at 09:10; a later WOD is delivered immediately after successful publication; a prior-evening WOD waits for the workout date. This matches the observed 09:03 and 17:09 posts.
- Use a lightweight single-user architecture: Python orchestration and SQLite state locally; ChatGPT-authenticated `codex exec --output-schema` for structured content; Astro with minimal client JavaScript for the public page; Cloudflare Pages free hosting; launchd for watcher and recovery jobs.
- Bright coach-card UI direction: mobile-first overview card, format explanation, workout timeline, level selector, movement cards, approved video embed, muscles/cues/scaling, and compact source/safety footer. Create `DESIGN.md` and a primitive showcase before product screens.
- Metis gap decisions folded into the plan: exact-room identity fails closed; workout date is the logical document key and body hash is a revision; corrections reuse one URL and at most one correction notice; unknown catalog movement stops; Mac launchd owns watcher plus five-minute reconciliation and bounded KST cutoff recovery; secrets load from Keychain only; parsed Kakao text is an untrusted data envelope; YouTube degrades fresh cache -> stale compatible cache -> official link/no embeds; Pages direct upload must verify the public revision marker before send; analytics are deferred.

## Scope IN

- One box, one Korean-language daily WOD page flow.
- Personal-agent WOD ingestion through the selected macOS Accessibility path, plus deterministic parsing and deduplication.
- Daily content with beginner/intermediate/advanced guidance and automatic schema/safety-boundary checks.
- Curated movement glossary and embedded video catalog.
- Responsive public page, automatic Cloudflare Pages publication, and one allowlisted Kakao `local-send` URL delivery.
- $0/near-$0 pilot using ChatGPT-managed Codex subscription auth, with an explicit optional paid-API upgrade boundary.
- Analytics are deferred for the personal MVP.

## Scope OUT (Must NOT have)

- Private Kakao server protocol writes, patched clients, rooted DB extraction, credential replay, or unrestricted multi-room automation.
- Medical advice, injury diagnosis, personalized load prescription, or generated claims that exceed the source-backed coaching schema. General movement cues may auto-publish only inside that schema.
- Relevance/view-count blending, AI visual judging of technique, channel reputation databases, per-page live fallback searches, video download/rehosting, or modified/obscured YouTube player controls.
- Multi-box tenancy, payments, social feed, workout logging, leaderboards, native iOS/Android apps, or a general CMS in the first implementation.
- Names or unrelated messages from the attached real-name chat export in fixtures, source, logs, or product storage.

## Open questions

None. The selector uses a general optional catalog field rather than a Row-only branch, and the accepted YouTube duration window is locked to `(30s, 5m)`.

## Approval gate
status: execution-approved
approach: Build a local-first personal agent on the user's Mac. `openkakao-cli` v1.7.1 watches and reads only the allowlisted Kakao room through macOS Accessibility. A Python process detects/deduplicates WODs, invokes ChatGPT-authenticated `codex exec` with a strict output schema, assembles catalog-backed explanations and approved videos, builds an Astro page, deploys it to Cloudflare Pages, and sends one public URL through allowlisted `local-send`. launchd owns event watching, the 09:10 KST delivery rule, and bounded recovery. Human review is intentionally absent; schema/source/safety-boundary failures stop publication.
next-action: commit and push the planning baseline, then hand off `.omo/plans/crossfit-wod-companion.md` to a fresh GPT-5.6 Luna High session for `$start-work --ship`; Todo 1 performs the required project-harness migration before product implementation.
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->
