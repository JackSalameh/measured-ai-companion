"""WB1.1-a  Rules or learning?

A hand-written keyword router for support tickets.
A rule is one (keyword, label) pair; the first rule whose keyword appears in the
ticket text wins; a ticket that matches no rule gets the label "other".

The 40 tickets were used to write the rules. The 10 held-out tickets were
written before the rules were final and never used to change them.
Run:  python wb1_1_a_rules_or_learning.py
"""

TICKETS = [  # (text, true label)
    ("I was charged twice for my last invoice", "billing"),
    ("Please send me a refund for order 4471", "billing"),
    ("My invoice shows the wrong VAT number", "billing"),
    ("Why did the price go up this month?", "billing"),
    ("I want to cancel my subscription and stop payments", "billing"),
    ("The card payment failed but money left my account", "billing"),
    ("Can I get a receipt for last month?", "billing"),
    ("Discount code did not apply at checkout", "billing"),
    ("I paid yesterday and the order still shows unpaid", "billing"),
    ("Please update the billing address on my account", "billing"),
    ("I forgot my password and the reset email never arrives", "login"),
    ("My account is locked after three attempts", "login"),
    ("I cannot sign in with my phone number", "login"),
    ("Two-factor code is not accepted", "login"),
    ("How do I change my email address for login?", "login"),
    ("The app logs me out every few minutes", "login"),
    ("I do not receive the verification code", "login"),
    ("Please unlock my account", "login"),
    ("Password reset link has expired", "login"),
    ("Sign in page shows an error 500", "login"),
    ("Where is my parcel? Tracking has not moved for five days", "shipping"),
    ("The package arrived damaged", "shipping"),
    ("I need to change the delivery address", "shipping"),
    ("Delivery was promised for Monday and nothing came", "shipping"),
    ("Can I pick up my order at a store instead?", "shipping"),
    ("The courier left the parcel at the wrong door", "shipping"),
    ("My order is missing one item", "shipping"),
    ("How long does shipping to Canada take?", "shipping"),
    ("Tracking number does not work", "shipping"),
    ("Please reschedule the delivery to next week", "shipping"),
    ("Do you have a student plan?", "other"),
    ("I would like to speak to a manager about your service", "other"),
    ("Your website is very slow today", "other"),
    ("Can I add a colleague as a team member?", "other"),
    ("Thank you, the problem is solved", "other"),
    ("Is there a mobile app for tablets?", "other"),
    ("I want to delete all my data", "other"),
    ("Where can I read your privacy policy?", "other"),
    ("Do you offer training for new users?", "other"),
    ("Can you recommend a plan for a team of five?", "other"),
]

HELD_OUT = [
    ("Money was taken from my card twice", "billing"),
    ("I am unable to access my profile with my credentials", "login"),
    ("My parcel has been sitting at the depot for a week", "shipping"),
    ("Do you give discounts to non-profits?", "other"),
    ("The refund for my canceled order has not arrived", "billing"),
    ("I never got the code to confirm my identity", "login"),
    ("The courier never rang the bell", "shipping"),
    ("Can I speak to someone about a complaint?", "other"),
    ("What is the cost of the yearly plan?", "other"),
    ("Please send the invoice to my accountant", "billing"),
]

RULES_V1 = [
    ("invoice", "billing"), ("refund", "billing"),
    ("password", "login"), ("locked", "login"),
    ("parcel", "shipping"), ("delivery", "shipping"),
]

# Written by looking at the misses of v1 on the 40 tickets, and nothing else.
RULES_V2 = RULES_V1 + [
    ("billing", "billing"), ("charged", "billing"), ("payment", "billing"),
    ("paid", "billing"), ("price", "billing"), ("subscription", "billing"),
    ("receipt", "billing"), ("discount", "billing"),
    ("sign in", "login"), ("login", "login"), ("logs me out", "login"),
    ("two-factor", "login"), ("verification", "login"), ("unlock", "login"),
    ("package", "shipping"), ("tracking", "shipping"), ("courier", "shipping"),
    ("shipping", "shipping"), ("pick up", "shipping"), ("missing", "shipping"),
]


def route(text, rules):
    t = text.lower()
    for keyword, label in rules:
        if keyword in t:
            return label
    return "other"


def accuracy(tickets, rules):
    hits = sum(route(text, rules) == label for text, label in tickets)
    return hits, len(tickets)


def main():
    print("WB1.1-a  Rules or learning?")
    print(f"{'version':<8}{'rules':>6}{'on the 40 used to write':>26}{'on 10 held out':>18}")
    for name, rules in (("v1", RULES_V1), ("v2", RULES_V2)):
        h1, n1 = accuracy(TICKETS, rules)
        h2, n2 = accuracy(HELD_OUT, rules)
        print(f"{name:<8}{len(rules):>6}{f'{h1}/{n1} = {h1 / n1:.3f}':>26}{f'{h2}/{n2} = {h2 / n2:.3f}':>18}")
    print("\nv2 on the held-out tickets (wrong answers only):")
    for text, label in HELD_OUT:
        guess = route(text, RULES_V2)
        if guess != label:
            print(f"  true={label:<8} rule said={guess:<8} | {text}")


if __name__ == "__main__":
    main()
