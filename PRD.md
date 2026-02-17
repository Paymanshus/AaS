# AaS MVP Product Requirements Document (PRD)

Assessment date: 2026-02-15  
Source plan: `PLAN.md`  
Implementation reviewed: `apps/api`, `apps/worker`, `apps/web`, `infra/sql`

## 1) Purpose

This PRD converts `PLAN.md` into explicit, testable MVP requirements and marks each one as:

- `DONE`: implemented in current codebase.
- `PARTIAL`: implemented but incomplete, weakly enforced, or not production-ready.
- `TODO`: not implemented yet.

The scope below is strictly MVP scope from `PLAN.md`.

## 2) How Much of PLAN.md Has Been Followed

Current implementation follows the MVP plan well at scaffold level, but not yet at hardening level.

- Product and API flow coverage: approximately 75% implemented (`DONE` + `PARTIAL`).
- Production-readiness and reliability coverage: approximately 35% implemented.
- Test coverage against MVP scenarios in `PLAN.md`: approximately 20% implemented.

High-level status:

| Area | Status |
|---|---|
| Login, create/join/ready/start flow | PARTIAL (flow exists, auth model is temporary) |
| Live streaming + replay parity foundation | PARTIAL (core implemented, not rigorously verified) |
| Worker orchestration + phase progression | PARTIAL (works as template pipeline, not full LangGraph agent system) |
| Wrapped report + badges | PARTIAL (implemented with heuristic logic) |
| Credits and monetization gate | PARTIAL (implemented, race/idempotency hardening missing) |
| Audience mode + reactions + spectator links | DONE/PARTIAL (implemented; share pipeline incomplete) |
| Safety/ACL/RLS/moderation | PARTIAL (basic checks only) |
| Viral mechanics and share assets | TODO/PARTIAL |
| Comprehensive MVP test suite | TODO (highest priority remaining item) |

## 3) MVP Requirements (Done + Remaining)

## A. UX, Accounts, and Core User Flows

### FR-001 Landing and primary CTA
- Requirement: show landing page with one-line hook and primary `Start an Argument` CTA.
- Acceptance criteria: `/` renders brand hook and CTA to app entry.
- Status: `DONE`
- Notes: Implemented in `apps/web/app/page.tsx`.

### FR-002 Login required before dashboard actions
- Requirement: user must be logged in before creating/managing arguments.
- Acceptance criteria: unauthenticated user navigating to `/app` is redirected to login.
- Status: `PARTIAL`
- Notes: enforced via localStorage-based client identity, not Supabase Auth/JWT.

### FR-003 Home dashboard with active/past arguments and credit count
- Requirement: dashboard shows active arguments, past arguments, and remaining starts.
- Acceptance criteria: data loaded from API and visibly split between active and past.
- Status: `DONE`
- Notes: `apps/web/app/app/page.tsx`, `GET /v1/me/arguments`.

### FR-004 Create flow <= 60 seconds (topic + controls + invite generation)
- Requirement: initiator can create argument and immediately generate invites.
- Acceptance criteria: topic + controls form, argument created, participant and spectator links generated.
- Status: `DONE`
- Notes: create + invite calls wired in dashboard.

### FR-005 Join flow with participant onboarding
- Requirement: invitee joins via token, then configures stance + exactly 3 defend points + optional red lines.
- Acceptance criteria: join token consumed (participant role), persona submission validates exactly 3 points.
- Status: `PARTIAL`
- Notes: persona setup exists, but no persona preset selector in UI.

### FR-006 Ready gate and initiator start action
- Requirement: participant marks ready; initiator starts only when ready criteria pass.
- Acceptance criteria: start rejected if <2 ready participants; accepted otherwise.
- Status: `DONE`
- Notes: `POST /ready` and `POST /start` gating implemented.

### FR-007 Live argument stream UI
- Requirement: single-column chat with left/right bubbles, typing behavior, meta updates, badge drops.
- Acceptance criteria: token events render drafts; final turns replace drafts; badge events shown.
- Status: `DONE`
- Notes: `apps/web/app/arguments/[id]/page.tsx` and websocket route.

### FR-008 Replay parity with live stream
- Requirement: replay should use same visual component model and ordering as live.
- Acceptance criteria: initial turn/event bootstrap from API + same bubble rendering path.
- Status: `PARTIAL`
- Notes: same page and feed are reused; explicit scrub-by-marker control is missing.

### FR-009 Wrapped recap screen content
- Requirement: post-argument report includes wrapped sections and highlights.
- Acceptance criteria: report endpoint returns structured wrapped object and summary.
- Status: `DONE`
- Notes: displayed on argument page after completion.

### FR-010 Public share mode links
- Requirement: participant and audience links can be generated when audience mode is enabled.
- Acceptance criteria: creator can issue invite links; spectators can read stream and replay/report.
- Status: `PARTIAL`
- Notes: links exist; share-card pipeline and clipping UX are not done.

## B. Global Controls and Debate Shape

### FR-011 Global control contract
- Requirement: support composure, shape, win condition, guardrails, audience mode, pace, evidence mode.
- Acceptance criteria: request schema validates all fields and stores controls on argument.
- Status: `DONE`

### FR-012 Guardrails influence generation behavior
- Requirement: control booleans should materially affect generation/moderation behavior.
- Acceptance criteria: each guardrail is enforced in runtime prompts and/or moderation policy.
- Status: `TODO`
- Notes: guardrails are stored but mostly not enforced; only generic moderation exists.

### FR-013 Shape defaults
- Requirement: shape presets map to turn/token defaults from plan.
- Acceptance criteria: QUICK/PROPER/SLOW map to defined max turns and token targets.
- Status: `DONE`

### FR-014 Token target enforcement
- Requirement: turn output should respect configured token range.
- Acceptance criteria: runtime truncates/retries or validates to keep turn length within shape limits.
- Status: `TODO`

### FR-015 Hidden phase progression
- Requirement: OPENING -> ESCALATION -> RESOLUTION progression throughout run.
- Acceptance criteria: phase transitions computed and emitted as events.
- Status: `DONE`

## C. API Contracts and Access

### FR-016 Create argument API
- Requirement: `POST /v1/arguments` creates argument and creator participant seat.
- Acceptance criteria: returns argument view with participant list and controls.
- Status: `DONE`

### FR-017 Invite API with role, expiry, and URL generation
- Requirement: creator can mint participant/spectator invite links.
- Acceptance criteria: returns token + role + URL + expiry.
- Status: `DONE`

### FR-018 Join API invite consumption semantics
- Requirement: participant invites are single-consumer; spectator invites are read-access tokens.
- Acceptance criteria: participant token cannot be reused by other user; seat limit enforced.
- Status: `PARTIAL`
- Notes: participant flow enforced; spectator usage tracking not enforced.

### FR-019 Persona snapshot API
- Requirement: participant submits argument-scoped persona snapshot before ready.
- Acceptance criteria: exactly 3 defend points required; persona locked after start.
- Status: `DONE`

### FR-020 Ready API
- Requirement: participant can mark ready only after persona exists.
- Acceptance criteria: ready rejected when persona missing.
- Status: `DONE`

### FR-021 Start API with idempotency
- Requirement: initiator start is deduplicated and charges one credit.
- Acceptance criteria: same idempotency key returns already-started response.
- Status: `PARTIAL`
- Notes: idempotency key check exists, but race safety is not strongly guaranteed.

### FR-022 Argument state retrieval API
- Requirement: fetch argument state + participants + controls with member/audience access checks.
- Acceptance criteria: member or valid audience token required.
- Status: `DONE`

### FR-023 Turns and events API
- Requirement: fetch finalized turns and full persisted event log for replay bootstrap.
- Acceptance criteria: ordered turns/events returned.
- Status: `DONE`

### FR-024 Report retrieval API
- Requirement: fetch wrapped report for eligible users.
- Acceptance criteria: returns report when available, 404 when not ready.
- Status: `DONE`

### FR-025 Reactions API
- Requirement: allow reactions in audience mode and emit reaction events.
- Acceptance criteria: reaction persisted and broadcast event emitted.
- Status: `DONE`

## D. Real-Time Transport and Event Model

### FR-026 WebSocket live stream gateway
- Requirement: stream historical + live events to authorized connections.
- Acceptance criteria: websocket sends backlog then pub/sub updates.
- Status: `DONE`

### FR-027 SSE spectator stream (optional)
- Requirement: read-only SSE stream for spectators when enabled.
- Acceptance criteria: endpoint gated by config + access checks.
- Status: `DONE`

### FR-028 Event contract parity
- Requirement: emit canonical event types (`turn.token`, `turn.final`, `turn.meta`, `badge.awarded`, `phase.changed`, `argument.completed`, `error`).
- Acceptance criteria: runtime emits required set during normal and failure flows.
- Status: `PARTIAL`
- Notes: core events exist; some advanced meta events from plan are missing.

### FR-029 Replay parity guarantee
- Requirement: event order in replay must equal live delivery order.
- Acceptance criteria: deterministic ordering and tested parity assertions.
- Status: `PARTIAL`
- Notes: event persistence exists, but parity is not yet covered by integration tests.

## E. Worker, Orchestration, and End Conditions

### FR-030 Queue topology
- Requirement: queues for `debate_run`, `postprocess`, `media`, `notifications`, `dead_letter`.
- Acceptance criteria: actors defined and routable.
- Status: `DONE`

### FR-031 Debate turn loop orchestration
- Requirement: worker executes alternating participant turns with event emission and persistence.
- Acceptance criteria: finalized turns stored, token and final events broadcast.
- Status: `DONE`

### FR-032 LangGraph-first participant agent architecture
- Requirement: participant agent logic represented as LangGraph flow (beyond simple scheduler utility).
- Acceptance criteria: debate reasoning and transitions are graph-based and explicit.
- Status: `PARTIAL`
- Notes: LangGraph currently used for schedule generation only.

### FR-033 End condition correctness
- Requirement: stop on max turns OR done-signal convergence OR stagnation threshold.
- Acceptance criteria: deterministic termination reason and no infinite loops.
- Status: `PARTIAL`
- Notes: implemented with heuristics (`done_hint`/similarity), not explicit model `done_signal` contract.

### FR-034 Stagnation detector fidelity
- Requirement: use similarity + claim novelty signal per plan.
- Acceptance criteria: detector references claim IDs and adjacent semantic similarity.
- Status: `PARTIAL`
- Notes: lexical cosine + local claim index used; no embedding/claim-id semantics.

### FR-035 Worker failure recovery
- Requirement: crash/retry behavior should avoid duplicate finalization and preserve consistency.
- Acceptance criteria: safe retry path, consistent status transitions, failure event path.
- Status: `TODO`

## F. Badges, Wrapped, and Viral Layer

### FR-036 Per-turn badge assignment with gating
- Requirement: zero/one badge per turn with confidence threshold, cooldown, and max badges.
- Acceptance criteria: threshold + cooldown + max count enforced.
- Status: `DONE`

### FR-037 Referee post-process wrapped generation
- Requirement: produce wrapped JSON + summary once run completes.
- Acceptance criteria: report row exists with required fields.
- Status: `DONE`

### FR-038 Wrapped section fidelity
- Requirement: report contains planned sections (`who cooked`, `best receipts`, `most stubborn point`, `unexpected common ground`) and usable highlights.
- Acceptance criteria: all sections non-empty when turns exist.
- Status: `DONE`

### FR-039 Share-card media pipeline
- Requirement: async media generation for share assets.
- Acceptance criteria: media worker produces persisted asset metadata.
- Status: `TODO`
- Notes: `media` actor exists as placeholder only.

### FR-040 Quote clipping and one-click share action
- Requirement: finalized turns can be clipped and sent to media/share pipeline.
- Acceptance criteria: UI control exists and backend endpoint/event supports clipping.
- Status: `TODO`

### FR-041 Heat/momentum live meta moments
- Requirement: sparing live meta events for virality and narrative pacing.
- Acceptance criteria: dedicated event payloads and UI rendering.
- Status: `TODO`

## G. Credits, Cost, and Abuse Controls

### FR-042 Startup credit ledger
- Requirement: new users seeded with 3 starts and balance tracked by ledger.
- Acceptance criteria: first-seen user receives seed entry and dashboard reflects balance.
- Status: `DONE`

### FR-043 Single credit debit on transition to RUNNING
- Requirement: debit exactly once per started argument.
- Acceptance criteria: retries/idempotent calls do not double-charge.
- Status: `PARTIAL`
- Notes: logical path exists; concurrency/race tests and locking are missing.

### FR-044 Concurrent-start limit per user
- Requirement: prevent API burn via per-user concurrent start cap.
- Acceptance criteria: start rejected when cap exceeded.
- Status: `TODO`

### FR-045 Moderation filter before broadcast
- Requirement: generated content moderated and replaced with safe fallback when flagged.
- Acceptance criteria: banned patterns trigger fallback text and flag metric.
- Status: `DONE`

### FR-046 Invite security model
- Requirement: invite links should be signed/scoped/expiring and role-safe.
- Acceptance criteria: cryptographically signed tokens or equivalent tamper-evident scheme.
- Status: `PARTIAL`
- Notes: random DB-backed tokens + expiry + role checks exist; no signature scheme.

### FR-047 Access control and RLS
- Requirement: ownership and role-based access enforcement for read/write paths.
- Acceptance criteria: API checks + DB-level RLS active in target DB.
- Status: `PARTIAL`
- Notes: API-level checks implemented; Supabase RLS SQL exists but not integrated/tested end-to-end.

## H. Tech Stack, Deployment, and Delivery

### FR-048 Monorepo structure and app split
- Requirement: `apps/web`, `apps/api`, `apps/worker` scaffolded and runnable.
- Acceptance criteria: each app has startup path and baseline docs.
- Status: `DONE`

### FR-049 Python-first backend stack
- Requirement: FastAPI + SQLAlchemy async + Dramatiq + Redis + LangGraph integrated.
- Acceptance criteria: runtime paths compile and execute with configured services.
- Status: `DONE`

### FR-050 Supabase Auth + Postgres-first deployment path
- Requirement: MVP should be deployable with Supabase Auth and Postgres.
- Acceptance criteria: auth verification and DB setup documented and wired.
- Status: `PARTIAL`
- Notes: local header auth + SQLite default used now; Supabase adaptation is incomplete.

### FR-051 CI baseline
- Requirement: CI runs web lint/build and API tests.
- Acceptance criteria: workflow file exists and runs these jobs.
- Status: `DONE`

### FR-052 Observability metrics
- Requirement: queue depth, token throughput, fanout count, job duration instrumentation.
- Acceptance criteria: metrics emitted and dashboardable.
- Status: `TODO`

### FR-053 Soft-launch controls and telemetry
- Requirement: invite-only flag and retention/share/cost telemetry for launch.
- Acceptance criteria: launch flagging + tracked KPIs.
- Status: `TODO`

## 4) Structural Quality Assessment (Current Implementation)

- Architecture is modular and coherent for an MVP scaffold (separate routes/services/runtime/workers/types).
- Contracts are generally clean: Pydantic schemas, typed frontend API layer, explicit event bus abstraction.
- Current biggest risk is not code organization; it is missing verification and production hardening.
- The codebase is suitable for iterative completion, but should not be treated as production-ready without the test requirement below.

## 5) Final High-Priority Requirement: Comprehensive Minimal MVP Test Suite (Release Gate)

### Requirement ID: TST-000 (Highest Priority, blocking release)
- Requirement: implement a complete but minimal test suite that covers every MVP subsystem and all critical plan scenarios before further feature expansion.
- Acceptance criteria:
  - All suites below exist and run in CI.
  - Every critical API path and worker path has at least one success test and one failure/edge test.
  - Live/replay parity, credit correctness, and access-control invariants are enforced by automated tests.
  - No manual-only release criteria remain for MVP core flows.

### A. Backend API Contract Tests (`pytest`, `httpx.AsyncClient` or FastAPI TestClient)

1. `TST-API-001` Health and app boot
- Setup: app startup with test DB URL.
- Assert: `/health` returns 200 and `{"status":"ok"}`.

2. `TST-API-002` Create argument with default controls
- Setup: authenticated headers (`x-user-id`, `x-user-handle`).
- Steps: POST `/v1/arguments`.
- Assert: argument created, creator participant seat_order=0, shape defaults match control.

3. `TST-API-003` Create argument with each shape
- Steps: create one per shape.
- Assert: `max_turns`, `target_min_tokens`, `target_max_tokens` match plan defaults.

4. `TST-API-004` Invite creation authorization
- Setup: creator user and non-creator user.
- Steps: non-creator attempts POST `/invites`.
- Assert: 403 for non-creator; 200 for creator.

5. `TST-API-005` Join participant token consumption semantics
- Steps: user A joins with participant token, user B reuses same token.
- Assert: user B receives conflict; participant seat created exactly once.

6. `TST-API-006` Join spectator access semantics
- Steps: spectator token used for read endpoints.
- Assert: can access `GET /arguments/{id}` and `GET /turns` only with valid audience token when not member.

7. `TST-API-007` Persona validation
- Steps: PUT persona with 2 points, then with 3 points.
- Assert: 422/400 on invalid; success on valid; ready reset on persona update.

8. `TST-API-008` Ready gating
- Steps: mark ready without persona; then with persona.
- Assert: failure then success.

9. `TST-API-009` Start readiness gate
- Steps: initiator starts with <2 ready participants.
- Assert: 400; start blocked.

10. `TST-API-010` Start authorization
- Steps: non-initiator start call.
- Assert: 403.

11. `TST-API-011` Idempotent start behavior
- Steps: same idempotency key repeated after start.
- Assert: second call returns `already_started`.

12. `TST-API-012` Report availability contract
- Steps: GET report before and after postprocess.
- Assert: 404 before, 200 after with required wrapped keys.

13. `TST-API-013` Reactions mode gating
- Steps: react when `audience_mode=false`, then true.
- Assert: 400 when disabled, success when enabled.

14. `TST-API-014` Access control negative tests
- Steps: unrelated user reads private argument without audience token.
- Assert: 403 across argument/turns/report endpoints.

### B. Credits and Ledger Invariant Tests

1. `TST-CRED-001` User bootstrap credits
- Assert: first request seeds `signup_seed` and `balance_after=3`.

2. `TST-CRED-002` Single debit on successful start
- Steps: complete valid start once.
- Assert: exactly one `argument_start` row and balance decremented by 1.

3. `TST-CRED-003` No debit on failed start
- Steps: start attempt fails readiness gate.
- Assert: no debit row added.

4. `TST-CRED-004` Idempotent replay no double charge
- Steps: valid start + repeated call with same idempotency key.
- Assert: only one debit row exists.

5. `TST-CRED-005` Concurrency safety (minimal race test)
- Steps: run two concurrent start requests.
- Assert: at most one transition/debit; if current code fails, test stays red until fixed.

### C. Worker Runtime and State Transition Tests (`pytest-asyncio`)

1. `TST-WORK-001` Minimum participants failure path
- Setup: argument running with <2 ready participants.
- Assert: status becomes `FAILED`; error event persisted.

2. `TST-WORK-002` Phase progression events
- Setup: deterministic turn text generation (monkeypatch `generate_turn_text`).
- Assert: phase transitions include opening/escalation/resolution in order.

3. `TST-WORK-003` Turn persistence contract
- Assert: each finalized turn has `turn_index`, speaker, content, metrics, metadata.

4. `TST-WORK-004` Stagnation stop path
- Setup: generator returns highly similar text repeatedly.
- Assert: early termination triggers before max turns.

5. `TST-WORK-005` Done-streak stop path
- Setup: generator emits repeated done-hint-compatible behavior.
- Assert: loop exits via done streak condition.

6. `TST-WORK-006` Moderation interception
- Setup: generated text contains banned term.
- Assert: persisted final text equals safe fallback and `metrics.was_flagged=true`.

7. `TST-WORK-007` Badge gating behavior
- Setup: crafted turns for high/low confidence and cooldown windows.
- Assert: no badge under threshold/cooldown; badge emitted when eligible.

8. `TST-WORK-008` Completion event and status
- Assert: final status `COMPLETED`, `ended_at` set, `argument.completed` event exists.

9. `TST-WORK-009` Postprocess upsert behavior
- Steps: run `run_postprocess` twice.
- Assert: single `argument_reports` row updated, not duplicated.

### D. Streaming and Replay Parity Tests

1. `TST-STREAM-001` WebSocket backlog delivery
- Setup: seed `turn_events`, open websocket.
- Assert: client receives backlog in ascending event id order before live events.

2. `TST-STREAM-002` WebSocket access control
- Assert: unauthorized websocket receives close code 4403.

3. `TST-STREAM-003` SSE enable/disable behavior
- Assert: when `SPECTATOR_SSE_ENABLED=false`, endpoint returns 404.

4. `TST-STREAM-004` Replay parity invariant
- Steps: capture websocket event sequence for a run and compare with stored `turn_events`.
- Assert: ordered `(event_type, turn_index, payload core fields)` sequence is identical.

Referential parity assertion shape:

```python
assert [
    (e["event_type"], e["turn_index"], core(e["payload"]))
    for e in websocket_events
] == [
    (r.event_type, r.turn_index, core(r.payload))
    for r in persisted_events
]
```

### E. Service Unit Tests (Fast, deterministic)

1. `TST-SVC-001` `shape_config` and `compute_phase`.
2. `TST-SVC-002` `cosine_similarity` edge cases (empty strings, punctuation-heavy inputs).
3. `TST-SVC-003` `maybe_award_badge` rule matrix.
4. `TST-SVC-004` `moderate_text` banned phrase and insult regex behavior.
5. `TST-SVC-005` `build_wrapped_report` non-empty and empty-turn branches with required keys.

### F. Frontend Minimal E2E Tests (Playwright recommended)

1. `TST-WEB-001` Login redirect guard
- Steps: clear localStorage, open `/app`.
- Assert: redirected to `/login`.

2. `TST-WEB-002` Create argument happy path
- Steps: login, create argument with controls.
- Assert: route to `/arguments/{id}`, topic visible.

3. `TST-WEB-003` Invite-join-persona-ready flow
- Steps: create participant invite, second browser context joins, sets persona, marks ready.
- Assert: participant ready count updates.

4. `TST-WEB-004` Start and live token rendering
- Steps: initiator starts argument in inline mode.
- Assert: typing draft appears then resolves into final turn bubble(s).

5. `TST-WEB-005` Badge and phase UI events
- Assert: phase label updates; badge chip renders when badge event arrives.

6. `TST-WEB-006` Audience reaction rail
- Setup: audience_mode on + spectator token.
- Steps: spectator reacts.
- Assert: reaction appears in live reaction list.

7. `TST-WEB-007` Wrapped report display
- Steps: wait for completion and report fetch.
- Assert: wrapped summary and required sections are shown.

8. `TST-WEB-008` Replay consistency check (minimal)
- Steps: reload completed argument page.
- Assert: finalized turns list is stable and ordered.

### G. Data and Security Tests

1. `TST-SEC-001` Seat limit enforcement
- Assert: joining above `MAX_PARTICIPANTS` returns conflict.

2. `TST-SEC-002` Persona lock after start
- Assert: persona update after RUNNING returns conflict.

3. `TST-SEC-003` Invite expiry enforcement
- Assert: expired invite returns gone/conflict path.

4. `TST-SEC-004` RLS migration smoke (for Postgres/Supabase env)
- Assert: policy SQL applies successfully and blocks unauthorized reads.

### H. Queue and Actor Wiring Tests

1. `TST-QUEUE-001` Actor enqueue path
- Assert: `start` calls enqueue `run_argument_actor` when not inline.

2. `TST-QUEUE-002` Postprocess chaining
- Assert: debate actor completion enqueues postprocess actor.

3. `TST-QUEUE-003` Fallback behavior when broker unavailable
- Assert: local inline fallback path still runs debate + postprocess.

### I. CI and Quality Gates

1. `TST-CI-001` CI must execute:
- API: `pytest -q` (including async/integration markers used in MVP).
- Web: lint + build.

2. `TST-CI-002` Add required failing-test policy
- For bug fixes, require at least one regression test before merge.

3. `TST-CI-003` Release gate
- Block MVP launch unless `TST-000` suite is green.
