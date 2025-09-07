# events.py
import random

def deposit_event(bank):
    """Simulate a deposit by a customer."""
    amt = random.randint(100, 10000)
    # Pick an existing customer 50% of the time, else create new
    if bank.customers and random.random() < 0.5:
        cid = random.choice(list(bank.customers.keys()))
    else:
        cid = bank.new_customer()
    bank.deposit(amt, customer_id=cid)
    return f"Customer {cid} deposited ${amt:.2f}"

def withdraw_event(bank):
    """Simulate a withdrawal by a customer with available deposits."""
    eligible = [cid for cid, c in bank.customers.items() if c.get("deposit_balance", 0) > 0]
    if not eligible:
        return "No customers with deposits available for withdrawal."
    cid = random.choice(eligible)
    cust = bank.customers[cid]
    total = sum(d["amount"] for d in cust["deposits"])
    if total <= 0:
        return f"Customer {cid} has no funds to withdraw."
    amt = random.randint(1, int(total))
    success = bank.withdraw(amt, customer_id=cid)
    if success:
        return f"Customer {cid} withdrew ${amt:.2f}"
    else:
        return f"Withdrawal of ${amt:.2f} failed for customer {cid}."

def loan_request_event(bank, approval_callback=None):
    """
    Simulate a loan request.
    If approval_callback is provided, it will be called with
    (customer_id, amount, years, rate, credit_score) and should return:
    'accept', 'decline', or ('counter', new_amt, new_yrs)
    """
    amt = random.randint(500, 20000)
    yrs = random.randint(1, 20)
    cid = bank.new_customer()
    score = bank.customers[cid]["credit_score"]

    # Determine default interest rate
    if score < 580: rate = 0.10
    elif score < 670: rate = 0.08
    elif score < 740: rate = 0.06
    elif score < 800: rate = 0.04
    else: rate = 0.02



    # Use callback for approval if provided
    decision = None
    new_amt = None
    new_yrs = None
    if approval_callback:
        decision, *values = approval_callback(cid, amt, yrs, rate, score)
        if decision == "counter":
            new_amt, new_yrs = values

    # Process decision
    if decision == "accept" or decision is None:
        bank.give_loan(amt, yrs, rate, customer_id=cid, require_approval=False)
        return f"Loan ACCEPTED for customer {cid} (${amt:.2f} for {yrs} yrs at {rate*100:.2f}%)"
    elif decision == "decline":
        return f"Loan DECLINED for customer {cid} (${amt:.2f} for {yrs} yrs at {rate*100:.2f}%)"
    elif decision == "counter":
        # Evaluate counteroffer probability based on credit score
        diff_amt = abs(new_amt - amt) / amt
        diff_yrs = abs(new_yrs - yrs) / max(1, yrs)
        if score < 580: tol = 0.6
        elif score < 670: tol = 0.4
        elif score < 740: tol = 0.25
        elif score < 800: tol = 0.15
        else: tol = 0.1

        acc_score = 1 - (diff_amt + diff_yrs) / 2
        acc_prob = max(0, acc_score - (1 - tol))

        if random.random() < acc_prob:
            bank.give_loan(new_amt, new_yrs, rate, customer_id=cid, require_approval=False)
            return f"Loan COUNTER ACCEPTED for customer {cid} (${new_amt:.2f} for {new_yrs} yrs at {rate*100:.2f}%)"
        else:
            return f"Loan COUNTER REJECTED for customer {cid}"
