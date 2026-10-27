-- Private server-side research store. No anonymous or authenticated browser access.
create schema if not exists lsi;
revoke all on schema lsi from public;
create table if not exists lsi.migrations (
  name text primary key, sha256 text not null, applied_at timestamptz not null default now()
);
create table if not exists lsi.releases (
  content_hash text primary key, build text not null, research_date text not null,
  git_sha text, imported_at timestamptz not null default now(), record_count integer not null,
  snapshot jsonb not null
);
create table if not exists lsi.record_versions (
  kind text not null, state text not null, record_key text not null,
  payload_hash text not null, payload jsonb not null,
  first_release text not null references lsi.releases(content_hash),
  first_seen_at timestamptz not null default now(),
  primary key(kind,state,record_key,payload_hash)
);
create table if not exists lsi.records (
  kind text not null, state text not null, record_key text not null,
  payload_hash text not null, payload jsonb not null,
  release_hash text not null references lsi.releases(content_hash),
  updated_at timestamptz not null default now(),
  primary key(kind,state,record_key)
);
create table if not exists lsi.change_events (
  id bigint generated always as identity primary key,
  release_hash text not null references lsi.releases(content_hash),
  kind text not null, state text not null, record_key text not null,
  action text not null check(action in ('added','changed','removed')),
  old_hash text, new_hash text, recorded_at timestamptz not null default now(),
  unique(release_hash,kind,state,record_key)
);
create table if not exists lsi.source_health (
  id bigint generated always as identity primary key,
  source_key text not null, url text not null, checked_at timestamptz not null default now(),
  status_code integer, outcome text not null, etag text, last_modified text,
  -- A successful HTTP response does not mean the source was read or facts refreshed.
  review_required boolean not null default true
);
create index if not exists source_health_due on lsi.source_health(source_key,checked_at desc);
create table if not exists lsi.job_runs (
  id bigint generated always as identity primary key,
  job text not null, started_at timestamptz not null default now(),
  finished_at timestamptz, status text not null, summary jsonb
);
-- Typed, derived views preserve complete original records and their evidence.
create or replace view lsi.sources with (security_invoker=true) as
select state, record_key as source_key, payload->>'title' as title,
       payload->>'url' as url, payload->>'basis' as basis, release_hash from lsi.records where kind='source';
create or replace view lsi.contracts with (security_invoker=true) as
select state, record_key as contract_id, payload->>'let' as letting_date,
       payload->>'cls' as classification, payload->>'award' as award_status,
       (payload->>'lowAmt')::numeric(20,2) as contract_low_bid_usd,
       (payload->>'l2')::numeric(20,2) as identified_lighting_usd,
       payload->>'awardNote' as award_evidence, payload, release_hash
from lsi.records where kind='contract';
create or replace view lsi.projects with (security_invoker=true) as
select state,record_key as project_id,payload,release_hash from lsi.records where kind='project';
create or replace view lsi.contacts with (security_invoker=true) as
select state,record_key as contact_id,payload,release_hash from lsi.records where kind='contact';
create or replace view lsi.manufacturer_evidence with (security_invoker=true) as
select state,payload,release_hash from lsi.records where kind='manufacturer_evidence';
do $$ declare t text; begin
  foreach t in array array['migrations','releases','record_versions','records','change_events','source_health','job_runs'] loop
    execute format('alter table lsi.%I enable row level security',t);
  end loop;
  if exists(select 1 from pg_roles where rolname='anon') then
    revoke all on schema lsi from anon;
    revoke all on all tables in schema lsi from anon;
  end if;
  if exists(select 1 from pg_roles where rolname='authenticated') then
    revoke all on schema lsi from authenticated;
    revoke all on all tables in schema lsi from authenticated;
  end if;
end $$;
