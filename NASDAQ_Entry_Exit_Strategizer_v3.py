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
        self.root.geometry("850x920")
        
        # Make window resizable
        self.root.minsize(800, 820)
        self.root.configure(bg="#1e1e1e")
        
        self.cancel_fetch = False
        self.is_fetching = False
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        
        # Create main canvas with scrollbars
        self.main_canvas = tk.Canvas(root, bg="#1e1e1e", highlightthickness=0)
        self.main_canvas.pack(side="left", fill="both", expand=True)
        
        # Add vertical scrollbar
        v_scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.main_canvas.yview)
        v_scrollbar.pack(side="right", fill="y")
        
        # Add horizontal scrollbar (pack this last, after status bar)
        self.h_scrollbar = ttk.Scrollbar(root, orient="horizontal", command=self.main_canvas.xview)
        
        # Configure canvas scrollbars
        self.main_canvas.configure(
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set
        )
        
        # Create scrollable frame inside canvas
        self.scrollable_frame = tk.Frame(self.main_canvas, bg="#1e1e1e")
        self.canvas_frame = self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Bind frame resize to update scroll region
        self.scrollable_frame.bind("<Configure>", lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))
        
        # Bind canvas resize to update frame width
        self.main_canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Enable mouse wheel scrolling
        self.main_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.main_canvas.bind_all("<Button-4>", self._on_mousewheel)  # Linux scroll up
        self.main_canvas.bind_all("<Button-5>", self._on_mousewheel)  # Linux scroll down
        
        # Now build the UI inside scrollable_frame instead of root
        self.build_ui()
        
        # Pack the horizontal scrollbar first (will be at very bottom)
        self.h_scrollbar.pack(side="bottom", fill="x")
        
        # Then create and pack status bar (will appear above h-scrollbar)
        self.create_status_bar()
        
        self.auto_refresh = False
        self.refresh_job = None
    
    def _on_canvas_configure(self, event):
        """Update the canvas window width to match canvas width"""
        self.main_canvas.itemconfig(self.canvas_frame, width=event.width)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.num == 5 or event.delta < 0:
            # Scroll down
            self.main_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            # Scroll up
            self.main_canvas.yview_scroll(-1, "units")
    
    def build_ui(self):
        """Build the user interface"""
        root = self.scrollable_frame  # Use scrollable frame instead of root
        
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
            text="Real-time analysis with RSI & Stochastic indicators + Early Warning System",
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
            "AGG", "BND", "TLT", "GLD", "SLV",
            "INDA", "INDY"
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
        self.stoch_k_label = self.create_data_label(self.data_frame, "Stochastic %K:", "---")
        self.stoch_d_label = self.create_data_label(self.data_frame, "Stochastic %D:", "---")
        
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
        self.logic_frame = tk.LabelFrame(
            main_frame,
            text="Logic Summary",
            font=("Arial", 10, "bold"),
            bg="#2d2d2d",
            fg="#ffffff",
            relief="solid",
            borderwidth=1
        )
        self.logic_frame.pack(fill="x", pady=5)
        
        logic_text = """
🔴 EXIT: >18% drop AND 50DMA < 200DMA AND RSI < 40 AND Stochastic %K < 20 AND %K crosses below %D
🟠 EXIT WARNING: All EXIT signals met EXCEPT drop % - Prepare for potential exit!
🟡 TAKE PROFIT: <5% from high AND RSI > 70 AND Stochastic %K > 80 AND %K crosses below %D
🟠 PROFIT WARNING: Overbought but waiting for bearish crossover - Watch closely!
🟢 RE-ENTRY: >30% drop AND RSI 35-45 AND Stochastic %K crosses above %D
🟠 ENTRY WARNING: Drop & RSI met but waiting for bullish crossover - Almost ready!
🔵 HOLD: Everything else
        """
        
        logic_label = tk.Label(
            self.logic_frame,
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
    
    def create_status_bar(self):
        """Create status bar at the bottom (always visible)"""
        # Status bar (outside scrollable area - always visible at bottom)
        self.status_label = tk.Label(
            self.root,
            text="Ready to analyze",
            font=("Arial", 9),
            bg="#1e1e1e",
            fg="#888888",
            anchor="w"
        )
        # Pack before the horizontal scrollbar so it appears above it
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=3)
        
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
        close = data['Close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
        
        # Avoid division by zero
        rs = gain / loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        # Return the last valid value
        rsi_value = rsi.iloc[-1]
        
        # Handle NaN
        if pd.isna(rsi_value):
            return 50.0  # Neutral value
        
        return float(rsi_value)
    
    def calculate_stochastic(self, data, k_period=14, d_period=3):
        """Calculate Stochastic oscillator (%K and %D)"""
        # Get price data
        close = data['Close']
        low = data['Low']
        high = data['High']
        
        # Calculate %K
        low_min = low.rolling(window=k_period).min()
        high_max = high.rolling(window=k_period).max()
        
        # Avoid division by zero
        denominator = high_max - low_min
        denominator = denominator.replace(0, 1e-10)
        
        stoch_k = 100 * (close - low_min) / denominator
        
        # Calculate %D (moving average of %K)
        stoch_d = stoch_k.rolling(window=d_period).mean()
        
        # Get the last values
        k_value = stoch_k.iloc[-1]
        d_value = stoch_d.iloc[-1]
        
        # Handle NaN values
        if pd.isna(k_value):
            k_value = 50.0
        if pd.isna(d_value):
            d_value = 50.0
        
        return float(k_value), float(d_value)
    
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
            
            # Download data
            self.root.after(0, lambda: self.status_label.config(text=f"⏳ Step 2/3: Downloading {ticker_symbol} market data..."))
            print(f"Attempting to download {ticker_symbol} data...")
            
            data = yf.download(ticker_symbol, period="1y", progress=False, threads=False)
            
            # Fix for multi-index columns (happens with single ticker downloads)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            elapsed = time.time() - start_time
            print(f"Data downloaded in {elapsed:.2f} seconds")
            print(f"Data shape: {data.shape}")
            print(f"Columns: {data.columns.tolist()}")
            
            if self.cancel_fetch:
                raise Exception("Cancelled by user")
            
            if data.empty:
                raise Exception(f"No data received for {ticker_symbol}. Check if ticker symbol is correct.")
            
            self.root.after(0, lambda: self.status_label.config(text="⏳ Step 3/3: Calculating indicators..."))
            print("Calculating technical indicators...")
            
            # Calculate metrics - ensure we're working with Series not DataFrame
            current_price = float(data['Close'].iloc[-1])
            week_52_high = float(data['High'].max())
            drop_percent = ((week_52_high - current_price) / week_52_high) * 100
            
            # Check if we have enough data
            if len(data) < 200:
                raise Exception(f"Insufficient data: only {len(data)} days available (need 200+ for accurate indicators)")
            
            # Calculate moving averages
            dma_50 = float(data['Close'].rolling(window=50).mean().iloc[-1])
            dma_200 = float(data['Close'].rolling(window=200).mean().iloc[-1])
            
            # Calculate RSI
            rsi = float(self.calculate_rsi(data))
            
            # Calculate Stochastic
            stoch_k, stoch_d = self.calculate_stochastic(data)
            stoch_k = float(stoch_k)
            stoch_d = float(stoch_d)
            
            print(f"{ticker_symbol} - Price: ${current_price:.2f}, RSI: {rsi:.2f}, Stoch %K: {stoch_k:.2f}, %D: {stoch_d:.2f}")
            
            if self.cancel_fetch:
                raise Exception("Cancelled by user")
            
            # Update UI with calculated values
            self.root.after(0, lambda: self.update_ui(
                ticker_symbol, current_price, week_52_high, drop_percent, 
                dma_50, dma_200, rsi, stoch_k, stoch_d
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
    
    def update_ui(self, ticker_symbol, current_price, week_52_high, drop_percent, dma_50, dma_200, rsi, stoch_k, stoch_d):
        """Update UI with calculated values"""
        self.current_price_label.config(text=f"${current_price:.2f}")
        self.week_high_label.config(text=f"${week_52_high:.2f}")
        self.drop_label.config(text=f"{drop_percent:.2f}%")
        self.dma_50_label.config(text=f"${dma_50:.2f}")
        self.dma_200_label.config(text=f"${dma_200:.2f}")
        self.rsi_label.config(text=f"{rsi:.2f}")
        self.stoch_k_label.config(text=f"{stoch_k:.2f}")
        self.stoch_d_label.config(text=f"{stoch_d:.2f}")
        
        # Apply advanced trading logic with stochastic
        decision, reason, color = self.apply_trading_logic(
            ticker_symbol, drop_percent, dma_50, dma_200, rsi, stoch_k, stoch_d
        )
        
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
    
    def apply_trading_logic(self, ticker_symbol, drop_percent, dma_50, dma_200, rsi, stoch_k, stoch_d):
        """Apply trading logic with RSI + Stochastic indicators"""
        
        # Calculate crossover status
        k_above_d = stoch_k > stoch_d
        k_below_d = stoch_k < stoch_d
        crossover_signal = "Bullish (%K > %D)" if k_above_d else "Bearish (%K < %D)"
        
        # EXIT condition (with Stochastic bearish crossover)
        if drop_percent > 18 and dma_50 < dma_200 and rsi < 40 and stoch_k < 20 and k_below_d:
            return (
                f"🔴 EXIT {ticker_symbol}",
                f"Strong exit signal - All indicators confirm:\n"
                f"• Drop from 52W high: {drop_percent:.2f}% (>18% ✓)\n"
                f"• 50 DMA < 200 DMA: ${dma_50:.2f} < ${dma_200:.2f} ✓\n"
                f"• RSI: {rsi:.2f} (<40 ✓) - Oversold\n"
                f"• Stochastic %K: {stoch_k:.2f} (<20 ✓) - Severely Oversold\n"
                f"• Stochastic %D: {stoch_d:.2f}\n"
                f"• Crossover: {crossover_signal} ✓ - Bearish momentum!\n"
                f"⚠️ CRITICAL: All indicators + bearish crossover confirm strong downtrend!",
                "#ff4444"
            )
        
        # WARNING condition (all exit signals except drop percentage)
        elif drop_percent <= 18 and dma_50 < dma_200 and rsi < 40 and stoch_k < 20 and k_below_d:
            return (
                f"🟠 EXIT WARNING {ticker_symbol}",
                f"⚠️ Early exit warning - Technical breakdown detected:\n"
                f"• Drop from 52W high: {drop_percent:.2f}% (not yet >18%, currently at {drop_percent:.2f}%)\n"
                f"• 50 DMA < 200 DMA: ${dma_50:.2f} < ${dma_200:.2f} ✓ - Death Cross!\n"
                f"• RSI: {rsi:.2f} (<40 ✓) - Oversold\n"
                f"• Stochastic %K: {stoch_k:.2f} (<20 ✓) - Severely Oversold\n"
                f"• Stochastic %D: {stoch_d:.2f}\n"
                f"• Crossover: {crossover_signal} ✓ - Bearish momentum!\n"
                f"💡 Action: All technical indicators are bearish. Consider:\n"
                f"   - Tightening stop losses\n"
                f"   - Reducing position size\n"
                f"   - Preparing for potential exit if drop reaches 18%\n"
                f"⚠️ Risk: High probability of further decline - watch closely!",
                "#ff9900"
            )
        
        # TAKE PROFIT condition (with Stochastic bearish crossover)
        elif drop_percent < 5 and rsi > 70 and stoch_k > 80 and k_below_d:
            return (
                f"🟡 TAKE PROFIT {ticker_symbol}",
                f"Strong overbought signal - Consider taking profits:\n"
                f"• Near 52W high: Only {drop_percent:.2f}% below peak ✓\n"
                f"• RSI: {rsi:.2f} (>70 ✓) - OVERBOUGHT\n"
                f"• Stochastic %K: {stoch_k:.2f} (>80 ✓) - VERY OVERBOUGHT\n"
                f"• Stochastic %D: {stoch_d:.2f}\n"
                f"• Crossover: {crossover_signal} ✓ - Bearish reversal signal!\n"
                f"• RSI & Stochastic overbought + bearish crossover = Peak signal!\n"
                f"💡 Recommendation: STRONG signal to secure gains or tighten stops\n"
                f"⚠️ Risk: VERY HIGH probability of pullback - momentum turning down!",
                "#ffaa00"
            )
        
        # TAKE PROFIT WARNING (overbought but no bearish crossover yet)
        elif drop_percent < 5 and rsi > 70 and stoch_k > 80 and k_above_d:
            return (
                f"🟠 PROFIT WARNING {ticker_symbol}",
                f"⚠️ Overbought conditions - Waiting for reversal signal:\n"
                f"• Near 52W high: Only {drop_percent:.2f}% below peak ✓\n"
                f"• RSI: {rsi:.2f} (>70 ✓) - OVERBOUGHT\n"
                f"• Stochastic %K: {stoch_k:.2f} (>80 ✓) - VERY OVERBOUGHT\n"
                f"• Stochastic %D: {stoch_d:.2f}\n"
                f"• Crossover: {crossover_signal} - Still bullish but extreme!\n"
                f"• Waiting for %K to cross below %D for confirmation\n"
                f"💡 Action: Stock is very overbought. Consider:\n"
                f"   - Setting tight trailing stops\n"
                f"   - Taking partial profits\n"
                f"   - Watching for bearish crossover signal\n"
                f"⚠️ Risk: At extreme levels - reversal could happen quickly!",
                "#ff9900"
            )
        
        # RE-ENTRY condition (with Stochastic crossover)
        elif drop_percent > 30 and 35 <= rsi <= 45 and k_above_d:
            return (
                f"🟢 RE-ENTRY {ticker_symbol}",
                f"Strong re-entry signal with bullish crossover:\n"
                f"• Drop from 52W high: {drop_percent:.2f}% (>30% ✓)\n"
                f"• RSI: {rsi:.2f} (35-45 range ✓) - Neutral/Recovering\n"
                f"• Stochastic %K: {stoch_k:.2f}\n"
                f"• Stochastic %D: {stoch_d:.2f}\n"
                f"• Crossover: {crossover_signal} ✓\n"
                f"• %K crossed above %D = Bullish momentum building!\n"
                f"💡 Excellent entry point with recovering momentum",
                "#44ff44"
            )
        
        # RE-ENTRY WARNING (drop and RSI met but waiting for bullish crossover)
        elif drop_percent > 30 and 35 <= rsi <= 45 and k_below_d:
            return (
                f"🟠 ENTRY WARNING {ticker_symbol}",
                f"⚠️ Re-entry conditions almost met - Waiting for momentum:\n"
                f"• Drop from 52W high: {drop_percent:.2f}% (>30% ✓) - Good value!\n"
                f"• RSI: {rsi:.2f} (35-45 range ✓) - Neutral/Recovering\n"
                f"• Stochastic %K: {stoch_k:.2f}\n"
                f"• Stochastic %D: {stoch_d:.2f}\n"
                f"• Crossover: {crossover_signal} - Still bearish\n"
                f"• Waiting for %K to cross above %D for bullish confirmation\n"
                f"💡 Action: Entry conditions nearly perfect. Consider:\n"
                f"   - Adding to watchlist\n"
                f"   - Preparing entry orders\n"
                f"   - Watching for bullish crossover signal\n"
                f"   - May enter small position and add on crossover\n"
                f"⚠️ Patience: Wait for momentum confirmation before full entry!",
                "#ff9900"
            )
        
        # HOLD condition
        else:
            reasons = []
            if drop_percent <= 18:
                reasons.append(f"Drop only {drop_percent:.2f}% (need >18% for exit)")
            if dma_50 >= dma_200:
                reasons.append("50 DMA above 200 DMA (bullish trend)")
            if rsi >= 40 and rsi <= 70:
                reasons.append(f"RSI at {rsi:.2f} (normal range 40-70)")
            if stoch_k >= 20 and stoch_k <= 80:
                reasons.append(f"Stochastic %K at {stoch_k:.2f} (normal range 20-80)")
            elif stoch_k > 80:
                if not k_below_d:
                    reasons.append(f"Stochastic %K at {stoch_k:.2f} (overbought but no bearish crossover yet)")
                else:
                    reasons.append(f"Stochastic %K at {stoch_k:.2f} (overbought, bearish crossover but need other confirmations)")
            elif stoch_k < 20:
                if not k_below_d:
                    reasons.append(f"Stochastic %K at {stoch_k:.2f} (oversold but no bearish crossover)")
                else:
                    reasons.append(f"Stochastic %K at {stoch_k:.2f} (oversold with bearish crossover but need other confirmations)")
            if drop_percent <= 30:
                reasons.append(f"Not enough drop for re-entry ({drop_percent:.2f}% vs >30%)")
            
            # Crossover status
            if k_above_d:
                reasons.append(f"Bullish crossover (%K: {stoch_k:.2f} > %D: {stoch_d:.2f}) - good for re-entry only")
            else:
                reasons.append(f"Bearish crossover (%K: {stoch_k:.2f} < %D: {stoch_d:.2f}) - need other confirmations")
            
            return (
                f"🔵 HOLD {ticker_symbol}",
                f"Hold position - Conditions not met:\n" +
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
    print("Features: RSI + Stochastic indicators with %K/%D Crossover Analysis")
    print("=" * 60)
    print("🔴 EXIT: Full bearish confirmation with >18% drop")
    print("🟠 EXIT WARNING: Technical breakdown - prepare for exit")
    print("🟡 TAKE PROFIT: Overbought + bearish crossover = reversal")
    print("🟠 PROFIT WARNING: Overbought - watch for crossover")
    print("🟢 RE-ENTRY: Recovery + bullish crossover confirmed")
    print("🟠 ENTRY WARNING: Good setup - waiting for momentum")
    print("🔵 HOLD: Monitor and wait")
    print("=" * 60)
    
    root = tk.Tk()
    app = QQQMTradingApp(root)
    root.mainloop()