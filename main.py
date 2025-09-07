# main.py
import time
import random
import tkinter as tk
from tkinter import simpledialog

from bank import Bank
from events import deposit_event, withdraw_event, loan_request_event

from history import HistoryLogger

class BankingGUI:
    def __init__(self, bank: Bank):
        self.bank = bank
        self.running = True
        self.simulation_paused = False
        self.day_duration = 1
        self.last_day_time = time.time()
        self.pending_event = None


        # --- GUI Setup ---
        self.root = tk.Tk()
        self.root.title("Banking Tycoon")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f5f5f5")

        # --- Summary Frame ---
        # --- Summary Frame ---
        summary_frame = tk.Frame(self.root, bg="#f5f5f5")
        summary_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.balance_label = tk.Label(summary_frame, text="Bank Balance:", font=("Arial", 16), bg="#f5f5f5")
        self.balance_label.pack(side=tk.LEFT, padx=10)

        self.total_deposits_label = tk.Label(summary_frame, text="", font=("Arial", 20), bg="#f5f5f5", fg="green")
        self.total_deposits_label.pack(side=tk.LEFT, padx=10)

        # --- New: Interest counters ---
        self.deposit_counter_label = tk.Label(summary_frame, text="", font=("Arial", 12), bg="#f5f5f5", fg="red")
        self.deposit_counter_label.pack(side=tk.LEFT, padx=10)

        self.loan_counter_label = tk.Label(summary_frame, text="", font=("Arial", 12), bg="#f5f5f5", fg="green")
        self.loan_counter_label.pack(side=tk.LEFT, padx=10)

        self.day_label = tk.Label(summary_frame, text="", font=("Arial", 16), bg="#f5f5f5")
        self.day_label.pack(side=tk.RIGHT, padx=10)

        # --- Middle Frame for Accounts ---
        middle_frame = tk.Frame(self.root, bg="#f5f5f5")
        middle_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Deposits Panel
        deposits_frame = tk.LabelFrame(middle_frame, text="Customer Deposits", font=("Arial", 12))
        deposits_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.deposits_text = tk.Text(deposits_frame, width=40)
        self.deposits_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.deposits_text.tag_configure("red", foreground="red")

        # Loans Panel
        loans_frame = tk.LabelFrame(middle_frame, text="Customer Loans", font=("Arial", 12))
        loans_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.loans_text = tk.Text(loans_frame, width=40)
        self.loans_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.loans_text.tag_configure("green", foreground="green")

        # --- Controls ---
        frame = tk.Frame(self.root, bg="#f5f5f5")
        frame.pack(pady=5)
        tk.Button(frame, text="Borrow", command=self.borrow).pack(side=tk.LEFT, padx=20)
        tk.Button(frame, text="Repay", command=self.repay).pack(side=tk.LEFT, padx=20)
        self.pause_btn = tk.Button(frame, text="Pause Simulation", command=self.toggle_pause)
        self.pause_btn.pack(side=tk.LEFT, padx=20)
        tk.Button(frame, text="Continue Event", command=self.continue_event).pack(side=tk.LEFT, padx=20)
        tk.Button(frame, text="Quit", command=self.quit_game).pack(side=tk.RIGHT, padx=20)


        # Event messages
        self.event_frame = tk.LabelFrame(self.root, text="Events", font=("Arial", 12))
        self.event_frame.pack(fill=tk.X, padx=10, pady=5)
        self.event_text = tk.Text(self.event_frame, height=5, state="disabled")
        self.event_text.pack(fill=tk.BOTH, padx=5, pady=5)

        # History
        self.history_frame = tk.LabelFrame(self.root, text="Bank History", font=("Arial", 12))
        self.history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.history_text = tk.Text(self.history_frame, height=10, state="disabled")
        self.history_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)


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

        # Buttons
        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Accept", command=accept, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Counter", command=counter, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Decline", command=decline, width=10).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(popup)  # Wait until user clicks something

        # Return result in expected format
        if result.get('decision') == 'counter':
            return ('counter', result['new_amt'], result['new_yrs'])
        else:
            return result.get('decision', 'decline')

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
        # --- Dashboard ---
        def refresh_dashboard(self):
            total_customer_balance = sum(c.get("deposit_balance", 0) for c in self.bank.customers.values())
            self.balance_label.config(text=f"Bank Balance: ${self.bank.balance:,.2f}")
            self.total_deposits_label.config(text=f"${self.bank.balance:,.2f} / ${total_customer_balance:,.2f}")
            self.day_label.config(text=f"Day: {self.bank.day}")

            # --- Interest counters ---
            days_until_deposit_payout = 30 - self.bank.days_since_last_deposit_collection
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
            for day, desc in self.bank.history[-10:]:
                self.history_text.insert(tk.END, f"Day {day}: {desc}\n")
            self.history_text.config(state="disabled")

        # --- Event simulation ---
        def simulate_event(self):
            event_funcs = [deposit_event, loan_request_event]
            if self.bank.deposits:
                event_funcs.append(withdraw_event)

            evt_func = random.choice(event_funcs)

            # Run event and ensure result is a string
            result = evt_func(self.bank)
            if not isinstance(result, str):
                result = str(result)

            self.event_text.config(state="normal")
            self.event_text.delete(1.0, tk.END)
            self.event_text.insert(tk.END, result)
            self.event_text.config(state="disabled")

            # Pause simulation until user clicks "Continue Event"
            self.simulation_paused = True
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
