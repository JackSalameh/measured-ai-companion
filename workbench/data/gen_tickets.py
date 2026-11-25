"""P1 Helpdesk Assistant: seeded generator of fictional support tickets.
Output: out/tickets.csv. Planted for chapter 3: exact duplicate texts (resubmitted tickets) and missing channels."""
import csv
import datetime as dt
import pathlib

from rng import Rng

SEED, N, START = 3101, 600, dt.date(2026, 1, 1)
QUEUES = ["billing", "login", "shipping", "other"]
WEIGHTS = [0.32, 0.26, 0.27, 0.15]
TEMPLATES = {
    "billing": ["I was charged twice for invoice {n}", "Please refund order {n}", "The price on my last invoice is wrong",
                "My card payment for order {n} failed", "Can I get a receipt for {month}?", "Why was I billed in {month}?",
                "The discount code did not apply to order {n}", "Please change the billing address on my account"],
    "login": ["I cannot sign in since {month}", "The password reset email never arrives", "My account is locked",
              "The verification code is not accepted", "Two-factor login fails on my phone", "The app logs me out every few minutes",
              "I forgot the email address I used to log in", "Sign-in page shows error {n}"],
    "shipping": ["Where is parcel {n}?", "Tracking for order {n} has not moved", "The package arrived damaged",
                 "Please change the delivery address for order {n}", "Order {n} is missing an item", "The courier left my parcel outside",
                 "How long does delivery to {country} take?", "Can I collect order {n} from a store?"],
    "other": ["Do you have a plan for a team of {k}?", "Is there a tablet version of the app?", "Please delete my data",
              "Where is your privacy policy?", "Do you offer training for new users?", "The website is slow today",
              "Can I add a colleague to my account?", "Thank you, the problem is solved"],
}
MONTHS = ["January", "February", "March", "April", "May", "June"]
COUNTRIES = ["Canada", "Portugal", "Japan", "Kenya", "Chile", "Norway"]


def make():
    g = Rng(SEED)
    rows = []
    for i in range(N):
        q = g.weighted(QUEUES, WEIGHTS)
        day = START + dt.timedelta(days=g.index(181))
        month = MONTHS[g.index(day.month)]                 # a month up to the ticket's own month
        text = g.choice(TEMPLATES[q]).format(n=1000 + g.index(9000), month=month, country=g.choice(COUNTRIES), k=2 + g.index(20))
        channel = "" if g.chance(0.02) else g.weighted(["email", "chat", "phone"], [0.5, 0.35, 0.15])
        tier = g.weighted(["free", "pro", "team"], [0.55, 0.3, 0.15])
        rows.append([day.isoformat(), channel, tier, text, q])
    # resubmissions: 3% of tickets sent again with identical text, a few days later
    for i in range(int(0.03 * N)):
        d, ch, tier, text, q = rows[g.index(N)]
        rows.append([(dt.date.fromisoformat(d) + dt.timedelta(days=1 + g.index(4))).isoformat(), ch, tier, text, q])
    rows.sort(key=lambda r: r[0])
    return [[f"T{k + 1:04d}"] + r for k, r in enumerate(rows)]


def write(path):
    rows = make()
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["ticket_id", "created", "channel", "tier", "text", "queue"])
        w.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    print(write(pathlib.Path(__file__).parent / "out" / "tickets.csv"), "tickets")
