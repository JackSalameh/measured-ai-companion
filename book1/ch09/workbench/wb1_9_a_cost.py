"""WB1.9-a  Token cost estimator.

Reads a usage file (one row per task: calls per month, input tokens, the part of the input that
is the same on every call and can be cached, output tokens) and a price table (USD per million
tokens for input, cached input and output, and the provider's minimum cacheable prompt length).
Prints the monthly cost of each task on each model, first with every input token at the full
input price, then with the cacheable part at the cached-input price where the price table gives
one and the cacheable part reaches the provider's minimum (blank minimum: none published).

    cost = calls x (input_tokens x input_price + output_tokens x output_price) / 1,000,000

What the estimate leaves out is printed at the end: read it before you trust the total.
Edit the two CSV files to model your own work. Only the standard library is used.
Run:  python wb1_9_a_cost.py [usage.csv] [prices.csv]
"""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
USAGE = HERE / "usage_helpdesk.csv"
PRICES = HERE / "prices_2026-11-22.csv"
M = 1_000_000


def read(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def call_cost(task, price, cached=False):
    """Cost in USD of one call. With cached=True the cacheable input tokens are billed at the
    cached-input price, if the price table has one and the cacheable part reaches the provider's
    minimum cacheable length; otherwise at the full input price."""
    n_in, n_cache, n_out = int(task["input_tokens"]), int(task["cacheable_input_tokens"]), int(task["output_tokens"])
    p_in, p_out = float(price["input_per_m"]), float(price["output_per_m"])
    p_cache = float(price["cached_input_per_m"]) if price["cached_input_per_m"] else p_in
    minimum = price.get("min_cacheable_tokens") or ""
    if minimum and n_cache < int(minimum):
        p_cache = p_in                     # below the provider's minimum: nothing is cached
    if cached:
        return ((n_in - n_cache) * p_in + n_cache * p_cache + n_out * p_out) / M
    return (n_in * p_in + n_out * p_out) / M


def monthly(tasks, price, cached=False):
    """Monthly cost of each task and the total."""
    per = {t["task"]: int(t["calls_per_month"]) * call_cost(t, price, cached) for t in tasks}
    return per, sum(per.values())


def output_share(tasks, price):
    """Share of the uncached monthly bill that pays for output tokens."""
    out = sum(int(t["calls_per_month"]) * int(t["output_tokens"]) * float(price["output_per_m"]) / M for t in tasks)
    return out / monthly(tasks, price)[1]


def main(usage=USAGE, prices=PRICES):
    tasks, table = read(usage), read(prices)
    print(f"WB1.9-a  usage: {pathlib.Path(usage).name}")
    print(f"         prices: {pathlib.Path(prices).name}")
    tok_in = sum(int(t["calls_per_month"]) * int(t["input_tokens"]) for t in tasks)
    tok_out = sum(int(t["calls_per_month"]) * int(t["output_tokens"]) for t in tasks)
    print(f"tokens per month: input {tok_in:,}, output {tok_out:,}")
    print()
    names = [t["task"] for t in tasks]
    print(f"{'model':<19}" + "".join(f"{n:>9}" for n in names) + f"{'total':>9}{'cached':>9}{'out':>6}")
    for p in table:
        per, tot = monthly(tasks, p)
        _, tot_c = monthly(tasks, p, cached=True)
        row = f"{p['model_id']:<19}" + "".join(f"{per[n]:>9.2f}" for n in names)
        print(row + f"{tot:>9.2f}{tot_c:>9.2f}{output_share(tasks, p):>6.0%}")
    print()
    print("USD per month. cached: cacheable input billed at the cached-input")
    print("price if it reaches the provider's minimum cacheable length")
    print("(OpenAI 1,024, Anthropic 512, Google 4,096 tokens; Mistral AI")
    print("publishes none). out: share of the uncached total paid for output.")
    print("Not counted: cache writes, retries, failed calls, reasoning tokens")
    print("billed as output, long-prompt surcharges, batch discounts, taxes,")
    print("and the time spent checking the answers.")


if __name__ == "__main__":
    main(*sys.argv[1:3])
