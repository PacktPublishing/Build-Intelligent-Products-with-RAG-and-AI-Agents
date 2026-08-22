-- ResumeRoast Chapter 7
-- Initial production database schema
--
-- Stores completed roast history and daily usage counters.
-- The uploaded PDF and complete extracted resume text are not stored.

begin;

-- UUID generation is available on hosted Supabase projects, but declaring
-- the extension makes the dependency explicit and keeps the migration portable.
create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- Completed roast history
-- ---------------------------------------------------------------------------

create table if not exists public.roasts (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    created_at timestamptz not null default now(),

    user_intent text not null
        constraint roasts_user_intent_length
        check (
            char_length(btrim(user_intent)) between 1 and 1000
        ),

    score smallint not null
        constraint roasts_score_range
        check (score between 0 and 10),

    roast_text text not null
        constraint roasts_text_not_blank
        check (char_length(btrim(roast_text)) > 0),

    prompt_version text not null
        constraint roasts_prompt_version_not_blank
        check (char_length(btrim(prompt_version)) > 0),

    model_name text not null
        constraint roasts_model_name_not_blank
        check (char_length(btrim(model_name)) > 0)
);

comment on table public.roasts is
    'Completed ResumeRoast results owned by authenticated users.';

comment on column public.roasts.roast_text is
    'Generated critique. It may contain selected quotations from the resume.';

-- A user's history will normally be requested newest first.
create index if not exists roasts_user_created_at_idx
    on public.roasts (user_id, created_at desc);

-- ---------------------------------------------------------------------------
-- Daily application usage
-- ---------------------------------------------------------------------------

create table if not exists public.daily_usage (
    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    usage_date date not null
        default ((now() at time zone 'utc')::date),

    request_count integer not null default 0
        constraint daily_usage_request_count_nonnegative
        check (request_count >= 0),

    updated_at timestamptz not null default now(),

    primary key (user_id, usage_date)
);

comment on table public.daily_usage is
    'UTC daily request counters used to enforce per-user application quotas.';

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------

alter table public.roasts enable row level security;
alter table public.daily_usage enable row level security;

-- Remove policies first so the policy section can be rerun safely.
drop policy if exists roasts_select_own on public.roasts;
drop policy if exists roasts_insert_own on public.roasts;
drop policy if exists daily_usage_select_own on public.daily_usage;

-- A signed-in user may read only their own roast history.
create policy roasts_select_own
    on public.roasts
    for select
    to authenticated
    using ((select auth.uid()) = user_id);

-- A signed-in user may create only a roast owned by themselves.
create policy roasts_insert_own
    on public.roasts
    for insert
    to authenticated
    with check ((select auth.uid()) = user_id);

-- Users may inspect only their own usage record.
-- They do not receive direct INSERT or UPDATE permission because otherwise
-- they could lower their own request count. A controlled quota function will
-- perform those operations in a later migration.
create policy daily_usage_select_own
    on public.daily_usage
    for select
    to authenticated
    using ((select auth.uid()) = user_id);

-- ---------------------------------------------------------------------------
-- Table privileges
-- ---------------------------------------------------------------------------

-- Start from no privileges and grant only the operations the app needs.
revoke all on table public.roasts from public;
revoke all on table public.roasts from anon;
revoke all on table public.roasts from authenticated;

revoke all on table public.daily_usage from public;
revoke all on table public.daily_usage from anon;
revoke all on table public.daily_usage from authenticated;

grant select, insert on table public.roasts to authenticated;
grant select on table public.daily_usage to authenticated;

commit;
