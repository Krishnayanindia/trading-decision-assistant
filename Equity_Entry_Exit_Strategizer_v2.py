import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import threading
import time

class QQQMTradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ETF/Stock Trading Decision Assistant")
        self.root.geometry("850x800")
        
        # Make window resizable
        self.root.minsize(800, 700)
        self.root.configure(bg="#1e1e1e")
        
        self.cancel_fetch = False
        self.is_fetching = False
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        
        # Header
        header_frame = tk.Frame(root, bg="#1e1e1e")
        header_frame.pack(pady=10)
        
        title_label = tk.Label(
            header_frame,
            text="🧠 ETF/Stock Trading Decision Assistant",
            font=("Arial", 20, "bold"),
            bg="#1e1e1e",
            fg="#ffffff"
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame,
            text="Real-time analysis based on your trading logic",
            font=("Arial", 10),
            bg="#1e1e1e",
            fg="#888888"
        )
        subtitle_label.pack()
        
        # Ticker input section
        ticker_frame = tk.Frame(header_frame, bg="#1e1e1e")
        ticker_frame.pack(pady=5)
        
        ticker_label = tk.Label(
            ticker_frame,
            text="Ticker Symbol:",
            font=("Arial", 11),
            bg="#1e1e1e",
            fg="#aaaaaa"
        )
        ticker_label.pack(side="left", padx=5)
        
        self.ticker_entry = tk.Entry(
            ticker_frame,
            font=("Arial", 12, "bold"),
            width=10,
            bg="#2d2d2d",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief="solid",
            borderwidth=1
        )
        self.ticker_entry.insert(0, "QQQM")
        self.ticker_entry.pack(side="left", padx=5)
        
        # Popular tickers dropdown
        popular_label = tk.Label(
            ticker_frame,
            text="Quick Select:",
            font=("Arial", 10),
            bg="#1e1e1e",
            fg="#888888"
        )
        popular_label.pack(side="left", padx=(15, 5))
        
        self.ticker_var = tk.StringVar()
        popular_tickers = [
            "QQQM", "QQQ", "SPY", "VOO", "VTI", 
            "IWM", "DIA", "EFA", "VEA", "VWO",
            "AGG", "BND", "TLT", "GLD", "SLV"
        ]
        
        ticker_dropdown = ttk.Combobox(
            ticker_frame,
            textvariable=self.ticker_var,
            values=popular_tickers,
            font=("Arial", 10),
            width=8,
            state="readonly"
        )
        ticker_dropdown.pack(side="left", padx=5)
        ticker_dropdown.bind("<<ComboboxSelected>>", self.on_ticker_selected)
        
        # Main container
        main_frame = tk.Frame(root, bg="#1e1e1e")
        main_frame.pack(pady=5, padx=20, fill="both", expand=True)
        
        # Current data section
        self.data_frame = tk.LabelFrame(
            main_frame,
            text="Current Market Data",
            font=("Arial", 12, "bold"),
            bg="#2d2d2d",
            fg="#ffffff",
            relief="solid",
            borderwidth=1
        )
        self.data_frame.pack(fill="x", pady=5)
        
        # Data labels
        self.current_price_label = self.create_data_label(self.data_frame, "Current Price:", "---")
        self.week_high_label = self.create_data_label(self.data_frame, "52-Week High:", "---")
        self.drop_label = self.create_data_label(self.data_frame, "Drop from 52W High:", "---")
        self.dma_50_label = self.create_data_label(self.data_frame, "50 DMA:", "---")
        self.dma_200_label = self.create_data_label(self.data_frame, "200 DMA:", "---")
        self.rsi_label = self.create_data_label(self.data_frame, "RSI (14):", "---")
        
        # Decision section
        self.decision_frame = tk.LabelFrame(
            main_frame,
            text="Trading Decision",
            font=("Arial", 12, "bold"),
            bg="#2d2d2d",
            fg="#ffffff",
            relief="solid",
            borderwidth=1
        )
        self.decision_frame.pack(fill="both", expand=True, pady=5)
        
        self.decision_label = tk.Label(
            self.decision_frame,
            text="Click 'Analyze Now' to start",
            font=("Arial", 20, "bold"),
            bg="#2d2d2d",
            fg="#ffffff",
            pady=20
        )
        self.decision_label.pack()
        
        self.reason_label = tk.Label(
            self.decision_frame,
            text="",
            font=("Arial", 10),
            bg="#2d2d2d",
            fg="#cccccc",
            wraplength=700,
            justify="left",
            pady=5
        )
        self.reason_label.pack()
        
        # Progress bar
        self.progress = ttk.Progressbar(
            self.decision_frame,
            mode='indeterminate',
            length=300
        )
        
        # Logic summary section
        logic_frame = tk.LabelFrame(
            main_frame,
            text="Logic Summary",
            font=("Arial", 10, "bold"),
            bg="#2d2d2d",
            fg="#ffffff",
            relief="solid",
            borderwidth=1
        )
        logic_frame.pack(fill="x", pady=5)
        
        logic_text = """
🔴 EXIT: >18% drop from 52W high AND 50DMA < 200DMA AND RSI < 40
🟢 RE-ENTRY: >30% drop AND RSI between 35-45
🔵 HOLD: Everything else
        """
        logic_label = tk.Label(
            logic_frame,
            text=logic_text,
            font=("Arial", 9),
            bg="#2d2d2d",
            fg="#aaaaaa",
            justify="left",
            pady=3
        )
        logic_label.pack()
        
        # Buttons
        button_frame = tk.Frame(root, bg="#1e1e1e")
        button_frame.pack(pady=8)
        
        self.analyze_button = tk.Button(
            button_frame,
            text="🔄 Analyze Now",
            command=self.start_analysis,
            font=("Arial", 11, "bold"),
            bg="#4a9eff",
            fg="white",
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2"
        )
        self.analyze_button.pack(side="left", padx=5)
        
        self.cancel_button = tk.Button(
            button_frame,
            text="❌ Cancel",
            command=self.cancel_analysis,
            font=("Arial", 11),
            bg="#ff4444",
            fg="white",
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2",
            state="disabled"
        )
        self.cancel_button.pack(side="left", padx=5)
        
        self.refresh_button = tk.Button(
            button_frame,
            text="♻️ Auto-Refresh (30s)",
            command=self.toggle_auto_refresh,
            font=("Arial", 11),
            bg="#444444",
            fg="white",
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2"
        )
        self.refresh_button.pack(side="left", padx=5)
        
        # Status bar
        self.status_label = tk.Label(
            root,
            text="Ready to analyze",
            font=("Arial", 9),
            bg="#1e1e1e",
            fg="#888888",
            anchor="w"
        )
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=3)
        
        self.auto_refresh = False
        self.refresh_job = None
        
    def on_ticker_selected(self, event):
        """Update ticker entry when dropdown selection changes"""
        selected = self.ticker_var.get()
        self.ticker_entry.delete(0, tk.END)
        self.ticker_entry.insert(0, selected)
    
    def create_data_label(self, parent, label_text, value_text):
        frame = tk.Frame(parent, bg="#2d2d2d")
        frame.pack(fill="x", padx=15, pady=3)
        
        label = tk.Label(
            frame,
            text=label_text,
            font=("Arial", 10),
            bg="#2d2d2d",
            fg="#aaaaaa",
            anchor="w",
            width=20
        )
        label.pack(side="left")
        
        value = tk.Label(
            frame,
            text=value_text,
            font=("Arial", 10, "bold"),
            bg="#2d2d2d",
            fg="#ffffff",
            anchor="w"
        )
        value.pack(side="left")
        
        return value
    
    def calculate_rsi(self, data, periods=14):
        """Calculate RSI indicator"""
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    
    def fetch_and_analyze(self):
        """Fetch data and apply trading logic"""
        self.is_fetching = True
        self.cancel_fetch = False
        
        try:
            # Get ticker from entry
            ticker_symbol = self.ticker_entry.get().strip().upper()
            if not ticker_symbol:
                raise Exception("Please enter a ticker symbol")
            
            # Show progress
            self.root.after(0, lambda: self.progress.pack(pady=10))
            self.root.after(0, lambda: self.progress.start(10))
            self.root.after(0, lambda: self.status_label.config(text=f"⏳ Step 1/3: Connecting to Yahoo Finance for {ticker_symbol}..."))
            self.root.after(0, lambda: self.decision_label.config(text="FETCHING DATA..."))
            
            print("=" * 60)
            print(f"Starting data fetch for {ticker_symbol}...")
            start_time = time.time()
            
            if self.cancel_fetch:
                raise Exception("Cancelled by user")
            
            # Try alternative method first
            self.root.after(0, lambda: self.status_label.config(text=f"⏳ Step 2/3: Downloading {ticker_symbol} market data..."))
            print(f"Attempting to download {ticker_symbol} data...")
            
            # Use simpler download method with progress disabled
            data = yf.download(ticker_symbol, period="1y", progress=False, threads=False)
            
            elapsed = time.time() - start_time
            print(f"Data downloaded in {elapsed:.2f} seconds")
            print(f"Data shape: {data.shape}")
            
            if self.cancel_fetch:
                raise Exception("Cancelled by user")
            
            if data.empty:
                raise Exception(f"No data received for {ticker_symbol}. Check if ticker symbol is correct.")
            
            self.root.after(0, lambda: self.status_label.config(text="⏳ Step 3/3: Calculating indicators..."))
            print("Calculating technical indicators...")
            
            # Calculate metrics
            current_price = float(data['Close'].iloc[-1])
            week_52_high = float(data['High'].max())
            drop_percent = ((week_52_high - current_price) / week_52_high) * 100
            
            # Check if we have enough data
            if len(data) < 200:
                raise Exception(f"Insufficient data: only {len(data)} days available (need 200+ for accurate 200 DMA)")
            
            dma_50 = float(data['Close'].rolling(window=50).mean().iloc[-1])
            dma_200 = float(data['Close'].rolling(window=200).mean().iloc[-1])
            rsi = float(self.calculate_rsi(data))
            
            print(f"{ticker_symbol} - Price: ${current_price:.2f}, Drop: {drop_percent:.2f}%, RSI: {rsi:.2f}")
            
            if self.cancel_fetch:
                raise Exception("Cancelled by user")
            
            # Update UI with calculated values
            self.root.after(0, lambda: self.update_ui(
                ticker_symbol, current_price, week_52_high, drop_percent, 
                dma_50, dma_200, rsi
            ))
            
            print(f"Analysis complete for {ticker_symbol}!")
            print("=" * 60)
            
        except Exception as e:
            error_msg = str(e)
            print(f"ERROR: {error_msg}")
            
            self.root.after(0, lambda: self.show_error(error_msg))
        
        finally:
            self.is_fetching = False
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.progress.pack_forget())
    
    def update_ui(self, ticker_symbol, current_price, week_52_high, drop_percent, dma_50, dma_200, rsi):
        """Update UI with calculated values"""
        self.current_price_label.config(text=f"${current_price:.2f}")
        self.week_high_label.config(text=f"${week_52_high:.2f}")
        self.drop_label.config(text=f"{drop_percent:.2f}%")
        self.dma_50_label.config(text=f"${dma_50:.2f}")
        self.dma_200_label.config(text=f"${dma_200:.2f}")
        self.rsi_label.config(text=f"{rsi:.2f}")
        
        # Apply trading logic
        decision, reason, color = self.apply_logic(ticker_symbol, drop_percent, dma_50, dma_200, rsi)
        
        self.decision_label.config(text=decision, fg=color)
        self.reason_label.config(text=reason)
        
        self.status_label.config(
            text=f"✓ {ticker_symbol} updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    
    def show_error(self, error_msg):
        """Show error message"""
        messagebox.showerror(
            "Error", 
            f"Failed to fetch/analyze data:\n\n{error_msg}\n\n"
            "Troubleshooting:\n"
            "1. Check internet connection\n"
            "2. Verify yfinance is installed: pip install yfinance\n"
            "3. Try updating yfinance: pip install --upgrade yfinance\n"
            "4. Yahoo Finance might be temporarily down\n"
            "5. Try running from command line to see detailed errors"
        )
        
        self.status_label.config(text=f"❌ Error: {error_msg[:50]}...")
        self.decision_label.config(text="ERROR", fg="#ff4444")
        self.reason_label.config(text=f"Error: {error_msg}")
    
    def apply_logic(self, ticker_symbol, drop_percent, dma_50, dma_200, rsi):
        """Apply the trading logic"""
        
        # EXIT condition
        if drop_percent > 18 and dma_50 < dma_200 and rsi < 40:
            return (
                f"🔴 EXIT {ticker_symbol}",
                f"Exit signal triggered:\n"
                f"• Drop from 52W high: {drop_percent:.2f}% (>18% ✓)\n"
                f"• 50 DMA < 200 DMA: ${dma_50:.2f} < ${dma_200:.2f} ✓\n"
                f"• RSI: {rsi:.2f} (<40 ✓)",
                "#ff4444"
            )
        
        # RE-ENTRY condition
        elif drop_percent > 30 and 35 <= rsi <= 45:
            return (
                f"🟢 RE-ENTRY {ticker_symbol}",
                f"Re-entry signal triggered:\n"
                f"• Drop from 52W high: {drop_percent:.2f}% (>30% ✓)\n"
                f"• RSI: {rsi:.2f} (between 35-45 ✓)\n"
                f"Good opportunity to re-enter!",
                "#44ff44"
            )
        
        # HOLD condition
        else:
            reasons = []
            if drop_percent <= 18:
                reasons.append(f"Drop only {drop_percent:.2f}% (need >18% for exit)")
            if dma_50 >= dma_200:
                reasons.append("50 DMA above 200 DMA (bullish)")
            if rsi >= 40:
                reasons.append(f"RSI at {rsi:.2f} (above 40)")
            if drop_percent <= 30:
                reasons.append(f"Not enough drop for re-entry ({drop_percent:.2f}% vs 30%)")
            
            return (
                f"🔵 HOLD {ticker_symbol}",
                f"Hold position. Conditions not met:\n" +
                "\n".join(f"• {r}" for r in reasons),
                "#4a9eff"
            )
    
    def start_analysis(self):
        """Start analysis in a separate thread"""
        if self.is_fetching:
            return
        
        self.analyze_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        thread = threading.Thread(target=self.analyze_thread, daemon=True)
        thread.start()
    
    def analyze_thread(self):
        """Thread for analysis"""
        self.fetch_and_analyze()
        self.root.after(0, lambda: self.analyze_button.config(state="normal"))
        self.root.after(0, lambda: self.cancel_button.config(state="disabled"))
    
    def cancel_analysis(self):
        """Cancel ongoing analysis"""
        self.cancel_fetch = True
        self.status_label.config(text="❌ Cancelled by user")
        self.decision_label.config(text="CANCELLED")
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh mode"""
        self.auto_refresh = not self.auto_refresh
        
        if self.auto_refresh:
            self.refresh_button.config(bg="#44ff44", fg="black")
            self.auto_refresh_cycle()
        else:
            self.refresh_button.config(bg="#444444", fg="white")
            if self.refresh_job:
                self.root.after_cancel(self.refresh_job)
    
    def auto_refresh_cycle(self):
        """Auto-refresh cycle"""
        if self.auto_refresh:
            self.start_analysis()
            self.refresh_job = self.root.after(30000, self.auto_refresh_cycle)

if __name__ == "__main__":
    print("Starting ETF/Stock Trading Decision Assistant...")
    print("Make sure yfinance is installed: pip install yfinance")
    print("You can analyze any ETF or stock ticker!")
    print("-" * 60)
    
    root = tk.Tk()
    app = QQQMTradingApp(root)
    root.mainloop()