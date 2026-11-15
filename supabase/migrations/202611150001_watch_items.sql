-- Scheduled retrieval: what each public source listed, and what changed between runs.
-- Observations only. Nothing here alters research records, awards or lighting dollars.
create table if not exists lsi.watch_items (
  source text not null, item_key text not null,
  payload jsonb not null, payload_hash text not null, lighting boolean not null default false,
  first_seen_at timestamptz not null default now(), last_seen_at timestamptz not null default now(),
  primary key(source,item_key)
);
create table if not exists lsi.watch_events (
  id bigint generated always as identity primary key,
  run_id bigint references lsi.job_runs(id), source text not null, item_key text not null,
  action text not null check(action in ('new','changed')),
  lighting boolean not null default false, payload jsonb not null, old_payload jsonb,
  recorded_at timestamptz not null default now(),
  -- A listed file or notice is a lead to read, not a verified fact.
  reviewed boolean not null default false
);
create index if not exists watch_events_recent on lsi.watch_events(recorded_at desc);
do $$ declare t text; begin
  foreach t in array array['watch_items','watch_events'] loop
    execute format('alter table lsi.%I enable row level security',t);
    if exists(select 1 from pg_roles where rolname='anon') then execute format('revoke all on lsi.%I from anon',t); end if;
    if exists(select 1 from pg_roles where rolname='authenticated') then execute format('revoke all on lsi.%I from authenticated',t); end if;
  end loop;
end $$;
