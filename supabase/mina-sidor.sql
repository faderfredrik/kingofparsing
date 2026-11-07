-- King of Parsing: tillägg för Mina sidor (profil, Tyck till och kontoradering).
-- Körs i Supabase → SQL Editor efter schema.sql. Innehåller inga hemligheter.

-- 1. Profil: lärosäte, kurs och högsta uppnådda titel.
create table if not exists public.profiles (
  user_id uuid primary key default auth.uid() references auth.users (id) on delete cascade,
  school text check (char_length(school) <= 120),
  course text check (char_length(course) <= 120),
  title smallint not null default 0,      -- högsta uppnådda titel (0–16), förloras aldrig
  king_at timestamptz,                    -- när Kungaprovet klarades
  updated_at timestamptz not null default now()
);
alter table public.profiles enable row level security;
drop policy if exists "Läsa egen profil" on public.profiles;
create policy "Läsa egen profil" on public.profiles for select to authenticated using (user_id = (select auth.uid()));
drop policy if exists "Skapa egen profil" on public.profiles;
create policy "Skapa egen profil" on public.profiles for insert to authenticated with check (user_id = (select auth.uid()));
drop policy if exists "Ändra egen profil" on public.profiles;
create policy "Ändra egen profil" on public.profiles for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
grant select, insert, update on public.profiles to authenticated;
revoke all on public.profiles from anon;

-- 2. Tyck till: kommentarer från användarna. Ägaren läser dem i Table Editor.
create table if not exists public.feedback (
  id bigint generated always as identity primary key,
  user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  created_at timestamptz not null default now(),
  text text not null check (char_length(text) between 1 and 200),
  name text check (char_length(name) <= 60),
  school text check (char_length(school) <= 120),
  may_quote boolean not null default false  -- användaren har godkänt att bli citerad på webbplatsen
);
alter table public.feedback enable row level security;
drop policy if exists "Läsa egna kommentarer" on public.feedback;
create policy "Läsa egna kommentarer" on public.feedback for select to authenticated using (user_id = (select auth.uid()));
drop policy if exists "Skicka kommentar" on public.feedback;
create policy "Skicka kommentar" on public.feedback for insert to authenticated with check (user_id = (select auth.uid()));
grant select, insert on public.feedback to authenticated;
revoke all on public.feedback from anon;

-- 3. Radera sitt konto. Svar, profil och kommentarer raderas automatiskt (on delete cascade).
create or replace function public.delete_my_account()
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  delete from auth.users where id = auth.uid();
end
$$;
revoke all on function public.delete_my_account() from public, anon;
grant execute on function public.delete_my_account() to authenticated;
