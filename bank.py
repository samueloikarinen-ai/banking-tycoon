#bank.py
import random
from saveload import load_customers, save_customers, load_bank_data, save_bank_data
from invest import StockMarket

ECONOMY_FILE = "files/economycycle.json"

class Bank:
    last_economic_event: str

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
        self.days_since_last_collection = []
        self.transaction_values = []
        self.monthly_interest_income_history = []
        self.total_paid = 0.0
        self.total_collected = 0.0
        # Add economic system
        self.economic_status = "Normal"  # Can be: Normal, Boom, Recession, Inflation, Crisis
        self.economic_multiplier = 1.0  # Multiplier for deposits
        self.interest_rate_multiplier = 1.0  # Multiplier for interest rates
        self.days_since_last_economic_change = 0
        self.economic_change_interval = 182  # Approximately half a year (365/2)
        # Income
        self.yearly_income = 0.0
        self.monthly_income = 0.0
        # Add tax system
        self.days_since_last_tax = 0
        self.tax_interval = 365  # One year
        self.tax_rate = 0.25  # 25% tax rate (can be adjusted based on economic status)
        self.taxes_paid_history = []  # Track historical tax payments
        # event messages to main.py gui
        self.event_messages = []
        #investing
        self.stock_market = StockMarket(self)
        self.owned_stocks = []  # This will be managed by StockMarket


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
                self.event_messages.append("No customer deposits available for withdrawal.")
                return False
            d = random.choice(eligible_deposits)
            customer_id = d[2]
        else:
            eligible_deposits = [d for d in self.deposits if d[2] == customer_id and d[0] > 0]
            if not eligible_deposits:
                self.event_messages.append(f"Customer {customer_id} has no funds to withdraw.")
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
            self.event_messages.append("Not enough funds for loan!")
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
                self.add_history(f"Loan to customer {customer_id} declined.")
                self.event_messages.append(f"Loan to customer {customer_id} declined.")
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
        self.total_collected = total_collected
        if total_collected > 0:
            self.add_history(f"Collected ${total_collected:,.2f} in loan interest this month")
            self.transaction_values.append(('+', total_collected))


    def pay_monthly_interest(self):
        total_paid = 0.0
        if self.days_since_last_collection >= 30:
            for cid, customer in self.customers.items():
                for dep in customer.get("deposits", []):
                    if dep["accrued"] > 0:
                        customer["deposit_balance"] += dep["accrued"]
                        total_paid += dep["accrued"]
                        dep["accrued"] = 0.0
                customer["deposit_balance"] = round(customer["deposit_balance"], 2)
            self.total_paid = total_paid
            if total_paid > 0:
                self.balance -= total_paid   # Deduct all interest payouts here only!
                self.add_history(f"Paid ${total_paid:,.2f} in deposit interest to customers")
                self.transaction_values.append(('-', total_paid))


    def borrow_central_bank(self, amount, years, rate=0.05,):
        days = int(years * 365)

        self.central_loans.append([amount, days, 0.0, rate])
        self.balance += amount
        self.add_history(f"Borrowed ${amount} from central bank at {rate*100:.2f}%")
        self.save_data()

    def repay_central_bank(self, loan_index=None, amount=None):
        """
        Repay a central bank loan.

        Args:
            loan_index (int, optional): Index of the loan in self.central_loans to repay.
                                        If None, the first loan will be selected.
            amount (float, optional): How much to repay. If None, repay full amount due.

        Returns:
            bool: True if repayment successful, False otherwise.
        """
        if not self.central_loans:
            self.event_messages.append("No central bank loans to repay.")
            return False

        # Default to the first loan if not specified
        if loan_index is None or loan_index < 0 or loan_index >= len(self.central_loans):
            loan_index = 0

        principal, days_left, accrued, rate = self.central_loans[loan_index]
        total_due = principal + accrued

        # If no amount specified, try full repayment
        if amount is None:
            amount = total_due

        # Check available balance
        if amount > self.balance:
            self.add_history(f"Not enough balance to repay ${amount:.2f}. Available: ${self.balance:.2f}")
            self.event_messages.append(f"Not enough balance to repay ${amount:.2f}. Available: ${self.balance:.2f}")
            return False

        # Apply repayment
        if amount >= total_due:
            # Full repayment
            self.balance -= total_due
            self.central_loans.pop(loan_index)
            self.add_history(f"Repaid central bank loan #{loan_index} in full: ${total_due:,.2f}")
            self.event_messages.append(f"Repaid central bank loan #{loan_index} in full: ${total_due:,.2f}")
        else:
            # Partial repayment: reduce accrued first, then principal
            repay_remaining = amount

            # Pay accrued first
            if accrued > 0:
                pay_accrued = min(accrued, repay_remaining)
                accrued -= pay_accrued
                repay_remaining -= pay_accrued

            # Then reduce principal if anything remains
            if repay_remaining > 0:
                principal -= repay_remaining
                repay_remaining = 0

            # Update loan record
            self.central_loans[loan_index] = [principal, days_left, accrued, rate]
            self.balance -= amount
            self.add_history(f"Partially repaid ${amount:,.2f} of central bank loan #{loan_index}. "
                             f"Remaining due: ${principal + accrued:,.2f}")

        self.save_data()
        return True

    def update_economic_status(self):
        """Change economic status every half year with different effects"""
        self.days_since_last_economic_change += 1

        if self.days_since_last_economic_change >= self.economic_change_interval:
            self.days_since_last_economic_change = 0

            # load states and their effects from file
            economic_states = [ECONOMY_FILE]

            # Get current state index
            current_state_index = next((i for i, state in enumerate(economic_states)
                                        if state["name"] == self.economic_status), 0)

            # Choose a new state (can be the same or different)
            if random.random() < 0.7:  # 70% chance to change to a different state
                if random.random() < 0.5:  # 50% chance for it to be normal
                    # Select Normal state specifically
                    new_state = next((s for s in economic_states if s["name"] == "Normal"), economic_states[0])
                else:
                    # Select any state except the current one
                    available_states = [s for s in economic_states if s["name"] != self.economic_status]
                    new_state = random.choice(available_states) if available_states else economic_states[0]
            else:
                new_state = economic_states[current_state_index]  # Stay in current state

            # Apply the economic changes
            old_status = self.economic_status
            self.economic_status = new_state["name"]
            self.economic_multiplier = new_state["deposit_multiplier"]
            self.interest_rate_multiplier = new_state["interest_rate_multiplier"]

            # Apply changes to existing deposits
            deposit_change_factor = new_state["deposit_multiplier"] / (
                economic_states[current_state_index]["deposit_multiplier"] if old_status != "Normal" else 1.0
            )

            for customer in self.customers.values():
                for deposit in customer.get("deposits", []):
                    deposit["amount"] = round(deposit["amount"] * deposit_change_factor, 2)

            # Log the economic change
            self.add_history(f"Economic change: {old_status} → {new_state['name']}. {new_state['message']}")
            self.event_messages.append(f"Economic change: {old_status} → {new_state['name']}. {new_state['message']}")
            return new_state["message"]

        return None


    # ---------- INVESTMENTS ------------

    def invest_in_stock(self, ticker, shares):
        """Public method for GUI to buy stocks"""
        return self.stock_market.buy_stock(ticker, shares)

    def sell_stock(self, ticker, shares):
        """Public method for GUI to sell stocks"""
        return self.stock_market.sell_stock(ticker, shares)

    def get_available_stocks(self):
        """Public method for GUI to get available stocks"""
        return self.stock_market.get_available_stocks()

    def get_owned_stocks(self):
        """Public method for GUI to get owned stocks"""
        return self.stock_market.get_owned_stocks()

    def get_portfolio_value(self):
        """Public method for GUI to get portfolio value"""
        return self.stock_market.get_portfolio_value()

    def get_portfolio_performance(self):
        """Public method for GUI to get portfolio performance"""
        return self.stock_market.get_portfolio_performance()




    # Yearly income
    def calculate_yearly_income(self):
        """Calculate yearly income based on the last 12 months of income history"""
        months = self.monthly_interest_income_history

        if not months:
            return 0.0
        elif len(months) >= 12:
            return sum(months[-12:])
        else:
            # If less than 12 months of data, extrapolate
            avg_monthly = sum(months) / len(months)
            return avg_monthly * 12

    def pay_taxes(self):
        """Calculate and pay yearly taxes"""
        tax_amount = self.yearly_income * self.tax_rate
        if tax_amount > 0 and self.balance >= tax_amount:
            self.balance -= tax_amount
            self.taxes_paid_history.append(tax_amount)
            self.days_since_last_tax = 0

            # Record in history and transactions
            self.add_history(f"Paid ${tax_amount:,.2f} in taxes")
            self.event_messages.append(f"Paid ${tax_amount:,.2f} in taxes")
            self.transaction_values.append(('-', tax_amount))

            # Return message for event display
            return f"Paid ${tax_amount:,.2f} in taxes"
        elif tax_amount > 0:
            message = f"Insufficient funds to pay taxes: ${tax_amount:,.2f} due"
            self.add_history(message)
            return message
        return "No taxes due at this time"



    # ---------- Day / Interest ----------
    def advance_day(self):
        self.day += 1
        self.days_since_last_collection += 1
        self.days_since_last_tax += 1  # Add this

        #
        if self.stock_market.update_market():
            self.add_history("Stock market updated - new stocks available")
            self.event_messages.append("Stock market updated - new stocks available")

        # Add tax payment logic
        if self.days_since_last_tax >= self.tax_interval:
            self.pay_taxes()

        #Economic cycle: boom, normal, recession, etc
        economic_event = self.update_economic_status()
        if economic_event:
            # Store for GUI display
            self.last_economic_event = economic_event

        # --- Customer loans accrual ---
        for loan in self.loans[:]:
            if loan[1] > 0:
                daily_interest = loan[0] * loan[3] * self.interest_rate_multiplier / 365
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
                # record the transaction
                self.transaction_values.append(('+', principal))
                self.loans.remove(loan)

                # --- Remove from customer loans list ---
                for cl in list(self.customers[customer_id]["loans"]):
                    if cl["amount"] == principal and cl["days_left"] <= 0:
                        self.customers[customer_id]["loans"].remove(cl)
                        break


        # --- Central bank loans ---
        for loan in self.central_loans[:]:
            if loan[1] > 0:
                loan[2] += loan[0] * loan[3] * self.interest_rate_multiplier / 365
                loan[1] -= 1
            else:
                principal, _, accrued, rate = loan
                total_due = principal + accrued
                if self.balance >= total_due:
                    self.balance -= total_due
                    self.central_loans.remove(loan)
                    self.add_history(f"Repaid central bank loan of ${total_due:,.2f}")
                    self.event_messages.append(f"Repaid central bank loan of ${total_due:,.2f}")
                else:
                    self.add_history("WARNING: Could not repay central bank loan (insufficient funds)")

        # --- Deposits daily accrual ---
        current_deposit_rate = 0.01 * self.interest_rate_multiplier
        for d in self.deposits:
            daily_interest = d[0] * current_deposit_rate / 365
            d[1] += daily_interest
            customer_id = d[2]
            for cd in self.customers[customer_id]["deposits"]:
                if cd["amount"] >= d[0]:
                    cd["accrued"] += daily_interest
                    break

        # --- Collect loan- and deposit interest every 30 days ---
        if self.days_since_last_collection >= 30:
            self.collect_monthly_interest()
            self.pay_monthly_interest()

            # create monthly income
            self.monthly_income = self.total_collected - self.total_paid
            self.monthly_interest_income_history.append(self.monthly_income)

            # Calculate yearly income - ADD THIS
            self.yearly_income = self.calculate_yearly_income()

            # reset
            self.days_since_last_collection = 0

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
            "next_customer_id": self.next_customer_id,
            "monthly_interest_income_history": self.monthly_interest_income_history,
            "days_since_last_collection": self.days_since_last_collection,
            "economic_status": self.economic_status,
            "economic_multiplier": self.economic_multiplier,
            "interest_rate_multiplier": self.interest_rate_multiplier,
            "days_since_last_economic_change": self.days_since_last_economic_change,
            "days_since_last_tax": self.days_since_last_tax,
            "monthly_income": self.monthly_income,
            "yearly_income": self.yearly_income,  # ADD THIS
            "taxes_paid_history": self.taxes_paid_history,
            "owned_stocks": self.owned_stocks
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
        self.monthly_interest_income_history = data.get("monthly_interest_income_history", [])
        self.days_since_last_collection = data.get("days_since_last_collection", 0)
        self.economic_status = data.get("economic_status", "Normal")
        self.economic_multiplier = data.get("economic_multiplier", 1.0)
        self.interest_rate_multiplier = data.get("interest_rate_multiplier", 1.0)
        self.days_since_last_economic_change = data.get("days_since_last_economic_change", 0)
        self.days_since_last_tax = data.get("days_since_last_tax", 0)
        self.monthly_income = data.get("monthly_income", 0.0)
        self.yearly_income = data.get("yearly_income", 0.0)  # ADD THIS
        self.taxes_paid_history = data.get("taxes_paid_history", [])
        self.owned_stocks = data.get("owned_stocks", [])
        # Reinitialize stock market after loading data
        self.stock_market = StockMarket(self)
        self.load_customers()