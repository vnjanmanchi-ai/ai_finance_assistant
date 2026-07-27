# 05 — Evaluation

## The one-sentence version

Evaluation is how you prove the RAG pipeline actually works well, instead of just assuming it does because the code runs without crashing.

## Why "it runs" isn't the same as "it works"

A RAG pipeline can run perfectly — no errors, fast response — and still be wrong in ways that are easy to miss:
- It might retrieve the *wrong* chunks (e.g. a diversification question pulls a bond-pricing chunk instead)
- It might retrieve the *right* chunks but the LLM still writes an answer that doesn't actually reflect them (this is called a **hallucination**, even in RAG — retrieval doesn't guarantee the LLM stays faithful to what it was given)
- It might work great on the 3 questions you happened to try manually, and fail on the 4th

Evaluation replaces "I tried a few questions and it seemed fine" with a repeatable, objective check.

## The two things worth actually measuring (not ROUGE — see below)

**1. Retrieval accuracy** — for a test question, did the pipeline retrieve the chunk(s) it *should have*? Since we control the knowledge base, we know the right answer: a question clearly about IRAs should retrieve chunk `kb-010`. This is simple to check and tells you if chunking/embedding/indexing are working correctly, independent of the LLM.

**2. Groundedness** — for a test question, does the LLM's final answer actually reflect what was in the retrieved chunks, or did it drift and add unsupported claims? This tests the "augmented generation" half separately from the "retrieval" half.

Keeping these two separate matters: if an answer is wrong, you want to know whether retrieval failed (wrong chunks were fetched) or generation failed (right chunks were fetched, but the LLM didn't use them faithfully) — they need completely different fixes.

## Why we're skipping ROUGE/NLTK specifically

ROUGE measures *word overlap* between a generated answer and a reference answer — it was built for summarization, not for checking factual accuracy. Two answers can say the same true thing in different words (low ROUGE score, but actually correct) or share lots of words while one is subtly wrong (high ROUGE score, but actually incorrect). For a financial-education RAG system, "did it retrieve the right source and stay faithful to it" is a much more direct, more honest question to ask than "does the wording resemble a reference answer" — so that's what our eval harness will check instead.

## What our Phase 9 eval harness will actually look like

1. **A small test set** — roughly 15-20 questions, one or two per knowledge base article, each tagged with the article/chunk it should retrieve. Example: `{"question": "What's a Roth IRA?", "expected_article": "kb-010"}`.
2. **Retrieval accuracy check** — for each test question, call `retrieve()` and check whether the expected article's chunks appear in the top results. This produces a simple percentage: "retrieved the right source in 18/20 test questions."
3. **Groundedness check** — for each test question, take the LLM's actual answer and the chunks it was given, and ask a second, cheap LLM call: *"Does this response's claims appear in this source text? Answer yes or no."* This is sometimes called "LLM-as-judge" — using a model to check another model's output against a specific, narrow yes/no question, rather than open-ended grading.
4. **Run this automatically** — as part of `pytest`, so it runs the same way our other tests do, and can be re-run every time the knowledge base or prompts change, to catch regressions.

## Where this will live in our code (not built yet)

`tests/test_rag_evaluation.py` (planned, Phase 9) — a test file that loads the test question set (probably `tests/eval_questions.json`), runs each question through `retrieve()` and through a full agent, and asserts retrieval accuracy and groundedness stay above a chosen threshold (e.g. 85%).

## The interview-ready way to describe this

*"Instead of a summarization metric like ROUGE, I evaluated the RAG pipeline on two things that actually matter for a knowledge-grounded system: retrieval accuracy against a labeled test set, and groundedness — whether the generated answer's claims are actually supported by what was retrieved."* That's a more precise, more defensible answer than "I used ROUGE scores," because it shows you understand *what* you're actually trying to verify, not just that you ran a standard metric.
