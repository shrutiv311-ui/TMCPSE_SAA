-- ============================================================
-- Toastmasters Pune South East — Supabase Database Setup
-- Run this ONCE in Supabase → SQL Editor → New Query
-- ============================================================

-- 1. MEMBERS (you add rows manually via Table Editor)
create table if not exists members (
  id         bigint primary key generated always as identity,
  name       text not null,
  email      text,
  phone      text,
  join_date  date,
  active     boolean default true
);

-- 2. ATTENDANCE (auto-filled when members check in)
create table if not exists attendance (
  id         bigint primary key generated always as identity,
  date       date not null,
  timestamp  text,
  member_id  bigint references members(id),
  name       text,
  email      text
);

-- 3. GUESTS (auto-filled when guests register)
create table if not exists guests (
  id         bigint primary key generated always as identity,
  date       date not null,
  timestamp  text,
  name       text not null,
  phone      text,
  how_heard  text
);

-- 4. TODAY'S SPEAKERS (set by SAA in Admin Panel)
create table if not exists today_speakers (
  id           bigint primary key generated always as identity,
  date         date not null,
  speaker_name text not null,
  role         text
);

-- 5. FEEDBACK (submitted by members/guests)
create table if not exists feedback (
  id            bigint primary key generated always as identity,
  date          date not null,
  timestamp     text,
  user_id       text,
  user_name     text,
  speaker_name  text,
  speaker_role  text,
  feedback_text text
);

-- 6. VOTES
create table if not exists votes (
  id         bigint primary key generated always as identity,
  date       date not null,
  timestamp  text,
  user_id    text,
  user_name  text,
  category   text,
  nominee    text
);

-- 7. MEETING CONFIG (voting open/closed switch)
create table if not exists meeting_config (
  id    bigint primary key generated always as identity,
  key   text unique not null,
  value text
);

-- Seed the voting switch as closed
insert into meeting_config (key, value)
values ('VotingOpen', 'No')
on conflict (key) do nothing;


-- ============================================================
-- SECURITY: Allow the app's anon key to read/write all tables
-- (Supabase Row Level Security is off by default — this is fine
--  for a private club app. If you want RLS, enable it per table.)
-- ============================================================

-- Optional: Add some sample members to test with
-- (Replace with your real club members)
insert into members (name, email, phone, join_date, active) values
  ('Your Name Here',    'you@gmail.com',        '9999999999', '2024-01-01', true),
  ('Test Member Two',   'test2@gmail.com',       '8888888888', '2024-01-01', true);
