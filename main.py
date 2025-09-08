import time
import random
import tkinter as tk
from tkinter import simpledialog

from prompt_toolkit.contrib.telnet import TelnetServer

from history import HistoryLogger

from bank import Bank
from events import deposit_event, withdraw_event, loan_request_event

class BankingGUI:
    def __init__(self, bank: Bank):
        self.root = tk.Tk()
        self.root.title("Banking Tycoon")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f5f5f5")

        self.bank = bank
        self.running = True
        self.simulation_paused = False
        self.day_duration = 1
        self.last_day_time = time.time()
        self.pending_event = None
        self.history_logger = HistoryLogger()
        self.logged_history_ids = set()


        # --- Summary Frame ---
        summary_frame = tk.Frame(self.root, bg="#f5f5f5")
        summary_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Balance
        self.total_deposits_label = tk.Label(summary_frame, text="", font=("Arial", 20), bg="#f5f5f5", fg="green")
        self.total_deposits_label.pack(side=tk.LEFT, padx=10)

        # Date
        self.day_label = tk.Label(summary_frame, text="", font=("Arial", 16), bg="#f5f5f5")
        self.day_label.pack(side=tk.RIGHT, padx=10)

        # Add monthly income label
        self.monthly_income_label = tk.Label(summary_frame, text="", font=("Arial", 12), bg="#f5f5f5", fg="purple")
        self.monthly_income_label.pack(side=tk.LEFT, padx=10)

        # add yearly income
        self.yearly_income_label = tk.Label(summary_frame, text="", font=("Arial", 12), bg="#f5f5f5", fg="darkgreen")
        self.yearly_income_label.pack(side=tk.LEFT, padx=10)



        #secondary summary frame
        secondary_summary_frame = tk.Frame(self.root, bg="#f5f5f5")
        secondary_summary_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=2)

        # Add central bank debt label
        self.central_loans_text = tk.Text(secondary_summary_frame, height=5, width=60, bg="#f5f5f5", borderwidth=0,
                                          font=("Arial", 10))
        self.central_loans_text.pack(side=tk.TOP, padx=10, pady=2)
        self.central_loans_text.config(state="disabled")




        # --- Middle Frame for Accounts ---
        middle_frame = tk.Frame(self.root, bg="#f5f5f5")
        middle_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Deposits Panel
        deposits_frame = tk.LabelFrame(middle_frame, text="Customer Deposits", font=("Arial", 12))
        deposits_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.deposits_text = tk.Text(deposits_frame, width=40)
        self.deposits_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.deposits_text.tag_configure("red", foreground="red")

        # Deposit Interest Counter in Deposits Panel
        self.deposit_counter_label = tk.Label(deposits_frame, text="", font=("Arial", 12), bg="#f5f5f5", fg="red")
        self.deposit_counter_label.pack(side=tk.BOTTOM, pady=(5, 10))

        # Loans Panel
        loans_frame = tk.LabelFrame(middle_frame, text="Customer Loans", font=("Arial", 12))
        loans_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.loans_text = tk.Text(loans_frame, width=40)
        self.loans_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.loans_text.tag_configure("green", foreground="green")

        # Loan Interest Counter in Loans Panel
        self.loan_counter_label = tk.Label(loans_frame, text="", font=("Arial", 12), bg="#f5f5f5", fg="green")
        self.loan_counter_label.pack(side=tk.BOTTOM, pady=(5, 10))

        # --- Controls ---
        frame = tk.Frame(self.root, bg="#f5f5f5")
        frame.pack(pady=5)
        tk.Button(frame, text="Borrow", command=self.borrow).pack(side=tk.LEFT, padx=20)
        tk.Button(frame, text="Repay", command=self.repay).pack(side=tk.LEFT, padx=20)
        self.pause_btn = tk.Button(frame, text="Pause Simulation", command=self.toggle_pause)
        self.pause_btn.pack(side=tk.LEFT, padx=20)
        tk.Button(frame, text="Continue Event", command=self.continue_event).pack(side=tk.LEFT, padx=20)
        tk.Button(frame, text="Quit", command=self.quit_game).pack(side=tk.RIGHT, padx=20)


        # Bottom section

        self.bottom_panels_frame = tk.Frame(self.root)
        self.bottom_panels_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)


        # Event panel
        self.event_frame = tk.LabelFrame(self.bottom_panels_frame, text="Event", font=("Arial", 12))
        self.event_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.event_text = tk.Text(self.event_frame, height=7, state="disabled")
        self.event_text.pack(fill=tk.BOTH, padx=5, pady=5)

        # Transaction Log panel
        self.transactions_frame = tk.LabelFrame(self.bottom_panels_frame, text="Transaction Log", font=("Arial", 12))
        self.transactions_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.transactions_text = tk.Text(self.transactions_frame, height=7, state="disabled")
        self.transactions_text.pack(fill=tk.BOTH, padx=5, pady=5)
        self.transactions_text.tag_configure("green", foreground="green")
        self.transactions_text.tag_configure("red", foreground="red")

        # History panel
        self.history_frame = tk.LabelFrame(self.bottom_panels_frame, text="History", font=("Arial", 12))
        self.history_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.history_text = tk.Text(self.history_frame, height=7, state="disabled")
        self.history_text.pack(fill=tk.BOTH, padx=5, pady=5)
        self.history_text.tag_configure("green", foreground="green")
        self.history_text.tag_configure("red", foreground="red")

        # Start loop
        self.root.after(100, self.update_loop)

    # loan input
    def get_loan_input(self, customer_id, amount, years, rate, credit_score):
        """
        Called by loan_request_event for interactive approval.
        Returns 'accept', 'decline', or ('counter', new_amt, new_years)
        """
        result = {}

        # Create a modal popup
        popup = tk.Toplevel(self.root)
        popup.title(f"Loan Request: Customer {customer_id}")
        popup.grab_set()  # modal behavior

        tk.Label(popup,
                 text=f"Customer {customer_id} requests a loan of ${amount:.2f} for {years} years at {rate * 100:.2f}%").pack(
            padx=10, pady=10)

        def accept():
            result['decision'] = 'accept'
            popup.destroy()

        def decline():
            result['decision'] = 'decline'
            popup.destroy()

        def counter():
            # Ask for new amount/years
            new_amt = simpledialog.askfloat("Counter Offer", "New Amount:", parent=popup, minvalue=1)
            new_yrs = simpledialog.askfloat("Counter Offer", "New Years:", parent=popup, minvalue=0.1)
            if new_amt is not None and new_yrs is not None:
                result['decision'] = 'counter'
                result['new_amt'] = new_amt
                result['new_yrs'] = new_yrs
                popup.destroy()

        # Counter Buttons
        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Accept", command=accept, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Counter", command=counter, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Decline", command=decline, width=10).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(popup)  # Wait until user clicks something

        # Return result in expected format
        if result.get('decision') == 'counter':
            return ('counter', result['new_amt'], result['new_yrs'])
        elif result.get('decision') in ('accept', 'decline'):
            return result.get('decision')
        else:
            return 'decline'  # default if dialog closed

    # --- Commands ---
    def borrow(self):
        amt = simpledialog.askfloat("Borrow", "Amount:")
        yrs = simpledialog.askfloat("Borrow", "Years:")
        if amt and yrs:
            self.bank.borrow_central_bank(amt, yrs)
            self.refresh_dashboard()

    def repay(self):
        self.bank.repay_central_bank()
        self.refresh_dashboard()

    def toggle_pause(self):
        self.simulation_paused = not self.simulation_paused
        self.pause_btn.config(text="Resume" if self.simulation_paused else "Pause")

    def continue_event(self):
        self.simulation_paused = False
        self.event_text.config(state="normal")
        self.event_text.delete(1.0, tk.END)
        self.event_text.config(state="disabled")

    def quit_game(self):
        self.running = False
        self.root.destroy()

    # --- Dashboard ---
    def refresh_dashboard(self):
        total_customer_balance = sum(c.get("deposit_balance", 0) for c in self.bank.customers.values())
        # No bank balance label to update anymore
        self.total_deposits_label.config(text=f"Balance Bank: ${self.bank.balance:,.2f} / Accounts: ${total_customer_balance:,.2f}")
        self.day_label.config(text=f"Day: {self.bank.day}")

        # Central Bank Debt
        self.central_loans_text.config(state="normal")
        self.central_loans_text.delete(1.0, tk.END)
        self.central_loans_text.insert(tk.END, "Central Bank Loans:\n")
        if self.bank.central_loans:
            for loan in self.bank.central_loans:
                principal, days_left, accrued, rate = loan
                total_due = principal + accrued

                self.central_loans_text.insert(
                    tk.END, f"  Amount: ${loan[0]:,.2f}, Days: {loan[1]}, Rate: {loan[3]:.2%}, Total due: {total_due:,.2f}\n",
                            "left"
                )
        else:
            self.central_loans_text.insert(tk.END, "  None\n")
        self.central_loans_text.config(state="disabled")

        # Monthly and yearly income
        monthly_income = self.bank.total_collected - self.bank.total_paid
        self.monthly_income_label.config(
            text=f"Monthly Income: ${monthly_income:,.2f}"
        )

        months = self.bank.monthly_interest_income_history

        if not months:
            yearly_income = 0.0
        elif len(months) >= 12:

            yearly_income = sum(months[-12:])
        else:

            repeated = (months * (12 // len(months) + 1))[:12]
            yearly_income = sum(repeated)

        self.yearly_income_label.config(
            text=f"Yearly Income: ${yearly_income:,.2f}"
        )

        # --- Interest counters ---
        days_until_deposit_payout = 30 - self.bank.days_since_last_collection
        days_until_loan_collection = 30 - self.bank.days_since_last_collection
        self.deposit_counter_label.config(text=f"Deposit interest in: {days_until_deposit_payout} days")
        self.loan_counter_label.config(text=f"Loan interest in: {days_until_loan_collection} days")

        # --- Deposits Panel ---
        self.deposits_text.config(state="normal")
        self.deposits_text.delete(1.0, tk.END)
        for cid, c in self.bank.customers.items():
            for dep in c.get("deposits", []):
                principal = dep.get("amount", 0.0)
                accrued = dep.get("accrued", 0.0)
                self.deposits_text.insert(tk.END, f"Customer {cid}: ${principal:.2f} (+ ")
                self.deposits_text.insert(tk.END, f"${accrued:.2f}", "red")
                self.deposits_text.insert(tk.END, " interest)\n")
        self.deposits_text.config(state="disabled")

        # --- Loans Panel ---
        self.loans_text.config(state="normal")
        self.loans_text.delete(1.0, tk.END)
        for cid, c in self.bank.customers.items():
            for l in c.get("loans", []):
                principal = l.get("amount", 0.0)
                accrued = l.get("accrued", 0.0)
                days_left = l.get("days_left", 0)
                self.loans_text.insert(tk.END, f"Customer {cid}: ${principal:.2f} (+ ")
                self.loans_text.insert(tk.END, f"${accrued:.2f}", "green")
                self.loans_text.insert(tk.END, f" interest) | {days_left} days left\n")
        self.loans_text.config(state="disabled")

        # --- History Panel ---
        self.history_text.config(state="normal")
        self.history_text.delete(1.0, tk.END)
        for day, desc in reversed(self.bank.history[-10:]):
            self.history_text.insert(tk.END, f"Day {day}: {desc}\n")
            # Only log new events
            history_id = (day, desc)
            if history_id not in self.logged_history_ids:
                self.history_logger.log(f"Day {day}: {desc}")
                self.logged_history_ids.add(history_id)
        self.history_text.config(state="disabled")

        # Transaction log
        self.transactions_text.config(state="normal")
        self.transactions_text.delete(1.0, tk.END)
        for sign, value in reversed(self.bank.transaction_values[-10:]):
            if sign == '+':
                self.transactions_text.insert(tk.END, f"+{value:.2f}\n", "green")
            else:
                self.transactions_text.insert(tk.END, f"-{value:.2f}\n", "red")
        self.transactions_text.config(state="disabled")

    # --- Event simulation ---
    def simulate_event(self):
        event_funcs = [deposit_event, loan_request_event]

        if self.bank.deposits:
            event_funcs.append(withdraw_event)

        evt_func = random.choice(event_funcs)
        should_pause = evt_func != loan_request_event

        if should_pause:
            self.simulation_paused = True
        else:
            self.simulation_paused = False

        # Run event and ensure result is a string
        if evt_func == loan_request_event:
            result = evt_func(self.bank, approval_callback=self.get_loan_input)
            # Don't pause for loan events – handled in modal
        else:
            result = evt_func(self.bank)
            # Pause for deposit/withdrawal events
            self.simulation_paused = True

        if not isinstance(result, str):
            result = str(result)

        self.event_text.config(state="normal")
        self.event_text.delete(1.0, tk.END)
        self.event_text.insert(tk.END, result)
        self.event_text.config(state="disabled")

        self.refresh_dashboard()

    # --- Update Loop ---
    def update_loop(self):
        if self.running and not self.simulation_paused:
            curr = time.time()
            if curr - self.last_day_time >= self.day_duration:
                self.bank.advance_day()
                self.last_day_time = curr

                # Random event
                if random.random() < 0.5:
                    self.simulate_event()

                self.refresh_dashboard()
        if self.running:
            self.root.after(500, self.update_loop)

    # --- Run ---
    def run(self):
        self.refresh_dashboard()
        self.root.mainloop()


if __name__ == "__main__":
    bank = Bank()
    gui = BankingGUI(bank)
    gui.run()