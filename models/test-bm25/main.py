import bm25s

corpus = [
    "a cat is a feline and likes to purr",
    "a dog is the human's best friend and loves to play",
    "a bird is a beautiful animal that can fly",
]

corpus_tokens = bm25s.tokenize(corpus)
corpus_tokens

for p in corpus_tokens.vocab:
    token_id = corpus_tokens.vocab[p]
    print(f'{p=}: {token_id}')


avg_doc_length = sum([len(id) for id in corpus_tokens.ids]) / len(corpus_tokens.ids)
avg_doc_length
# %% 




retriever = bm25s.BM25(corpus=corpus)
retriever.index(corpus_tokens)

queries = ["man cannot fly", "man's best friend"]
for q in queries:
    print(f'{q=}')
    query_tokens = bm25s.tokenize(q)
    print(f'  {query_tokens=}')
    scores = retriever.retrieve(query_tokens, k=3)
    print(f'  {scores=}')

retriever.method

