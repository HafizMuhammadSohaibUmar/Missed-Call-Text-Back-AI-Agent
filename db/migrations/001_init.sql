create extension if not exists pgcrypto;

create table if not exists conversations (
    id               uuid primary key default gen_random_uuid(),
    phone_number     text not null,
    business_id      text not null,
    messages         jsonb not null default '[]'::jsonb,
    status           text not null default 'open',
    lead_extracted   boolean not null default false,
    created_at       timestamptz not null default now(),
    last_message_at  timestamptz not null default now()
);

create index if not exists idx_conversations_business_phone
    on conversations (business_id, phone_number, last_message_at desc);

create index if not exists idx_conversations_business_status
    on conversations (business_id, status, last_message_at desc);

create table if not exists suppression_list (
    business_id    text not null,
    phone_number   text not null,
    reason         text not null,
    created_at     timestamptz not null default now(),
    primary key (business_id, phone_number)
);

create table if not exists missed_calls (
    id                    uuid primary key default gen_random_uuid(),
    business_id           text not null,
    from_number           text not null,
    to_number             text not null,
    call_sid              text not null,
    text_sent             boolean not null default false,
    text_sent_at          timestamptz,
    duplicate_suppressed  boolean not null default false,
    created_at            timestamptz not null default now()
);

create unique index if not exists idx_missed_calls_business_call_sid
    on missed_calls (business_id, call_sid);

create index if not exists idx_missed_calls_business_from_created
    on missed_calls (business_id, from_number, created_at desc);

create table if not exists leads (
    id               uuid primary key default gen_random_uuid(),
    business_id      text not null,
    conversation_id  uuid not null references conversations(id) on delete cascade,
    phone_number     text not null,
    name             text not null,
    service_type     text not null,
    address          text not null,
    urgency_level    text not null,
    created_at       timestamptz not null default now()
);

create index if not exists idx_leads_business_created
    on leads (business_id, created_at desc);
