import bm25s

corpus = [
    "a cat is a feline and likes to purr",
    "a dog is the human's best friend and loves to play",
    "a bird is a beautiful animal that can fly",
]

corpus_tokens = bm25s.tokenize(corpus)
corpus_tokens

for p in corpus_tokens.vocab:
    print(f'{p=}: {corpus_tokens.vocab[p]}')


retriever = bm25s.BM25(corpus=corpus)
retriever.index(corpus_tokens)

queries = ["man cannot fly", "man's best friend"]
for q in queries:
    print(f'{q=}')
    query_tokens = retriever.get_tokens_ids(q.split(" "))
    print(f'  {query_tokens=}')
    scores = retriever.get_scores(query_tokens_single=query_tokens)
    print(f'  {scores=}')


