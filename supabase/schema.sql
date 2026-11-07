-- King of Parsing: databas i Supabase.
-- Klistras in och körs i Supabase → SQL Editor. Filen innehåller inga hemligheter.
-- Lösenordet som låser upp appen läggs in separat av ägaren (se längst ned).

-- 1. Nyckeln till appen: en enda rad som bara inloggade användare får läsa.
create table if not exists public.app_secret (
  id int primary key default 1,
  password text not null,
  constraint app_secret_one_row check (id = 1)
);
alter table public.app_secret enable row level security;
drop policy if exists "Inloggade får läsa nyckeln" on public.app_secret;
create policy "Inloggade får läsa nyckeln" on public.app_secret
  for select to authenticated using (true);

-- 2. Varje svar som en användare lämnar.
create table if not exists public.answers (
  id bigint generated always as identity primary key,
  user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  created_at timestamptz not null default now(),
  form text not null,          -- den böjda formen, t.ex. ἐπηρώτησεν
  lemma text,                  -- uppslagsordet, t.ex. ἐπερωτάω
  expected text not null,      -- den godkända parsning som låg närmast svaret, t.ex. AAI3S
  answer text,                 -- användarens parsning
  ok boolean not null,         -- både parsning och uppslagsord rätt
  parse_ok boolean,
  lex_ok boolean,
  hint smallint not null default 0,  -- 0 ingen hjälp, 1 delarna, 2 delarna med etiketter
  book text
);
create index if not exists answers_user_time on public.answers (user_id, created_at);
alter table public.answers enable row level security;
drop policy if exists "Läsa egna svar" on public.answers;
create policy "Läsa egna svar" on public.answers
  for select to authenticated using (user_id = (select auth.uid()));
drop policy if exists "Spara egna svar" on public.answers;
create policy "Spara egna svar" on public.answers
  for insert to authenticated with check (user_id = (select auth.uid()));

-- 3. Totalt antal parsade ord, till räknaren på startsidan. Visar bara en siffra.
create or replace function public.total_parsed()
returns bigint
language sql
stable
security definer
set search_path = ''
as $$ select count(*) from public.answers $$;
revoke all on function public.total_parsed() from public;
grant execute on function public.total_parsed() to anon, authenticated;

-- 4. Rättigheter: inloggade får läsa nyckeln och läsa och spara sina egna svar (reglerna ovan begränsar vilka rader).
--    Den som inte är inloggad får ingenting.
grant select on public.app_secret to authenticated;
grant select, insert on public.answers to authenticated;
revoke all on public.app_secret from anon;
revoke all on public.answers from anon;

-- 5. Lösenordet läggs in av ägaren, inte här. Kör en egen fråga i SQL Editor:
--    insert into public.app_secret (id, password) values (1, 'DITT LÖSENORD')
--    on conflict (id) do update set password = excluded.password;
--    Lösenordet ska vara samma som du skriver när du kör scripts/build.py.
