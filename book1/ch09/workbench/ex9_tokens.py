"""Chapter 9 example: the same text, two real tokenizers, two token counts.

Uses two tokenizers that ship inside the open-source package mistral-common (version 1.13.1):
an older SentencePiece tokenizer with a vocabulary of 32,000 tokens and the newer "Tekken"
tokenizer (file tekken_240911.json) with 131,072 tokens. Both come from the same company, so the
difference you see is caused by the tokenizer alone. Tokenizers of different providers differ
at least as much, and price lists are per token: a price per million tokens is only comparable
across providers once you know how many tokens each one counts for your own text.

Needs:  pip install "mistral-common[sentencepiece]==1.13.1"   (no network access at run time)
Run:    python ex9_tokens.py
"""
import os

TEXTS = {
    "English": "The invoice was paid on 14 March, three days after the due date.",
    "French": "La facture a été payée le 14 mars, trois jours après la date d'échéance.",
    "Numbers": "Total: 1,234,567.89 EUR; tax 20% = 246,913.58 EUR.",
    "Code": "def total(xs):\n    return sum(x['amount'] for x in xs)\n",
}


def tokenizers():
    import mistral_common
    from mistral_common.tokens.tokenizers.sentencepiece import SentencePieceTokenizer
    from mistral_common.tokens.tokenizers.tekken import Tekkenizer
    d = os.path.join(os.path.dirname(mistral_common.__file__), "data")
    return (SentencePieceTokenizer(os.path.join(d, "tokenizer.model.v1")),
            Tekkenizer.from_file(os.path.join(d, "tekken_240911.json")))


def counts():
    sp, tk = tokenizers()
    rows = []
    for name, text in TEXTS.items():
        a = len(sp.encode(text, bos=False, eos=False))
        b = len(tk.encode(text, bos=False, eos=False))
        rows.append((name, len(text), len(text.split()), a, b))
    return sp.n_words, tk.n_words, rows


def main():
    n_sp, n_tk, rows = counts()
    print(f"vocabulary sizes: SentencePiece v1 {n_sp:,}, Tekken {n_tk:,}")
    print(f"{'text':<9}{'chars':>6}{'words':>6}{'SP v1':>7}{'Tekken':>8}{'ratio':>7}")
    for name, c, w, a, b in rows:
        print(f"{name:<9}{c:>6}{w:>6}{a:>7}{b:>8}{a / b:>7.2f}")
    ta, tb = sum(r[3] for r in rows), sum(r[4] for r in rows)
    print(f"{'all':<9}{sum(r[1] for r in rows):>6}{sum(r[2] for r in rows):>6}{ta:>7}{tb:>8}{ta / tb:>7.2f}")


if __name__ == "__main__":
    main()
