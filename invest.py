# invest.py
import json
import random
import os
from datetime import datetime

STOCKS_FILE = "files/stocks.json"
CURRENT_STOCKS_FILE = "files/current_stocks.json"


class StockMarket:
    def __init__(self, bank):
        self.bank = bank
        self.available_stocks = []
        self.owned_stocks = []  # [ticker, shares, purchase_price]
        self.stock_price_history = {}  # {ticker: [price_history]}
        self.days_since_last_market_update = 0
        self.market_update_interval = 30  # Update market every 30 days
        self.load_stocks()
        self.load_owned_stocks()

    def load_stocks(self):
        """Load stocks from JSON file and initialize current prices"""
        try:
            # First try to load current stock data
            if os.path.exists(CURRENT_STOCKS_FILE):
                with open(CURRENT_STOCKS_FILE, 'r', encoding='utf-8') as f:
                    self.available_stocks = json.load(f)
            else:
                # Load from original stocks and initialize current prices
                with open(STOCKS_FILE, 'r', encoding='utf-8') as f:
                    original_stocks = json.load(f)
                    self.available_stocks = original_stocks.copy()

                # Save current state
                self.save_current_stocks()

            # Initialize price history for each stock
            for stock in self.available_stocks:
                ticker = stock['ticker']
                self.stock_price_history[ticker] = [stock['stock']['price']]

        except FileNotFoundError:
            print(f"Warning: {STOCKS_FILE} not found. No stocks available.")
            self.available_stocks = []

    def save_current_stocks(self):
        """Save current stock data to separate file"""
        try:
            with open(CURRENT_STOCKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.available_stocks, f, indent=2)
        except Exception as e:
            print(f"Error saving current stocks: {e}")

    def load_owned_stocks(self):
        """Load owned stocks from bank data"""
        if hasattr(self.bank, 'owned_stocks'):
            self.owned_stocks = self.bank.owned_stocks
        else:
            self.owned_stocks = []

    def save_owned_stocks(self):
        """Save owned stocks to bank data"""
        self.bank.owned_stocks = self.owned_stocks

    def update_market(self):
        """Update stock prices and available stocks"""
        self.days_since_last_market_update += 1

        if self.days_since_last_market_update >= self.market_update_interval:
            self.days_since_last_market_update = 0

            # Randomly add/remove some stocks from the market
            self.rotate_available_stocks()

            # Update prices for all available stocks
            self.update_stock_prices()

            # Save updated stock data
            self.save_current_stocks()

            return True
        return False

    def rotate_available_stocks(self):
        """Randomly select 20 stocks to be available in the market"""
        # Get all possible stocks
        try:
            with open(STOCKS_FILE, 'r', encoding='utf-8') as f:
                all_stocks = json.load(f)
        except FileNotFoundError:
            print(f"Warning: {STOCKS_FILE} not found.")
            return

        # Filter out stocks that are already owned
        owned_tickers = [s[0] for s in self.owned_stocks]
        available_for_selection = [s for s in all_stocks if s['ticker'] not in owned_tickers]

        # Select 20 random stocks (or less if not enough available)
        num_to_select = min(30, len(available_for_selection))
        if num_to_select > 0:
            self.available_stocks = random.sample(available_for_selection, num_to_select)
        else:
            self.available_stocks = []

    def update_stock_prices(self):
        """Update prices for all available stocks based on random factors"""
        for stock in self.available_stocks:
            current_price = stock['stock']['price']

            # More realistic price changes based on company performance
            volatility = random.uniform(0.02, 0.08)  # 2-8% volatility
            trend_factor = random.uniform(-0.05, 0.1)  # Random trend

            # Company-specific factors
            pe_ratio = stock['stock'].get('pe_ratio', 15)
            debt_equity = stock['financials'].get('debt_equity', 1.0)

            # Calculate price change
            if pe_ratio > 20:  # Overvalued stocks more volatile
                volatility *= 1.5
            if debt_equity > 1.5:  # High debt companies more risky
                volatility *= 1.3

            change_percent = random.gauss(trend_factor, volatility)
            new_price = current_price * (1 + change_percent)

            # Ensure price doesn't go below a minimum
            min_price = current_price * 0.3  # At least 30% of current price
            new_price = max(new_price, min_price)

            # Update stock data
            stock['stock']['price'] = round(new_price, 2)
            stock['stock']['daily_change_percent'] = round(change_percent * 100, 2)

            # Update 52-week high/low if needed
            if new_price > stock['stock'].get('52_week_high', 0):
                stock['stock']['52_week_high'] = round(new_price, 2)
            if new_price < stock['stock'].get('52_week_low', float('inf')):
                stock['stock']['52_week_low'] = round(new_price, 2)

            # Update price history
            ticker = stock['ticker']
            if ticker in self.stock_price_history:
                self.stock_price_history[ticker].append(new_price)
                # Keep only the last 100 price points
                if len(self.stock_price_history[ticker]) > 100:
                    self.stock_price_history[ticker] = self.stock_price_history[ticker][-100:]

    def get_available_stocks(self):
        """Get stocks currently available in the market"""
        return self.available_stocks

    def get_owned_stocks(self):
        """Get stocks owned by the bank"""
        return self.owned_stocks

    def buy_stock(self, ticker, shares):
        """Buy shares of a stock"""
        # Find the stock
        stock = next((s for s in self.available_stocks if s['ticker'] == ticker), None)
        if not stock:
            return False, "Stock not available"

        total_cost = stock['stock']['price'] * shares
        if total_cost > self.bank.balance:
            return False, "Insufficient funds"

        # Check if we already own this stock
        owned_idx = -1
        for i, (owned_ticker, owned_shares, purchase_price) in enumerate(self.owned_stocks):
            if owned_ticker == ticker:
                owned_idx = i
                break

        if owned_idx >= 0:
            # Update existing holding
            current_value = self.owned_stocks[owned_idx][1] * self.owned_stocks[owned_idx][2]
            new_value = current_value + total_cost
            new_shares = self.owned_stocks[owned_idx][1] + shares
            new_avg_price = new_value / new_shares

            self.owned_stocks[owned_idx] = [ticker, new_shares, new_avg_price]
        else:
            # Add new holding
            self.owned_stocks.append([ticker, shares, stock['stock']['price']])


        # Deduct from bank balance
        self.bank.balance -= total_cost

        # Remove from available stocks if we now own all shares (simplified)
        # In reality, stocks would remain available unless delisted
        stock_idx = next((i for i, s in enumerate(self.available_stocks) if s['ticker'] == ticker), -1)
        if stock_idx >= 0:
            self.available_stocks.pop(stock_idx)

        # Add to transaction history
        self.bank.add_history(f"Bought {shares} shares of {ticker} at ${stock['stock']['price']:.2f} each")
        self.bank.transaction_values.append(('-', total_cost))

        self.save_owned_stocks()
        self.save_current_stocks()
        return True, f"Successfully bought {shares} shares of {ticker}"

    def sell_stock(self, ticker, shares):
        """Sell shares of a stock"""
        # Find the owned stock
        owned_idx = -1
        for i, (owned_ticker, owned_shares, purchase_price) in enumerate(self.owned_stocks):
            if owned_ticker == ticker:
                owned_idx = i
                break

        if owned_idx < 0:
            return False, "You don't own this stock"

        if shares > self.owned_stocks[owned_idx][1]:
            return False, "You don't own enough shares"

        # Find the current price from available stocks or history
        current_price = None
        for stock in self.available_stocks:
            if stock['ticker'] == ticker:
                current_price = stock['stock']['price']
                break

        if current_price is None:
            # If stock is not available, use the last known price from history
            if ticker in self.stock_price_history and self.stock_price_history[ticker]:
                current_price = self.stock_price_history[ticker][-1]
            else:
                return False, "Cannot determine current price"

        sale_value = current_price * shares
        purchase_cost = self.owned_stocks[owned_idx][2] * shares
        profit = sale_value - purchase_cost

        # Update bank balance
        self.bank.balance += sale_value

        # Update or remove the holding
        if shares == self.owned_stocks[owned_idx][1]:
            # Sold all shares - remove from owned
            self.owned_stocks.pop(owned_idx)

            # Add back to available stocks
            try:
                with open(STOCKS_FILE, 'r', encoding='utf-8') as f:
                    all_stocks = json.load(f)
                original_stock = next((s for s in all_stocks if s['ticker'] == ticker), None)
                if original_stock:
                    # Update with current price but keep other original data
                    original_stock['stock']['price'] = current_price
                    self.available_stocks.append(original_stock)
            except FileNotFoundError:
                pass
        else:
            # Sold some shares
            self.owned_stocks[owned_idx][1] -= shares

        # Add to transaction history
        profit_text = f" (profit: ${profit:.2f})" if profit >= 0 else f" (loss: ${-profit:.2f})"
        self.bank.add_history(f"Sold {shares} shares of {ticker} at ${current_price:.2f} each{profit_text}")
        self.bank.transaction_values.append(('+', sale_value))

        self.save_owned_stocks()
        self.save_current_stocks()
        return True, f"Successfully sold {shares} shares of {ticker}"

    def get_stock_value(self, ticker):
        """Get the current value of a stock"""
        # First check available stocks
        for stock in self.available_stocks:
            if stock['ticker'] == ticker:
                return stock['stock']['price']

        # Then check price history
        if ticker in self.stock_price_history and self.stock_price_history[ticker]:
            return self.stock_price_history[ticker][-1]

        return 0

    def get_portfolio_value(self):
        """Calculate the total value of the investment portfolio"""
        total_value = 0
        for ticker, shares, purchase_price in self.owned_stocks:
            current_price = self.get_stock_value(ticker)
            total_value += current_price * shares
        return total_value

    def get_portfolio_performance(self):
        """Calculate portfolio performance"""
        total_invested = 0
        total_current = 0

        for ticker, shares, purchase_price in self.owned_stocks:
            total_invested += purchase_price * shares
            current_price = self.get_stock_value(ticker)
            total_current += current_price * shares

        if total_invested == 0:
            return 0, 0

        total_return = total_current - total_invested
        percent_return = (total_return / total_invested) * 100 if total_invested > 0 else 0

        return total_return, percent_return
