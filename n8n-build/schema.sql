create table if not exists n8n_missed_calls (
  id bigint generated always as identity primary key,
  call_sid text not null unique,
  from_number text not null,
  to_number text not null,
  call_status text not null,
  text_sent boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists n8n_missed_calls_phone_created_idx on n8n_missed_calls (from_number, created_at desc);

create table if not exists n8n_sms_suppression (
  phone_number text primary key,
  reason text not null,
  source_message_sid text,
  created_at timestamptz not null default now()
);

create table if not exists n8n_missed_call_leads (
  id bigint generated always as identity primary key,
  phone_number text not null,
  name text not null,
  service_type text not null,
  address text not null,
  urgency_level text not null,
  created_at timestamptz not null default now()
);
