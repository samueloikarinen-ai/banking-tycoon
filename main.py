import time
import random
import tkinter as tk
from tkinter import simpledialog, ttk
from svgelements import SVG, Path, Polygon, Polyline, Circle, Ellipse, Line, Rect, Move
from shapely.geometry import Point, Polygon as ShapelyPolygon
import json
import os

# Import your other modules (ensure they are in the same directory)
from history import HistoryLogger
from bank import Bank
from events import deposit_event, withdraw_event, loan_request_event
from menu import PauseMenu  # for the map

# -------------------------------
# File paths for map resources
# -------------------------------
MAP_FOLDER = os.path.join("maps", "europe")
SVG_FILE = os.path.join(MAP_FOLDER, "europe.svg")
JSON_FILE = ("files/countries.json")

# Load country names from JSON
with open(JSON_FILE, "r", encoding="utf-8") as f:
    COUNTRY_NAMES = json.load(f)

# -------------------------------
# Modified BankingGUI (now takes a parent)
# -------------------------------
class BankingGUI:
    def __init__(self, parent, bank: Bank):
        self.root = parent  # Use the parent window
        self.bank = bank
        self.running = True
        self.simulation_paused = False
        self.day_duration = 1
        self.last_day_time = time.time()
        self.pending_event = None
        self.history_logger = HistoryLogger()
        self.logged_history_ids = set()

        # Configure business-like fonts
        self.small_font = ("Segoe UI", 8)
        self.medium_font = ("Segoe UI", 10)
        self.large_font = ("Segoe UI", 12)
        self.title_font = ("Segoe UI", 9, "bold")
        
        # Main banking frame - FIXED HEIGHT to 30% of screen
        screen_height = self.root.winfo_screenheight()
        banking_height = int(screen_height * 0.3)  # 30% of screen
        
        self.banking_frame = tk.Frame(self.root, bg="#2c3e50", relief=tk.RAISED, bd=1, height=banking_height)
        self.banking_frame.pack(side=tk.TOP, fill=tk.X)
        self.banking_frame.pack_propagate(False)  # Prevent frame from resizing

        # --- Top Summary Frame (More compact) ---
        summary_frame = tk.Frame(self.banking_frame, bg="#34495e", height=30)
        summary_frame.pack(side=tk.TOP, fill=tk.X, padx=3, pady=2)
        summary_frame.pack_propagate(False)

        # Balance - larger and more prominent
        self.total_deposits_label = tk.Label(summary_frame, text="", font=self.large_font, 
                                           bg="#34495e", fg="#27ae60", padx=5)
        self.total_deposits_label.pack(side=tk.LEFT)



        # Monthly income - more visible
        self.monthly_income_label = tk.Label(summary_frame, text="", font=self.medium_font, 
                                           bg="#34495e", fg="#9b59b6", padx=5)
        self.monthly_income_label.pack(side=tk.LEFT)

        # Yearly income - more visible
        self.yearly_income_label = tk.Label(summary_frame, text="", font=self.medium_font, 
                                          bg="#34495e", fg="#2ecc71", padx=5)
        self.yearly_income_label.pack(side=tk.LEFT)

        # Economic state indicator - ADD THIS
        self.economic_state = tk.Label(summary_frame, text="Economic State: Normal",
                                       font=self.small_font, bg="#34495e", fg="#f39c12", padx=5)
        self.economic_state.pack(side=tk.LEFT)

        #taxes
        self.tax_label = tk.Label(summary_frame, text="Taxes: $0.00",
                                  font=self.small_font, bg="#34495e", fg="#e74c3c", padx=5)
        self.tax_label.pack(side=tk.LEFT)

        # Date
        self.day_label = tk.Label(summary_frame, text="", font=self.medium_font,
                                bg="#34495e", fg="#ecf0f1", padx=5)
        self.day_label.pack(side=tk.RIGHT)

        # --- Main content frame with proper proportions ---
        content_frame = tk.LabelFrame(self.banking_frame, text="Bank",
                                            font=self.title_font, bg="#2c3e50", fg="#ecf0f1")
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=3, pady=2)

        # Bank information here

        self.central_loans_text = tk.Text(content_frame, height=2, bg="#34495e", fg="#ecf0f1",
                                          borderwidth=1, relief=tk.SUNKEN, font=self.small_font)
        self.central_loans_text.pack(fill=tk.X, padx=2, pady=1)
        self.central_loans_text.config(state="disabled")

        # --- Left column---
        left_column = tk.Frame(content_frame, bg="#2c3e50")
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)



        # Accounts frame for Deposits and Loans
        accounts_frame = tk.Frame(left_column, bg="#2c3e50")
        accounts_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=2)

        # Deposits Panel - more compact
        deposits_frame = tk.LabelFrame(accounts_frame, text="Deposits", 
                                     font=self.title_font, bg="#2c3e50", fg="#ecf0f1")
        deposits_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=1)

        self.deposits_text = tk.Text(deposits_frame, bg="#34495e", fg="#ecf0f1", 
                                   font=self.small_font, borderwidth=1, relief=tk.SUNKEN)
        self.deposits_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.deposits_text.tag_configure("red", foreground="#e74c3c")

        # Deposit Interest Counter
        self.deposit_counter_label = tk.Label(deposits_frame, text="", font=self.small_font, 
                                            bg="#2c3e50", fg="#e74c3c")
        self.deposit_counter_label.pack(side=tk.BOTTOM, pady=(1, 2))

        # Loans Panel - more compact
        loans_frame = tk.LabelFrame(accounts_frame, text="Loans", 
                                  font=self.title_font, bg="#2c3e50", fg="#ecf0f1")
        loans_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=1)

        self.loans_text = tk.Text(loans_frame, bg="#34495e", fg="#ecf0f1", 
                                font=self.small_font, borderwidth=1, relief=tk.SUNKEN)
        self.loans_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.loans_text.tag_configure("green", foreground="#2ecc71")

        # Loan Interest Counter
        self.loan_counter_label = tk.Label(loans_frame, text="", font=self.small_font, 
                                         bg="#2c3e50", fg="#2ecc71")
        self.loan_counter_label.pack(side=tk.BOTTOM, pady=(1, 2))

        # --- Right column: Info panels ---
        right_column = tk.Frame(content_frame, bg="#2c3e50")
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Event panel - more compact
        event_frame = tk.LabelFrame(right_column, text="Event",
                                    font=self.title_font, bg="#2c3e50", fg="#ecf0f1")
        event_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 2))

        self.event_text = tk.Text(event_frame, height=3, state="disabled", bg="#34495e", fg="#ecf0f1",
                                  font=self.small_font, borderwidth=1, relief=tk.SUNKEN)
        self.event_text.pack(fill=tk.BOTH, padx=1, pady=1)






        # Bottom info panels frame
        info_panels_frame = tk.Frame(right_column, bg="#2c3e50")
        info_panels_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=2)

        # History panel - more compact
        history_frame = tk.LabelFrame(info_panels_frame, text="History", 
                                    font=self.title_font, bg="#2c3e50", fg="#ecf0f1")
        history_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=1)

        self.history_text = tk.Text(history_frame, height=3, state="disabled", bg="#34495e", fg="#ecf0f1",
                                  font=self.small_font, borderwidth=1, relief=tk.SUNKEN)
        self.history_text.pack(fill=tk.BOTH, padx=1, pady=1)
        self.history_text.tag_configure("green", foreground="#2ecc71")
        self.history_text.tag_configure("red", foreground="#e74c3c")

        # Transaction Log panel - more compact
        transactions_frame = tk.LabelFrame(info_panels_frame, text="Transactions", 
                                         font=self.title_font, bg="#2c3e50", fg="#ecf0f1")
        transactions_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=1)

        self.transactions_text = tk.Text(transactions_frame, height=3, state="disabled", bg="#34495e", fg="#ecf0f1",
                                       font=self.small_font, borderwidth=1, relief=tk.SUNKEN)
        self.transactions_text.pack(fill=tk.BOTH, padx=1, pady=1)
        self.transactions_text.tag_configure("green", foreground="#2ecc71")
        self.transactions_text.tag_configure("red", foreground="#e74c3c")

        # --- Controls at the very bottom ---
        controls_frame = tk.Frame(self.banking_frame, bg="#2c3e50", height=28)
        controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=3, pady=2)
        controls_frame.pack_propagate(False)

        # Button style - more compact
        button_style = {"font": self.small_font, "bg": "#3498db", "fg": "white", 
                       "activebackground": "#2980b9", "activeforeground": "white",
                       "relief": tk.RAISED, "bd": 1, "padx": 6, "pady": 2}

        tk.Button(controls_frame, text="Borrow", command=self.borrow, **button_style).pack(side=tk.LEFT, padx=2)
        tk.Button(controls_frame, text="Repay", command=self.repay, **button_style).pack(side=tk.LEFT, padx=2)
        self.pause_btn = tk.Button(controls_frame, text="Pause", command=self.toggle_pause, **button_style)
        self.pause_btn.pack(side=tk.LEFT, padx=2)
        tk.Button(controls_frame, text="Continue", command=self.continue_event, **button_style).pack(side=tk.LEFT, padx=2)

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

        # If we have a reference to the map app, sync its pause state too
        if hasattr(self, 'map_app_ref'):
            if self.simulation_paused:
                self.map_app_ref.pause_game()
            else:
                self.map_app_ref.resume_game()

    def continue_event(self):
        self.simulation_paused = False
        self.pause_btn.config(text="Pause")  # Update button text

        # If we have a reference to the map app, sync its pause state too
        if hasattr(self, 'map_app_ref'):
            self.map_app_ref.resume_game()



    def quit_game(self):
        self.running = False
        self.root.destroy()

    # --- Dashboard ---
    def refresh_dashboard(self):
        total_customer_balance = sum(c.get("deposit_balance", 0) for c in self.bank.customers.values())
        self.total_deposits_label.config(text=f"Balance Bank: ${self.bank.balance:,.2f} / Accounts: ${total_customer_balance:,.2f}")
        self.day_label.config(text=f"Day: {self.bank.day}")

        # Display all event messages
            # Check for event messages to display (this is where event display logic belongs)
        event_messages = []

            # Add economic events if available
        if hasattr(self.bank, 'last_economic_event') and self.bank.last_economic_event:
            event_messages.append(f"Economic Event: {self.bank.last_economic_event}")
            self.bank.last_economic_event = None

            # Add other event messages from simulation
        if hasattr(self.bank, 'event_messages') and self.bank.event_messages:
            event_messages.extend(self.bank.event_messages)
                # Don't clear here - we'll clear after displaying

            # Display all event messages
        if event_messages:
            try:
                self.event_text.config(state="normal")
                self.event_text.delete(1.0, tk.END)

                    # Show up to 5 most recent events
                for msg in reversed (event_messages[-2:]):
                    self.event_text.insert(tk.END, f"• {msg}\n")

                self.event_text.config(state="disabled")




            except tk.TclError:
                    # Widget might have been destroyed, skip update
                pass

        # Central Bank Debt
        self.central_loans_text.config(state="normal")
        self.central_loans_text.delete(1.0, tk.END)
        self.central_loans_text.insert(tk.END, "Central Bank Loans:\n")
        if self.bank.central_loans:
            for loan in self.bank.central_loans:
                principal, days_left, accrued, rate = loan
                total_due = principal + accrued

                self.central_loans_text.insert(
                    tk.END, f"  Amount: ${loan[0]:,.2f}, Days: {loan[1]}, Rate: {loan[3]:.2%}, Total due: {total_due:,.2f}\n"
                )
        else:
            self.central_loans_text.insert(tk.END, "  None\n")
        self.central_loans_text.config(state="disabled")

        # Monthly and yearly income
        self.monthly_income_label.config(
            text=f"Monthly Income: ${self.bank.monthly_income:,.2f}"
        )

        # Use the bank's calculated yearly income instead of calculating it here
        self.yearly_income_label.config(
            text=f"Yearly Income: ${self.bank.yearly_income:,.2f}"  # CHANGED THIS LINE
        )

        #taxes
        if self.bank.taxes_paid_history:
            last_tax = self.bank.taxes_paid_history[-1]
            self.tax_label.config(text=f"Taxes: ${last_tax:,.2f}")
        else:
            self.tax_label.config(text="Taxes: $0.00")

        # Update economic state display - ADD THIS
        self.economic_state.config(text=f"Economic State: {self.bank.economic_status}")

        # Set appropriate color based on economic state

        if self.bank.economic_status == "Boom":
            self.economic_state.config(fg="#27ae60")  # Green
        elif self.bank.economic_status == "Recession":
            self.economic_state.config(fg="#e74c3c")  # Red
        elif self.bank.economic_status == "Inflation":
            self.economic_state.config(fg="#f39c12")  # Orange
        elif self.bank.economic_status == "Crisis":
            self.economic_state.config(fg="#8e44ad")  # Purple
        else:  # Normal
            self.economic_state.config(fg="#3498db")  # Blue


        # --- Interest counters ---
        days_until_deposit_payout = 30 - self.bank.days_since_last_collection
        days_until_loan_collection = 30 - self.bank.days_since_last_collection
        self.deposit_counter_label.config(text=f"Deposit interest in: {days_until_deposit_payout} days")
        self.loan_counter_label.config(text=f"Loan interest in: {days_until_loan_collection} days")



        # --- Deposits Panel ---
        self.deposits_text.config(state="normal")
        self.deposits_text.delete(1.0, tk.END)

        # Collect all deposits and sort by amount (largest first)
        all_deposits = []
        for cid, c in self.bank.customers.items():
            for dep in c.get("deposits", []):
                principal = dep.get("amount", 0.0)
                accrued = dep.get("accrued", 0.0)
                total = principal + accrued
                all_deposits.append((total, cid, principal, accrued))

        # Sort by total amount (largest first)
        all_deposits.sort(key=lambda x: x[0], reverse=True)

        # Display sorted deposits
        for total, cid, principal, accrued in all_deposits:
            self.deposits_text.insert(tk.END, f"Customer {cid}: ${principal:.2f} (+ ")
            self.deposits_text.insert(tk.END, f"${accrued:.2f}", "red")
            self.deposits_text.insert(tk.END, " interest)\n")

        self.deposits_text.config(state="disabled")

        # --- Loans Panel ---
        self.loans_text.config(state="normal")
        self.loans_text.delete(1.0, tk.END)

        # Collect all loans and sort by amount (largest first)
        all_loans = []
        for cid, c in self.bank.customers.items():
            for l in c.get("loans", []):
                principal = l.get("amount", 0.0)
                accrued = l.get("accrued", 0.0)
                days_left = l.get("days_left", 0)
                total = principal + accrued
                all_loans.append((total, cid, principal, accrued, days_left))

        # Sort by total amount (largest first)
        all_loans.sort(key=lambda x: x[0], reverse=True)

        # Display sorted loans
        for total, cid, principal, accrued, days_left in all_loans:
            self.loans_text.insert(tk.END, f"Customer {cid}: ${principal:.2f} (+ ")
            self.loans_text.insert(tk.END, f"${accrued:.2f}", "green")
            self.loans_text.insert(tk.END, f" interest) | {days_left} days left\n")

        self.loans_text.config(state="disabled")

        # --- History Panel ---
        self.history_text.config(state="normal")
        self.history_text.delete(1.0, tk.END)
        for day, desc in reversed(self.bank.history[-8:]):
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
        for sign, value in reversed(self.bank.transaction_values[-8:]):
            if sign == '+':
                self.transactions_text.insert(tk.END, f"+{value:.2f}\n", "green")
            else:
                self.transactions_text.insert(tk.END, f"-{value:.2f}\n", "red")
        self.transactions_text.config(state="disabled")

    # --- Event simulation ---
    def simulate_event(self):
        try:
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

            # Store the result in bank's event messages
            if hasattr(self.bank, 'event_messages'):
                self.bank.event_messages.append(result)
            else:
                # Initialize if it doesn't exist
                self.bank.event_messages = [result]

        except Exception as e:
            print(f"Error in simulate_event: {e}")
            # Store error as an event message
            if hasattr(self.bank, 'event_messages'):
                self.bank.event_messages.append(f"Error in event: {e}")
            else:
                self.bank.event_messages = [f"Error in event: {e}"]

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

    def run(self):
        self.refresh_dashboard()
        self.root.mainloop()

# -------------------------------
# Modified EuropeMapApp (now takes a parent)
# -------------------------------
class EuropeMapApp:
    def __init__(self, parent, svg_file, country_names, banking_gui, investments_panel):
        self.root = parent  # Use the parent window
        self.banking_gui = banking_gui
        self.investments_panel = investments_panel
        
        # Map frame that takes 70% of screen
        screen_height = self.root.winfo_screenheight()
        map_height = int(screen_height * 0.7)  # 70% of screen
        
        self.map_frame = tk.Frame(parent, height=map_height)
        self.map_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.map_frame.pack_propagate(False)

        # Create controls frame at the bottom of the map area
        self.map_controls_frame = tk.Frame(self.map_frame, bg="#2c3e50", height=40)
        self.map_controls_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.map_controls_frame.pack_propagate(False)

        self.canvas = tk.Canvas(self.map_frame, bg="lightblue")
        self.canvas.pack(fill="both", expand=True)

        self.svg = SVG.parse(svg_file)
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.last_mouse_pos = None
        self.min_scale = 0.2
        self.countries = []
        self.country_names = country_names

        self.draw_map()

        self.tooltip_label = tk.Label(parent, text="", bg="yellow", font=("Segoe UI", 9), 
                                    relief=tk.RAISED, bd=1, padx=4, pady=1)
        self.tooltip_label.place_forget()

        # Bind events
        self.canvas.bind("<MouseWheel>", self.zoom)
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.pan)
        self.canvas.bind("<ButtonRelease-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_hover)

        # Initialize pause menu
        self.pause_menu = PauseMenu(parent, self.resume_game, self.quit_game)
        self.paused = False

        # Bind ESC key to toggle pause
        self.root.bind("<Escape>", self.toggle_pause)

        #add buttons
        self.add_map_controls()

    # Add this method to EuropeMapApp class:
    def add_map_controls(self):
        """Add control buttons to the map area"""
        button_style = {
            "font": ("Segoe UI", 9),
            "bg": "#3498db",
            "fg": "white",
            "activebackground": "#2980b9",
            "activeforeground": "white",
            "relief": tk.RAISED,
            "bd": 1,
            "padx": 8,
            "pady": 4
        }



        # Create buttons with proper command references
        #from investments panel
        tk.Button(self.map_controls_frame, text="Investments",
                  command=self.investments_panel.show, **button_style).pack(side=tk.RIGHT, padx=5)

        #from banking gui
        tk.Button(self.map_controls_frame, text="Borrow",
                  command=self.banking_gui.borrow, **button_style).pack(side=tk.RIGHT, padx=5)
        tk.Button(self.map_controls_frame, text="Repay",
                  command=self.banking_gui.repay, **button_style).pack(side=tk.RIGHT, padx=5)
        tk.Button(self.map_controls_frame, text="Pause",
                  command=self.banking_gui.toggle_pause, **button_style).pack(side=tk.RIGHT, padx=5)
        tk.Button(self.map_controls_frame, text="Continue",
                  command=self.banking_gui.continue_event, **button_style).pack(side=tk.RIGHT, padx=5)

    # -------------------------------
    # Transform helper
    # -------------------------------
    def transform(self, x, y):
        return x * self.scale + self.offset_x, y * self.scale + self.offset_y

    # -------------------------------
    # Path to polygons
    # -------------------------------
    def path_to_polygons(self, path):
        polygons = []
        current = []
        for seg in path:
            if isinstance(seg, Move):
                if current:
                    polygons.append(current)
                    current = []
                current.append((seg.end.x, seg.end.y))
            elif hasattr(seg, "end"):
                current.append((seg.end.x, seg.end.y))
        if current:
            polygons.append(current)
        return polygons

    # -------------------------------
    # Get country name
    # -------------------------------
    def get_country_name(self, element):
        code = getattr(element, "id", None) or getattr(element, "data_code", None)
        if not code and hasattr(element, "title"):
            code = element.title
        return self.country_names.get(code, "Unknown")

    # -------------------------------
    # Draw SVG map
    # -------------------------------
    def draw_map(self):
        for element in self.svg.elements():
            if isinstance(element, Path):
                for poly in self.path_to_polygons(element):
                    self.draw_polygon(poly, element)
            elif isinstance(element, (Polygon, Polyline)):
                points = [(p[0], p[1]) for p in element]
                self.draw_polygon(points, element)
            elif isinstance(element, Circle):
                cx, cy = self.transform(element.cx, element.cy)
                r = getattr(element, "r", getattr(element, "rx", 0)) * self.scale
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="black")
            elif isinstance(element, Ellipse):
                cx, cy = self.transform(element.cx, element.cy)
                rx = element.rx * self.scale
                ry = element.ry * self.scale
                self.canvas.create_oval(cx - rx, cy - ry, cx + rx, cy + ry, outline="black")
            elif isinstance(element, Line):
                x1, y1 = self.transform(element.x1, element.y1)
                x2, y2 = self.transform(element.x2, element.y2)
                self.canvas.create_line(x1, y1, x2, y2, fill="black")
            elif isinstance(element, Rect):
                x, y = self.transform(element.x, element.y)
                w = element.width * self.scale
                h = element.height * self.scale
                self.canvas.create_rectangle(x, y, x + w, y + h, outline="black")

    # -------------------------------
    # Draw polygon
    # -------------------------------
    def draw_polygon(self, points, element):
        if not points:
            return
        transformed = [self.transform(x, y) for x, y in points]
        flat = [c for p in transformed for c in p]
        cid = self.canvas.create_polygon(flat, outline="black", fill="lightgreen", width=1)
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        bbox = (min(xs), min(ys), max(xs), max(ys))
        name = self.get_country_name(element)
        self.countries.append({
            "canvas_id": cid,
            "original_points": points,
            "bbox": bbox,
            "name": name
        })

    # -------------------------------
    # Zoom
    # -------------------------------
    def zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        new_scale = self.scale * factor
        if new_scale < self.min_scale:
            return
        mx, my = event.x, event.y
        self.offset_x = mx - (mx - self.offset_x) * factor
        self.offset_y = my - (my - self.offset_y) * factor
        self.scale = new_scale
        for country in self.countries:
            self.canvas.scale(country["canvas_id"], mx, my, factor, factor)

    # -------------------------------
    # Pan
    # -------------------------------
    def start_pan(self, event):
        self.last_mouse_pos = (event.x, event.y)

    def pan(self, event):
        dx = event.x - self.last_mouse_pos[0]
        dy = event.y - self.last_mouse_pos[1]
        self.offset_x += dx
        self.offset_y += dy
        self.last_mouse_pos = (event.x, event.y)
        for item in self.canvas.find_all():
            self.canvas.move(item, dx, dy)

    # -------------------------------
    # Click highlight
    # -------------------------------
    def on_click(self, event):
        if self.paused:
            return
        click_x = (event.x - self.offset_x) / self.scale
        click_y = (event.y - self.offset_y) / self.scale
        point = Point(click_x, click_y)
        for c in self.countries:
            self.canvas.itemconfig(c["canvas_id"], fill="lightgreen")
        self.tooltip_label.place_forget()
        for c in self.countries:
            min_x, min_y, max_x, max_y = c["bbox"]
            if min_x <= click_x <= max_x and min_y <= click_y <= max_y:
                if ShapelyPolygon(c["original_points"]).contains(point):
                    self.canvas.itemconfig(c["canvas_id"], fill="yellow")
                    # Show tooltip at exact mouse position
                    self.tooltip_label.config(text=c["name"])
                    self.tooltip_label.place(x=event.x, y=event.y)
                    break

    # -------------------------------
    # Hover tooltip - FIXED to follow mouse exactly
    # -------------------------------
    def on_hover(self, event):
        if self.paused:
            return
        hover_x = (event.x - self.offset_x) / self.scale
        hover_y = (event.y - self.offset_y) / self.scale
        point = Point(hover_x, hover_y)
        
        found = False
        for c in self.countries:
            if ShapelyPolygon(c["original_points"]).contains(point):
                # Place tooltip at exact mouse position
                self.tooltip_label.config(text=c["name"])
                self.tooltip_label.place(x=event.x, y=event.y)
                found = True
                break
        
        if not found:
            self.tooltip_label.place_forget()

    # -------------------------------
    # Pause functionality
    # -------------------------------
    def toggle_pause(self, event=None):
        if self.paused:
            self.resume_game()
        else:
            self.pause_game()

    def pause_game(self):
        self.paused = True
        self.pause_menu.show()

    def resume_game(self):
        self.paused = False
        self.pause_menu.hide()

    def quit_game(self):
        self.root.destroy()



# -------------------------------
# Investments panel
# -------------------------------

class InvestmentsPanel:
    def __init__(self, parent, banking_gui):
        self.parent = parent
        self.banking_gui = banking_gui
        self.bank = banking_gui.bank
        self.window = None



    def show(self):
        """Show the investments panel"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("Investment Portfolio")
        self.window.geometry("1200x600")
        self.window.protocol("WM_DELETE_WINDOW", self.hide)

        # Create notebook for tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Available stocks tab
        available_frame = ttk.Frame(notebook)
        notebook.add(available_frame, text="Available Stocks")
        self.setup_available_stocks(available_frame)

        # Owned stocks tab
        owned_frame = ttk.Frame(notebook)
        notebook.add(owned_frame, text="My Portfolio")
        self.setup_owned_stocks(owned_frame)

        # Portfolio summary
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="Portfolio Summary")
        self.setup_portfolio_summary(summary_frame)

        self.refresh_data()

    def hide(self):
        """Hide the investments panel"""
        if self.window:
            self.window.destroy()
            self.window = None

    def setup_available_stocks(self, parent):
        """Setup the available stocks tab"""
        # Create treeview
        columns = ("Ticker", "Company", "Price", "Change %", "52W High", "52W Low", "P/E Ratio", "Industry", "Action")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)

        # Set column headings and widths
        tree.heading("Ticker", text="Ticker")
        tree.heading("Company", text="Company")
        tree.heading("Price", text="Price")
        tree.heading("Change %", text="Change %")
        tree.heading("52W High", text="52W High")
        tree.heading("52W Low", text="52W Low")
        tree.heading("P/E Ratio", text="P/E Ratio")
        tree.heading("Industry", text="Industry")
        tree.heading("Action", text="Action")

        tree.column("Ticker", width=80, anchor=tk.CENTER)
        tree.column("Company", width=150, anchor=tk.W)
        tree.column("Price", width=80, anchor=tk.CENTER)
        tree.column("Change %", width=80, anchor=tk.CENTER)
        tree.column("52W High", width=80, anchor=tk.CENTER)
        tree.column("52W Low", width=80, anchor=tk.CENTER)
        tree.column("P/E Ratio", width=80, anchor=tk.CENTER)
        tree.column("Industry", width=120, anchor=tk.W)
        tree.column("Action", width=80, anchor=tk.CENTER)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Pack widgets
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        # Add buy frame
        buy_frame = ttk.Frame(parent)
        buy_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(buy_frame, text="Shares to buy:").pack(side=tk.LEFT, padx=5)
        shares_var = tk.StringVar(value="1")
        shares_entry = ttk.Entry(buy_frame, textvariable=shares_var, width=10)
        shares_entry.pack(side=tk.LEFT, padx=5)

        buy_button = ttk.Button(buy_frame, text="Buy Selected",
                                command=lambda: self.buy_selected_stock(tree, shares_var.get()))
        buy_button.pack(side=tk.LEFT, padx=5)

        self.available_tree = tree

    def setup_owned_stocks(self, parent):
        """Setup the owned stocks tab"""
        # Create treeview
        columns = ("Ticker", "Shares", "Avg Price", "Current Price", "Value", "Gain/Loss", "Gain/Loss %", "Action")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)

        # Set column headings
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor=tk.CENTER)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Pack widgets
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        # Add sell frame
        sell_frame = ttk.Frame(parent)
        sell_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(sell_frame, text="Shares to sell:").pack(side=tk.LEFT, padx=5)
        shares_var = tk.StringVar(value="1")
        shares_entry = ttk.Entry(sell_frame, textvariable=shares_var, width=10)
        shares_entry.pack(side=tk.LEFT, padx=5)

        sell_button = ttk.Button(sell_frame, text="Sell Selected",
                                 command=lambda: self.sell_selected_stock(tree, shares_var.get()))
        sell_button.pack(side=tk.LEFT, padx=5)

        self.owned_tree = tree

    def setup_portfolio_summary(self, parent):
        """Setup the portfolio summary tab"""
        summary_frame = ttk.Frame(parent)
        summary_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Portfolio value
        ttk.Label(summary_frame, text="Portfolio Value:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W,
                                                                                           pady=5)
        self.portfolio_value_label = ttk.Label(summary_frame, text="$0.00", font=("Arial", 12))
        self.portfolio_value_label.grid(row=0, column=1, sticky=tk.W, pady=5)

        # Total invested
        ttk.Label(summary_frame, text="Total Invested:", font=("Arial", 12, "bold")).grid(row=1, column=0, sticky=tk.W,
                                                                                          pady=5)
        self.total_invested_label = ttk.Label(summary_frame, text="$0.00", font=("Arial", 12))
        self.total_invested_label.grid(row=1, column=1, sticky=tk.W, pady=5)

        # Total gain/loss
        ttk.Label(summary_frame, text="Total Gain/Loss:", font=("Arial", 12, "bold")).grid(row=2, column=0, sticky=tk.W,
                                                                                           pady=5)
        self.total_gain_label = ttk.Label(summary_frame, text="$0.00", font=("Arial", 12))
        self.total_gain_label.grid(row=2, column=1, sticky=tk.W, pady=5)

        # Percent gain/loss
        ttk.Label(summary_frame, text="Return %:", font=("Arial", 12, "bold")).grid(row=3, column=0, sticky=tk.W,
                                                                                    pady=5)
        self.percent_gain_label = ttk.Label(summary_frame, text="0.00%", font=("Arial", 12))
        self.percent_gain_label.grid(row=3, column=1, sticky=tk.W, pady=5)

        # Refresh button
        refresh_button = ttk.Button(summary_frame, text="Refresh", command=self.refresh_data)
        refresh_button.grid(row=4, column=0, columnspan=2, pady=10)

    def refresh_data(self):
        """Refresh all data in the investments panel"""
        if not self.window or not self.window.winfo_exists():
            return

        # Refresh available stocks
        self.refresh_available_stocks()

        # Refresh owned stocks
        self.refresh_owned_stocks()

        # Refresh portfolio summary
        self.refresh_portfolio_summary()

    def refresh_available_stocks(self):
        """Refresh the available stocks list"""
        if not hasattr(self, 'available_tree'):
            return

        # Clear existing items
        for item in self.available_tree.get_children():
            self.available_tree.delete(item)

        # Get available stocks
        available_stocks = self.bank.get_available_stocks()

        # Add stocks to treeview
        for stock in available_stocks:
            ticker = stock['ticker']
            company = stock['company_name']
            price = stock['stock']['price']
            change_percent = stock['stock'].get('daily_change_percent', 0)
            high_52w = stock['stock'].get('52_week_high', price)
            low_52w = stock['stock'].get('52_week_low', price)
            pe_ratio = stock['stock'].get('pe_ratio', 'N/A')
            industry = stock.get('industry', 'N/A')

            # Color code based on performance
            change_color = "green" if change_percent >= 0 else "red"

            self.available_tree.insert("", "end", values=(
                ticker, company, f"${price:.2f}",
                f"{change_percent:+.2f}%", f"${high_52w:.2f}",
                f"${low_52w:.2f}", pe_ratio, industry, "Buy"
            ))

    def refresh_owned_stocks(self):
        """Refresh the owned stocks list"""
        if not hasattr(self, 'owned_tree'):
            return

        # Clear existing items
        for item in self.owned_tree.get_children():
            self.owned_tree.delete(item)

        # Get owned stocks
        owned_stocks = self.bank.get_owned_stocks()

        # Add stocks to treeview
        for ticker, shares, avg_price in owned_stocks:
            current_price = self.bank.stock_market.get_stock_value(ticker)
            current_value = current_price * shares
            total_invested = avg_price * shares
            gain_loss = current_value - total_invested
            gain_loss_percent = (gain_loss / total_invested) * 100 if total_invested > 0 else 0

            # Color code based on performance
            gain_color = "green" if gain_loss >= 0 else "red"

            self.owned_tree.insert("", "end", values=(
                ticker, shares, f"${avg_price:.2f}",
                f"${current_price:.2f}", f"${current_value:.2f}",
                f"${gain_loss:+.2f}", f"{gain_loss_percent:+.2f}%", "Sell"
            ))

    def refresh_portfolio_summary(self):
        """Refresh the portfolio summary"""
        if not hasattr(self, 'portfolio_value_label'):
            return

        portfolio_value = self.bank.get_portfolio_value()
        total_return, percent_return = self.bank.get_portfolio_performance()

        # Calculate total invested
        total_invested = 0
        for ticker, shares, avg_price in self.bank.get_owned_stocks():
            total_invested += avg_price * shares

        self.portfolio_value_label.config(text=f"${portfolio_value:.2f}")
        self.total_invested_label.config(text=f"${total_invested:.2f}")

        # Color code based on performance
        return_color = "green" if total_return >= 0 else "red"
        self.total_gain_label.config(text=f"${total_return:+.2f}", foreground=return_color)
        self.percent_gain_label.config(text=f"{percent_return:+.2f}%", foreground=return_color)

    def buy_selected_stock(self, tree, shares_str):
        """Buy the selected stock"""
        selection = tree.selection()
        if not selection:
            return

        try:
            shares = int(shares_str)
            if shares <= 0:
                raise ValueError
        except ValueError:
            tk.messagebox.showerror("Error", "Please enter a valid number of shares")
            return

        item = tree.item(selection[0])
        ticker = item['values'][0]

        success, message = self.bank.invest_in_stock(ticker, shares)
        if success:
            tk.messagebox.showinfo("Success", message)
            self.refresh_data()
            self.banking_gui.update_balance_display()  # Update main GUI balance
        else:
            tk.messagebox.showerror("Error", message)

    def sell_selected_stock(self, tree, shares_str):
        """Sell the selected stock"""
        selection = tree.selection()
        if not selection:
            return

        try:
            shares = int(shares_str)
            if shares <= 0:
                raise ValueError
        except ValueError:
            tk.messagebox.showerror("Error", "Please enter a valid number of shares")
            return

        item = tree.item(selection[0])
        ticker = item['values'][0]

        success, message = self.bank.sell_stock(ticker, shares)
        if success:
            tk.messagebox.showinfo("Success", message)
            self.refresh_data()
            self.banking_gui.update_balance_display()  # Update main GUI balance
        else:
            tk.messagebox.showerror("Error", message)






# -------------------------------
# Combined Application
# -------------------------------
class CombinedGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Banking Tycoon")
        
        # Force fullscreen
        self.root.attributes('-fullscreen', True)
        
        # Initialize the Bank
        self.bank = Bank()



        # Create the banking GUI first (30% of screen)
        self.banking_gui = BankingGUI(self.root, self.bank)

        self.investments_panel = InvestmentsPanel(self.root,self.banking_gui)

        # Create the map GUI second (70% of screen)
        self.map_app = EuropeMapApp(self.root, SVG_FILE, COUNTRY_NAMES, self.banking_gui, self.investments_panel)



        # Add reference to map app in banking GUI for two-way communication
        self.banking_gui.map_app_ref = self.map_app

        # Start the banking update loop
        self.root.after(100, self.banking_gui.update_loop)

    def update_game(self):
        """Update the game state"""
        if not self.banking_gui.simulation_paused:
            # Update bank
            curr = time.time()
            if curr - self.banking_gui.last_day_time >= self.banking_gui.day_duration:
                self.bank.advance_day()
                self.banking_gui.last_day_time = curr

                # Update stock market
                self.bank.update_stock_market()

                # Random event
                if random.random() < 0.5:
                    self.banking_gui.simulate_event()

                # Refresh GUI
                self.banking_gui.refresh_dashboard()

                # Refresh investments panel if open
                if hasattr(self.banking_gui,
                           'investments_panel') and self.banking_gui.investments_panel.window and self.banking_gui.investments_panel.window.winfo_exists():
                    self.banking_gui.investments_panel.refresh_data()

        # Schedule next update
        if self.banking_gui.running:
            self.root.after(500, self.update_game)


    def run(self):
        self.root.mainloop()

# -------------------------------
# Run the combined game
# -------------------------------
if __name__ == "__main__":
    game = CombinedGame()
    game.run()