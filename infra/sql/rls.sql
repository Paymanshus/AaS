-- Supabase-oriented RLS starter policies for AaS tables.
-- Assumes auth.uid() maps to users.id.

alter table if exists public.arguments enable row level security;
alter table if exists public.argument_participants enable row level security;
alter table if exists public.turns enable row level security;
alter table if exists public.argument_reports enable row level security;

create policy if not exists arguments_creator_manage
on public.arguments
for all
using (creator_user_id = auth.uid()::text)
with check (creator_user_id = auth.uid()::text);

create policy if not exists participants_can_read_argument
on public.arguments
for select
using (
  exists (
    select 1 from public.argument_participants ap
    where ap.argument_id = arguments.id
      and ap.user_id = auth.uid()::text
  )
  or audience_mode = true
);

create policy if not exists participant_self_manage
on public.argument_participants
for all
using (user_id = auth.uid()::text)
with check (user_id = auth.uid()::text);

create policy if not exists participants_read_turns
on public.turns
for select
using (
  exists (
    select 1 from public.argument_participants ap
    where ap.argument_id = turns.argument_id
      and ap.user_id = auth.uid()::text
  )
);

create policy if not exists participants_read_reports
on public.argument_reports
for select
using (
  exists (
    select 1 from public.argument_participants ap
    where ap.argument_id = argument_reports.argument_id
      and ap.user_id = auth.uid()::text
  )
);
