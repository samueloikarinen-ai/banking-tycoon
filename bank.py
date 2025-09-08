#bank.py
import random
from saveload import load_customers, save_customers, load_bank_data, save_bank_data

class Bank:
    def __init__(self):
        self.balance = 20000.0
        self.loans = []          # [amount, days_left, accrued, rate, customer_id]
        self.central_loans = []  # [amount, days_left, accrued, rate]
        self.interest_earned = 0.0
        self.deposits = []       # [amount, accrued, customer_id]
        self.day = 0
        self.history = []        # [(day, description)]
        self.next_customer_id = 1
        self.customers = {}      # customer_id: {id, loans, deposits, deposit_balance, credit_score}
        self.running = True
        self.pending_event = None
        self.days_since_last_collection = 0
        self.days_since_last_deposit_collection = 0
        self.transaction_values = []
        self.monthly_interest_income_history = []
        self.total_paid = 0.0
        self.total_collected = 0.0


        # Load data
        self.load_data()

    # ---------- History ----------
    def add_history(self, description):
        self.history.append((self.day, description))
        self.history = [h for h in self.history if self.day - h[0] < 30]

    # ---------- Customers ----------
    def new_customer(self):
        """Create a new customer with unique ID and default values."""
        cid = self.next_customer_id
        score_ranges = [
            ("Poor", 300, 449),
            ("Fair", 450, 599),
            ("Good", 600, 699),
            ("Very Good", 700, 799),
            ("Excellent", 800, 850)
        ]
        _, min_score, max_score = random.choice(score_ranges)
        credit_score = random.randint(min_score, max_score)

        self.customers[cid] = {
            "id": cid,
            "credit_score": credit_score,
            "loans": [],
            "deposits": [],
            "deposit_balance": 0.0
        }
        self.next_customer_id += 1
        self.save_customers()
        return cid

    def add_customer(self):
        return self.new_customer()

    def save_customers(self):
        save_customers(self.customers)

    def load_customers(self):
        self.customers = load_customers()
        if self.customers:
            self.customers = {int(k): v for k, v in self.customers.items()}
            self.next_customer_id = max(self.customers.keys()) + 1

    # ---------- Deposits ----------
    def deposit(self, amount, customer_id=None):
        if customer_id is None:
            if self.customers and random.random() < 0.5:
                customer_id = random.choice(list(self.customers.keys()))
            else:
                customer_id = self.new_customer()
        elif customer_id not in self.customers:
            customer_id = self.new_customer()

        before_balance = self.customers[customer_id].get("deposit_balance", 0.0)
        after_balance = round(before_balance + amount, 2)

        # --- Update global deposits list ---
        existing = next((d for d in self.deposits if d[2] == customer_id), None)
        if existing:
            existing[0] = round(existing[0] + amount, 2)
        else:
            self.deposits.append([round(amount, 2), 0.0, customer_id])

        # --- Update customer deposits list ---
        cust_existing = next((d for d in self.customers[customer_id]["deposits"]), None)
        if cust_existing:
            cust_existing["amount"] = round(cust_existing["amount"] + amount, 2)
        else:
            self.customers[customer_id]["deposits"].append({"amount": round(amount, 2), "accrued": 0.0})

        # --- Update balances ---
        self.customers[customer_id]["deposit_balance"] = after_balance
        self.balance = round(self.balance + amount, 2)

        # --- History & Save ---
        self.add_history(f"Customer {customer_id} deposited ${amount:.2f} (had ${before_balance:.2f}, now ${after_balance:.2f})")
        self.transaction_values.append(('+', amount))
        self.save_data()
        self.save_customers()
        return customer_id

    def withdraw(self, amount, customer_id=None):
        if customer_id is None:
            eligible_deposits = [d for d in self.deposits if d[0] > 0]
            if not eligible_deposits:
                print("No customer deposits available for withdrawal.")
                return False
            d = random.choice(eligible_deposits)
            customer_id = d[2]
        else:
            eligible_deposits = [d for d in self.deposits if d[2] == customer_id and d[0] > 0]
            if not eligible_deposits:
                print(f"Customer {customer_id} has no funds to withdraw.")
                return False
            d = random.choice(eligible_deposits)

        before_balance = self.customers[customer_id].get("deposit_balance", 0.0)
        if amount > before_balance:
            amount = before_balance
        after_balance = round(before_balance - amount, 2)

        # --- Update global deposits ---
        d[0] = round(d[0] - amount, 2)
        if d[0] <= 0:
            self.deposits.remove(d)

        # --- Update customer deposits ---
        for cd in list(self.customers[customer_id]["deposits"]):
            if cd["amount"] >= amount:
                cd["amount"] = round(cd["amount"] - amount, 2)
                if cd["amount"] <= 0:
                    self.customers[customer_id]["deposits"].remove(cd)
                break

        # --- Update balances ---
        self.customers[customer_id]["deposit_balance"] = after_balance
        self.balance = round(self.balance - amount, 2)

        # --- History & Save ---
        self.add_history(f"Customer {customer_id} withdrew ${amount:.2f} (had ${before_balance:.2f}, now ${after_balance:.2f})")
        self.transaction_values.append(('-', amount))
        self.save_data()
        self.save_customers()
        return True

    # ---------- Loans ----------
    def give_loan(self, amount, years, rate=None, customer_id=None, require_approval=True, get_input_func=None):
        if amount > self.balance:
            print("Not enough funds for loan!")
            return False

        if customer_id is None or customer_id not in self.customers:
            customer_id = self.new_customer()

        # Determine interest rate if not provided
        if rate is None:
            score = self.customers[customer_id]["credit_score"]
            if score < 450: rate=0.10
            elif score < 600: rate=0.08
            elif score < 700: rate=0.06
            elif score < 800: rate=0.04
            else: rate=0.02

        # Optional interactive approval
        if require_approval and get_input_func:
            while True:
                response = get_input_func(
                    f"Customer {customer_id} requests a loan of ${amount} for {years} yrs at {rate*100:.2f}%. Approve? (y/n): "
                ).strip().lower()
                if response in ("y", "n"):
                    break
            if response != "y":
                print(f"Loan to customer {customer_id} declined.")
                return False

        # Register loan
        days = int(years * 365)
        self.loans.append([amount, days, 0.0, rate, customer_id])
        self.customers[customer_id]["loans"].append({"amount": amount, "days_left": days, "accrued": 0.0, "rate": rate})
        self.balance -= amount
        self.add_history(f"Loan granted ${amount} at {rate*100:.2f}% to customer {customer_id}")
        self.save_data()
        self.save_customers()
        return True

    def collect_monthly_interest(self):
        total_collected = 0.0
        for loan in self.loans:
            principal, days_left, accrued, rate, customer_id = loan
            if accrued > 0:
                self.balance += accrued
                self.interest_earned += accrued
                total_collected += accrued
                loan[2] = 0.0
                for cl in self.customers[customer_id]["loans"]:
                    if cl["amount"] == principal and cl["days_left"] == days_left:
                        cl["accrued"] = 0.0
                        break
        if total_collected > 0:
            self.add_history(f"Collected ${total_collected:,.2f} in loan interest this month")
            self.transaction_values.append(('+', total_collected))


    def pay_monthly_interest(self):
        if self.days_since_last_deposit_collection >= 30:
            total_paid = 0.0
            for cid, customer in self.customers.items():
                for dep in customer.get("deposits", []):
                    if dep["accrued"] > 0:
                        customer["deposit_balance"] += dep["accrued"]
                        total_paid += dep["accrued"]
                        dep["accrued"] = 0.0
                customer["deposit_balance"] = round(customer["deposit_balance"], 2)
            if total_paid > 0:
                self.balance -= total_paid   # Deduct all interest payouts here only!
                self.add_history(f"Paid ${total_paid:,.2f} in deposit interest to customers")
                self.transaction_values.append(('-', total_paid))


    def borrow_central_bank(self, amount, years, rate=0.05):
        days = int(years * 365)
        self.central_loans.append([amount, days, 0.0, rate])
        self.balance += amount
        self.add_history(f"Borrowed ${amount} from central bank at {rate*100:.2f}%")
        self.save_data()

    def repay_central_bank(self):
        total_due = sum(l[0]+l[2] for l in self.central_loans)
        if total_due > self.balance:
            print("Not enough money to repay central bank loans!")
            return False
        self.balance -= total_due
        self.central_loans.clear()
        self.add_history(f"Repaid ${total_due:,.2f} to central bank")
        self.save_data()
        return True

    # ---------- Day / Interest ----------
    def advance_day(self):
        self.day += 1
        self.days_since_last_collection += 1
        self.days_since_last_deposit_collection += 1

        # --- Customer loans accrual ---
        for loan in self.loans[:]:
            if loan[1] > 0:
                daily_interest = loan[0] * loan[3] / 365
                loan[2] += daily_interest
                loan[1] -= 1
                customer_id = loan[4]
                for cl in self.customers[customer_id]["loans"]:
                    if cl["amount"] == loan[0] and cl["days_left"] == loan[1] + 1:
                        cl["accrued"] += daily_interest
                        cl["days_left"] = loan[1]
                        break
            else:
                principal, _, accrued, rate, customer_id = loan
                self.balance += principal
                self.add_history(f"Customer {customer_id} repaid loan principal of ${principal:,.2f}")
                self.loans.remove(loan)

        # --- Central bank loans ---
        for loan in self.central_loans[:]:
            if loan[1] > 0:
                loan[2] += loan[0] * loan[3] / 365
                loan[1] -= 1
            else:
                principal, _, accrued, rate = loan
                total_due = principal + accrued
                if self.balance >= total_due:
                    self.balance -= total_due
                    self.central_loans.remove(loan)
                    self.add_history(f"Repaid central bank loan of ${total_due:,.2f}")
                else:
                    self.add_history("WARNING: Could not repay central bank loan (insufficient funds)")

        # --- Deposits daily accrual ---
        for d in self.deposits:
            daily_interest = d[0] * 0.01 / 365
            d[1] += daily_interest
            customer_id = d[2]
            for cd in self.customers[customer_id]["deposits"]:
                if cd["amount"] >= d[0]:
                    cd["accrued"] += daily_interest
                    break

        # --- Collect loan and deposit interest every 30 days ---
        if self.days_since_last_collection and self.days_since_last_deposit_collection >= 30:
            self.collect_monthly_interest()
            self.pay_monthly_interest()

            # create monthly income
            monthly_income = self.total_collected - self.total_paid
            self.monthly_interest_income_history.append(monthly_income)

            # reset
            self.days_since_last_collection = 0
            self.days_since_last_deposit_collection = 0


        self.save_data()
        self.save_customers()

    # ---------- Persistence ----------
    def save_data(self):
        save_bank_data({
            "balance": self.balance,
            "loans": self.loans,
            "central_loans": self.central_loans,
            "interest_earned": self.interest_earned,
            "deposits": self.deposits,
            "day": self.day,
            "history": self.history,
            "next_customer_id": self.next_customer_id
        })

    def load_data(self):
        data = load_bank_data()
        self.balance = data.get("balance", 20000)
        self.loans = data.get("loans", [])
        self.central_loans = data.get("central_loans", [])
        self.interest_earned = data.get("interest_earned", 0.0)
        self.deposits = data.get("deposits", [])
        self.day = data.get("day", 0)
        self.history = data.get("history", [])
        self.next_customer_id = data.get("next_customer_id", 1)
        self.load_customers()