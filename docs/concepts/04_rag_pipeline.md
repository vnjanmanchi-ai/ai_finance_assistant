# 04 — The RAG pipeline (retrieval, at query time)

## The one-sentence version

"RAG pipeline" is the umbrella name for the whole process of taking a live user question, retrieving relevant chunks for it, and handing those chunks to the LLM to ground its answer — Retrieval-Augmented Generation.

## Why RAG exists at all

An LLM by itself only knows what it learned during training — it has no idea what's in your 10 knowledge base articles, and it can't be *certain* about specific facts (it might confidently state something subtly wrong). RAG fixes this by handing the LLM the actual source material at the moment it's asked a question, so it's writing an answer *from* real text in front of it, rather than purely from memory. This is also what makes source citations possible — we know exactly which chunks the LLM was given, so we can tell the user "sources: this article, this section."

## The retrieval half, step by step

This is the part that happens fresh, every single query — unlike chunking/embedding/indexing, which already happened once at build time (see `00_overview.md` if this distinction isn't clear yet):

1. User asks: *"What's the difference between a Roth and Traditional IRA?"*
2. That question gets embedded into a vector (same embedding model used on the knowledge base — see `01_embeddings.md`)
3. Azure AI Search compares that vector against all stored chunk vectors (see `03_indexing.md`) and returns the closest matches — in our config, `top_k: 4`
4. Those matching chunks (with their original text, not just vectors) come back as the retrieval result

## The augmented-generation half

Once we have the retrieved chunks, `base_agent.py` does three things before calling the LLM:

1. **Wraps** the chunks in explicit delimiters (`wrap_retrieved_context()` in `security.py`) so the LLM can tell "this is reference material" apart from "this is an instruction" — our defense against prompt injection
2. **Combines** the agent's system prompt + those wrapped chunks + the guardrail preamble into one system message
3. **Sends** that combined system message plus the user's actual question to the LLM

The LLM then writes its answer using both its general language ability *and* the specific facts sitting right in front of it in the retrieved chunks.

## Where this lives in our code

- `retrieve()` in `search_index.py` — does steps 1-4 above
- `retrieve_context()` in `base_agent.py` — calls `retrieve()` once per allowed category for that agent, caps the total at 4 chunks
- `run()` in `base_agent.py` — the full pipeline: safety check → retrieve → wrap → call LLM → add disclaimer → add citations → log → return

## A common misconception worth clearing up

RAG does not mean "the LLM searches the internet" or "the LLM has access to a database it can query on its own." The retrieval step happens entirely in *our* code, before the LLM is ever called. By the time the LLM sees anything, retrieval is already finished — the LLM is just given a chunk of text as part of its prompt, exactly the same as if you'd pasted that text into the message yourself. The LLM has no independent ability to "look something up" mid-answer; every fact it can draw on for this response was decided by our retrieval step beforehand.

## Why the agent-level category filter matters here specifically

Compare two agents making the exact same retrieval call machinery, with one difference: the Finance Q&A agent searches across all 4 knowledge base categories, while the Tax Education agent only searches `tax_advantaged_accounts`. Same pipeline, same code — the *scope* of what it's allowed to retrieve is what actually defines each agent's specialization. This is worth sitting with: a lot of what makes our "6 different agents" actually different from each other isn't different code, it's different configuration (different `kb_categories`, different system prompt, sometimes a different model) running through the identical `BaseAgent.run()` pipeline.
