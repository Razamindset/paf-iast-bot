# PAF-IAST Knowledge Bot 🤖🎓

A streamlined Retrieval-Augmented Generation (RAG) chatbot designed specifically for answering questions about the Pak-Austria Fachhochschule (PAF-IAST) using Google Embeddings and Groq's Llama 3 LLM.

## Project Structure

```text
paf-iast-bot/
├── src/
│   ├── crawler_simple.py  # A focused, recursive HTML crawler & chunker
│   ├── embedder.py        # Connects to Google GenAI for text-embedding-004
│   └── database.py        # Supabase pgvector client with deduplication
├── ingest.py              # CLI tool: Scrape -> Embed -> Store in DB
├── chat.py                # CLI tool: The actual Chatbot Interface
├── example.env            # Environment variables template
└── requirements.txt       # Python dependencies
```

## Setup Instructions

### 1. Database Setup (Supabase)
Create a new Supabase project and execute the following SQL in the Supabase SQL Editor to initialize the vector database:

```sql
-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;

-- Create a table to store your documents
create table pafiast_documents (
  id bigserial primary key,
  url text,
  content text,
  metadata jsonb,
  embedding vector(768), -- Google embeddings are 768 dimensions
  chunk_hash text UNIQUE
);

-- Create a function to search for documents via cosine similarity
create or replace function match_documents (
  query_embedding vector(768),
  match_threshold float,
  match_count int
)
returns table (
  id bigint,
  url text,
  content text,
  metadata jsonb,
  similarity float
)
language sql stable
as $$
  select
    pafiast_documents.id,
    pafiast_documents.url,
    pafiast_documents.content,
    pafiast_documents.metadata,
    1 - (pafiast_documents.embedding <=> query_embedding) as similarity
  from pafiast_documents
  where 1 - (pafiast_documents.embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
$$;
```

### 2. Environment Configuration
1. Rename `example.env` to `.env`
2. Populate `.env` with your API keys:
   - `SUPABASE_URL` and `SUPABASE_KEY` (from Supabase Project Settings > API)
   - `GOOGLE_API_KEY` (from Google AI Studio)
   - `GROQ_API_KEY` (from Groq Console)

### 3. Installation
Ensure you are using your virtual environment, then install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

**Step 1: Build the Knowledge Base**
Run the ingestion pipeline to crawl the university website, split the data into chunks, create embeddings, and push everything to your Supabase Vector DB.
```bash
python ingest.py
```
*(Note: Duplicate paragraphs are automatically skipped via cryptographic hashing to save API costs and prevent database bloat.)*

**Step 2: Talk to the Bot**
Run the chatbot interface. It will convert your text to a vector, find the most relevant context in Supabase, and stream an answer via Llama 3!
```bash
python chat.py
```
