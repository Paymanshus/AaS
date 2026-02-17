# AaS MVP Plan: Minimal, Viral, Python-First

## Brief Summary
- Build AaS as a chat-first web app where humans configure personas once, start arguments in under 60 seconds, and watch agents argue live with replay/share parity.
- Use `Next.js + Vercel` for the viral UX surface, and `FastAPI + LangGraph + Dramatiq + Redis + Supabase` for Python-first orchestration and persistence.
- Optimize MVP for virality and learning: real-time token streaming, event-driven workers, badge moments, and a “Spotify Wrapped”-style post-argument recap.
- Ship monetization-ready limits (`3 starts/account`) without payments in MVP; prioritize growth loops and share mechanics.

## Product Scope (MVP)
- `In scope`: login, create argument, invite/join, persona setup, ready/start, live stream, replay, wrapped recap, badges, public share link.
- `In scope`: initiator-owned global controls only, participant-owned stance/points/red lines only.
- `Out of scope`: voice/video, long-term personality profiling, payment checkout, advanced moderation appeals, team/org features.
- `Out of scope`: WebRTC media transport; text streaming uses WebSockets (and optional SSE for spectators).

## User Experience and Screens
- `Landing`: logo, one-line hook, single large CTA (`Start an Argument`), login required.
- `Home`: `Create New Argument` CTA, active arguments, past arguments, credit count (`3 max started`).
- `Create Flow` (target <= 60 seconds): topic + global controls + invite generation.
- `Join Flow`: participant sets stance, exactly 3 defend points, optional red lines, persona preset selector.
- `Live Argument`: single-column chat stream, left/right agent bubbles, typing animation, meta beats, badge drops.
- `Replay`: exact same UI and message order as live, scrub by turn markers, share CTA.
- `Wrapped`: fun post-match report card with stats, quotes, overlap, momentum shifts, badges.

## Global Controls (Initiator Only, Decision Complete)
- `argument_composure` slider `0..100`, labels shown as endpoints only: `Civil but ruthless` to `Spicy but not unhinged`.
- `argument_shape` enum: `QUICK_SKIRMISH`, `PROPER_THROWDOWN`, `SLOW_BURN`.
- `win_condition` enum: `BE_RIGHT`, `FIND_OVERLAP`, `EXPOSE_WEAK_POINTS`, `UNDERSTAND_OTHER_SIDE`.
- `guardrails` booleans: `no_personal_attacks`, `no_moral_absolutism`, `no_hypotheticals`, `steelman_before_rebuttal`, `stay_on_topic`.
- `audience_mode` boolean enabling reactions, badge announcements, and public-share prompts.
- `pace_mode` enum: `FAST`, `NORMAL`, `DRAMATIC`; controls artificial pause ranges in stream delivery.
- `evidence_mode` enum: `FREEFORM`, `RECEIPTS_PREFERRED`; in receipts mode each turn must include at least one concrete claim anchor.

## Argument Shape Defaults
- `QUICK_SKIRMISH`: max 8 turns, target 80-140 tokens/turn, best-share default.
- `PROPER_THROWDOWN`: max 14 turns, target 120-180 tokens/turn.
- `SLOW_BURN`: max 10 turns, target 180-300 tokens/turn.
- Hidden phase progression is always enabled: `OPENING`, `ESCALATION`, `RESOLUTION`.

## Agent Architecture (LangGraph)
- One participant agent per participant; each agent is a LangGraph node invoked in alternating turns.
- One referee agent runs post-conversation only and creates wrapped JSON + short summary text.
- One badge agent runs after each finalized turn and may award zero or one badge.
- End condition is hybrid and deterministic: stop on max turns OR both active agents emit `done_signal=true` twice in a row OR stagnation detector triggers twice.
- Stagnation detector: embedding similarity on adjacent turns > threshold and no new claim IDs introduced.
- Badge gating: confidence threshold + cooldown window + max badges per argument to avoid always-on badge spam.

## Real-Time and Messaging Design
- Primary live transport is WebSocket from frontend to FastAPI gateway (`/ws/arguments/{id}`).
- Worker streams token events into Redis Pub/Sub; API gateway fans out to connected sockets.
- Optional spectator fallback is SSE (`/sse/arguments/{id}`) for read-only public viewers.
- Webhooks are used for external side effects only: share-card rendering pipeline and optional social posting integrations.
- Replay is event-sourced from persisted turn events so live and replay are visually identical.

## Data Model (Supabase Postgres)
- `users`: Supabase Auth user profile and handle.
- `personas`: reusable persona templates (`name`, `stance_style`, `points_default`, `red_lines_default`, `owner_user_id`).
- `arguments`: topic, creator, controls, status, phase, turn counters, shape config, audience flags.
- `argument_participants`: user, persona snapshot JSON, ready state, seat order.
- `argument_invites`: signed token, role (`participant` or `spectator`), expiry, usage.
- `turns`: argument id, turn index, speaker id, content, phase, metrics, model metadata.
- `turn_events`: token/meta/badge events with sequence numbers for replay parity.
- `badges_awarded`: turn id, badge key, reason, confidence.
- `argument_reports`: wrapped JSON blob, highlights, share assets metadata.
- `credit_ledger`: per-user credit deltas, reason, resulting balance.
- `audience_reactions`: optional reaction events keyed by argument and timestamp.

## Public APIs, Interfaces, and Types
- `POST /v1/arguments`: create argument with global controls.
- `POST /v1/arguments/{id}/invites`: create participant/spectator links.
- `POST /v1/arguments/{id}/join`: consume invite and attach user seat.
- `PUT /v1/arguments/{id}/participants/me/persona`: submit persona snapshot for this argument.
- `POST /v1/arguments/{id}/ready`: mark participant ready.
- `POST /v1/arguments/{id}/start`: validates min 2 ready and enqueues run job.
- `GET /v1/arguments/{id}`: argument state + participants + controls.
- `GET /v1/arguments/{id}/turns`: finalized turns for replay bootstrap.
- `GET /v1/arguments/{id}/report`: wrapped report payload.
- `WS /v1/arguments/{id}/stream`: token/meta/badge/state events.
- `SSE /v1/arguments/{id}/spectate`: optional read-only stream.
- `Event type contract`: `turn.token`, `turn.final`, `turn.meta`, `badge.awarded`, `phase.changed`, `argument.completed`, `error`.
- `Type additions`: `ArgumentControls`, `PersonaSnapshot`, `TurnEvent`, `WrappedReport`, `BadgeAward`, `CreditBalance`.

## Queueing and Async Jobs (Learning-Focused)
- Use Dramatiq with Redis broker for Python-native async jobs.
- Queues: `debate_run`, `postprocess`, `media`, `notifications`, `dead_letter`.
- `debate_run` job owns the LangGraph turn loop and emits stream events.
- `postprocess` runs referee summary and computes share-ready highlights.
- `media` generates OG/share images asynchronously.
- Reliability concepts included: idempotency key per argument start, retry backoff, dead-letter inspection, dedupe guard on start calls.
- Observability concepts included: job duration histogram, queue depth gauge, token throughput, socket fanout count.

## Viral Mechanics (Useful + Quirky)
- Auto-generated argument title and subtitle optimized for share cards.
- “Heat meter” and “momentum shift” meta events shown sparingly in live chat.
- Quote clipping button on each finalized turn for one-click share image generation.
- Wrapped report sections: `Who cooked`, `Best receipts`, `Most stubborn point`, `Unexpected common ground`.
- Public share modes: `participants only` link and `audience` link with reaction rail when enabled.
- Tone guide in prompts/UI: self-aware, slightly unhinged, never preachy, never corporate.

## Safety, Abuse, and Cost Guardrails
- Hard caps by shape on max turns and max tokens per turn.
- One credit deducted only when argument transitions to `RUNNING`.
- Per-user concurrent argument starts limited to prevent API burn.
- Basic moderation filter on generated output before broadcast; flagged turns are replaced with safe fallback text.
- Invite links are signed, scoped, expiring, and single-role.
- RLS policies enforce ownership for creation/edit and role-based read access.

## Tech Stack and Deployment (Concrete)
- Frontend: `Next.js (App Router)`, `TypeScript`, `Tailwind CSS`, `Framer Motion`, `Supabase JS auth`.
- Backend API: `FastAPI`, `Pydantic v2`, `SQLAlchemy async`, `Redis asyncio`, `LangGraph`.
- Worker: `Dramatiq` process sharing backend codebase and models.
- Storage/Auth: `Supabase Postgres + Supabase Auth + Supabase Storage`.
- Hosting: `Vercel` for web, `Fly.io` or `Railway` for API/worker, managed `Redis` provider.
- CI: GitHub Actions for tests, type checks, lint, and migration checks.

## Implementation Plan (Execution Order)
- Phase 1: scaffold monorepo (`apps/web`, `apps/api`, `apps/worker`), auth, DB schema, basic dashboard and credit ledger.
- Phase 2: create/join/ready/start API flow, persona snapshots, invite token model, minimal live page shell.
- Phase 3: LangGraph turn loop with participant agents, hidden phase progression, deterministic end rules, finalized turn persistence.
- Phase 4: WebSocket streaming + Redis Pub/Sub fanout + replay parity using `turn_events`.
- Phase 5: referee wrapped generator + badge agent + share card pipeline + public audience links.
- Phase 6: polish viral UX copy/motion, harden rate limits and retries, run load and E2E tests, deploy.
- Phase 7: soft launch with invite-only flag and telemetry dashboard for cost/retention/share rates.

## Test Cases and Scenarios
- `Setup speed`: median user can create and share an argument in under 60 seconds.
- `Readiness gate`: start fails until minimum two participants are ready.
- `Credit correctness`: credit deducted exactly once per started argument; retries do not double-charge.
- `Realtime correctness`: live token stream order equals persisted replay order.
- `Termination correctness`: each shape ends at configured rules with no infinite loops.
- `Badge behavior`: no badge when confidence below threshold; cooldown and max count respected.
- `Referee output`: wrapped JSON always includes required sections and at least one highlight quote.
- `Access control`: spectators cannot mutate; non-members cannot read private arguments.
- `Failure recovery`: worker crash resumes safely or marks argument failed with retry path.
- `Load target`: 100 concurrent spectators on one argument with acceptable latency and no dropped final turns.

## Explicit Assumptions and Defaults
- Default model provider is OpenAI-compatible API; participant/referee use mid-tier model, badge uses cheaper model.
- Payments are not in MVP; users start with exactly 3 argument credits and no auto-top-up.
- Minimum participants is 2, maximum for MVP is 4 to contain prompt and cost complexity.
- Public audience sharing is opt-in via `audience_mode`; private participant links remain default.
- WebRTC is intentionally excluded from MVP since text real-time needs are fully met by WebSocket/SSE.
- Persona profile is snapshot-per-argument; editing a base persona does not mutate in-progress arguments.
