# 01 — Embeddings

## The one-sentence version

An embedding turns a piece of text into a list of numbers (a vector) such that texts with similar *meaning* end up as similar *numbers* — even if they don't share any of the same words.

## Why this is useful

Computers can't compare "meaning" directly, but they're very good at comparing numbers. If "What's an ETF?" and "How do exchange-traded funds work?" get turned into two vectors that are numerically close to each other, we can find relevant knowledge base content by pure math (distance between vectors) instead of requiring the user's exact wording to match the article's exact wording.

## A concrete (simplified) picture

Imagine every chunk of text becomes a point in space. Chunks about similar topics cluster near each other:

```
                    "IRA basics"  •
                                    •  "401k basics"
                                  (tax-advantaged accounts cluster)


  "what is a stock" •
                        •  "what is a bond"
                            •  "what is an ETF"
                     (stocks/bonds/ETFs cluster)
```

A real embedding isn't 2 numbers — Azure's `text-embedding-3-small` model (the one in our `config.yaml`) produces **1536 numbers** per chunk. You can't visualize 1536 dimensions, but the "similar meaning = nearby points" idea is exactly the same, just in a space too large to draw.

## How we use it

1. **At build time**: every knowledge base chunk gets embedded once and stored (this is the expensive-ish, one-time cost).
2. **At query time**: the user's question gets embedded fresh, every single time. That question-vector is then compared against all the stored chunk-vectors to find the closest matches — that comparison is what "search" means in a vector search engine.

## Where this lives in our code

`src/rag/embedder.py` — two functions:
- `embed_texts(list_of_strings)` → calls Azure OpenAI once for a batch of chunks (used during ingestion)
- `embed_text(single_string)` → embeds one string (used for a live user question at query time)

Both call the same underlying model — `text-embedding-3-small`, set in `config.yaml` under `azure_openai.deployments.embedding` — which is what guarantees chunk-vectors and question-vectors live in the same comparable space. If you ever embedded chunks with one model and questions with a different model, the "distance" comparison would be meaningless — like comparing a distance measured in miles to one measured in kilometers without converting.

## What "distance" actually means here

The most common similarity measure is **cosine similarity** — it asks "do these two vectors point in the same direction," not "are they the exact same size." Azure AI Search handles this math internally when you search; we don't have to implement it ourselves, which is why `search_index.py`'s `retrieve()` function can just ask for "the k nearest neighbors" and get back the most relevant chunks.

## Common misconception to avoid

Embeddings are **not** a summary and they're **not** keywords. You can't look at a vector and read what it means — it's meaningless to a human directly. Its only purpose is being compared to other vectors. This is why we still store the original chunk *text* right alongside its vector (see `03_indexing.md`) — the vector is only used to *find* the right chunk; the actual text is what gets shown to the LLM and the user.
