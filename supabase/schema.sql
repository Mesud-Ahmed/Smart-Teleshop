create extension if not exists pgcrypto;
create extension if not exists vector;

create table if not exists public.products (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  category text not null,
  cost_price numeric(12, 2) not null,
  sale_price numeric(12, 2) not null,
  stock_qty integer not null default 0,
  image_url text,
  fingerprint_text text,
  embedding_vector vector(768) not null,
  created_at timestamptz not null default timezone('utc', now())
);

create index if not exists products_embedding_vector_idx
on public.products
using ivfflat (embedding_vector vector_cosine_ops)
with (lists = 100);

create table if not exists public.sales (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references public.products(id) on delete cascade,
  quantity integer not null,
  sale_price numeric(12, 2) not null,
  cost_price numeric(12, 2) not null,
  profit numeric(12, 2) not null,
  created_at timestamptz not null default timezone('utc', now())
);

create index if not exists sales_created_at_idx
on public.sales (created_at desc);

create or replace function public.match_products(
  query_embedding vector(768),
  match_count int default 3
)
returns table (
  id uuid,
  name text,
  category text,
  sale_price numeric,
  stock_qty integer,
  image_url text,
  similarity float
)
language sql
as $$
  select
    p.id,
    p.name,
    p.category,
    p.sale_price,
    p.stock_qty,
    p.image_url,
    1 - (p.embedding_vector <=> query_embedding) as similarity
  from public.products p
  order by p.embedding_vector <=> query_embedding
  limit match_count;
$$;
