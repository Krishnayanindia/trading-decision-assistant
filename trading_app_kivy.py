import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.core.window import Window
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import threading
import time

# Set window size for testing (optional)
Window.size = (480, 800)


class TradingApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cancel_fetch = False
        self.is_fetching = False

    def build(self):
        """Build the Kivy UI"""
        self.title = "Trading Decision Assistant"

        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=5)

        # Header
        header = BoxLayout(orientation='vertical', size_hint_y=0.15, spacing=2)
        title_label = Label(
            text="🧠 Trading Decision Assistant",
            font_size='20sp',
            bold=True,
            size_hint_y=0.6
        )
        subtitle_label = Label(
            text="Real-time RSI & Stochastic Analysis",
            font_size='10sp',
            size_hint_y=0.4
        )
        header.add_widget(title_label)
        header.add_widget(subtitle_label)
        main_layout.add_widget(header)

        # Ticker selection
        ticker_layout = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=5)
        ticker_label = Label(text="Ticker:", size_hint_x=0.2)
        self.ticker_input = TextInput(
            multiline=False,
            size_hint_x=0.3,
            hint_text='Enter ticker (e.g. QQQM)'
        )

        popular_tickers = [
            "QQQM", "QQQ", "SPY", "VOO", "VTI",
            "IWM", "DIA", "EFA", "VEA", "VWO",
            "AGG", "BND", "TLT", "GLD", "SLV"
        ]

        self.ticker_spinner = Spinner(
            text="Select",
            values=popular_tickers,
            size_hint_x=0.5
        )
        self.ticker_spinner.bind(text=self.on_spinner_select)

        ticker_layout.add_widget(ticker_label)
        ticker_layout.add_widget(self.ticker_input)
        ticker_layout.add_widget(self.ticker_spinner)
        main_layout.add_widget(ticker_layout)

        # Scrollable data display
        scroll = ScrollView(size_hint=(1, 0.5))
        self.data_layout = GridLayout(
            cols=2,
            spacing=5,
            padding=5,
            size_hint_y=None
        )
        self.data_layout.bind(minimum_height=self.data_layout.setter('height'))

        # Add data labels
        self.data_labels = {}
        self.add_data_label("Current Price", "---")
        self.add_data_label("52W High", "---")
        self.add_data_label("Drop %", "---")
        self.add_data_label("50 DMA", "---")
        self.add_data_label("200 DMA", "---")
        self.add_data_label("RSI (14)", "---")
        self.add_data_label("Stoch %K", "---")
        self.add_data_label("Stoch %D", "---")

        scroll.add_widget(self.data_layout)
        main_layout.add_widget(scroll)

        # Decision display
        self.decision_label = Label(
            text="Click 'Analyze' to start",
            font_size='18sp',
            bold=True,
            size_hint_y=0.12,
            color=(0.29, 0.62, 1, 1)
        )
        main_layout.add_widget(self.decision_label)

        self.reason_label = Label(
            text="",
            font_size='10sp',
            size_hint_y=0.08,
            text_size=(400, None)
        )
        main_layout.add_widget(self.reason_label)

        # Progress bar
        self.progress_bar = ProgressBar(
            max=100,
            size_hint_y=0.05
        )
        main_layout.add_widget(self.progress_bar)

        # Buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=5)
        self.analyze_btn = Button(
            text="🔄 Analyze",
            size_hint_x=0.5
        )
        self.analyze_btn.bind(on_press=self.start_analysis)

        self.refresh_btn = Button(
            text="♻️ Auto-Refresh",
            size_hint_x=0.5,
            background_color=(0.3, 0.3, 0.3, 1)
        )
        self.refresh_btn.bind(on_press=self.toggle_auto_refresh)

        button_layout.add_widget(self.analyze_btn)
        button_layout.add_widget(self.refresh_btn)
        main_layout.add_widget(button_layout)

        # Status bar
        self.status_label = Label(
            text="Ready",
            font_size='9sp',
            size_hint_y=0.05
        )
        main_layout.add_widget(self.status_label)

        self.auto_refresh = False
        self.refresh_job = None

        return main_layout

    def add_data_label(self, label_text, value_text):
        """Add a data label to the display"""
        label = Label(text=label_text, size_hint_y=None, height=40, bold=True)
        value = Label(text=value_text, size_hint_y=None, height=40)
        self.data_layout.add_widget(label)
        self.data_layout.add_widget(value)
        self.data_labels[label_text] = value

    def on_spinner_select(self, spinner, text):
        """Update ticker input when spinner selection changes"""
        if text != "Select":
            self.ticker_input.text = text

    def calculate_rsi(self, data, periods=14):
        """Calculate RSI indicator"""
        close = data['Close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()

        rs = gain / loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))

        rsi_value = rsi.iloc[-1]
        if pd.isna(rsi_value):
            return 50.0

        return float(rsi_value)

    def calculate_stochastic(self, data, k_period=14, d_period=3):
        """Calculate Stochastic oscillator"""
        close = data['Close']
        low = data['Low']
        high = data['High']

        low_min = low.rolling(window=k_period).min()
        high_max = high.rolling(window=k_period).max()

        denominator = high_max - low_min
        denominator = denominator.replace(0, 1e-10)

        stoch_k = 100 * (close - low_min) / denominator
        stoch_d = stoch_k.rolling(window=d_period).mean()

        k_value = stoch_k.iloc[-1]
        d_value = stoch_d.iloc[-1]

        if pd.isna(k_value):
            k_value = 50.0
        if pd.isna(d_value):
            d_value = 50.0

        return float(k_value), float(d_value)

    def fetch_and_analyze(self):
        """Fetch data and analyze"""
        self.is_fetching = True
        self.cancel_fetch = False

        try:
            ticker_symbol = self.ticker_input.text.strip().upper()

            if not ticker_symbol:
                self.show_error("Please enter a ticker symbol")
                return

            # Update UI
            self.decision_label.text = "FETCHING DATA..."
            self.status_label.text = f"⏳ Downloading {ticker_symbol}..."
            self.progress_bar.value = 30

            print(f"\n{'='*60}")
            print(f"Fetching data for: {ticker_symbol}")
            print(f"{'='*60}")

            # Download data with error handling
            try:
                data = yf.download(ticker_symbol, period="1y", progress=False, threads=False)
                print(f"Downloaded data shape: {data.shape}")
                print(f"Data columns: {list(data.columns)}")
            except Exception as e:
                print(f"ERROR downloading data: {e}")
                self.show_error(f"Failed to download data: {str(e)}")
                return

            # Fix MultiIndex columns
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            # Ensure required columns exist
            required_cols = ['Close', 'High', 'Low']
            if not all(col in data.columns for col in required_cols):
                print(f"Missing columns. Available: {list(data.columns)}")
                self.show_error(f"Invalid data structure for {ticker_symbol}")
                return

            if data.empty or len(data) == 0:
                self.show_error(f"No data found for {ticker_symbol}. Check if ticker is valid.")
                return

            self.progress_bar.value = 60
            self.status_label.text = "⏳ Calculating indicators..."

            # Calculate metrics
            current_price = float(data['Close'].iloc[-1])
            week_52_high = float(data['High'].max())
            drop_percent = ((week_52_high - current_price) / week_52_high) * 100

            if len(data) < 200:
                self.show_error(f"Insufficient data: {len(data)} days")
                return

            dma_50 = float(data['Close'].rolling(window=50).mean().iloc[-1])
            dma_200 = float(data['Close'].rolling(window=200).mean().iloc[-1])
            rsi = float(self.calculate_rsi(data))
            stoch_k, stoch_d = self.calculate_stochastic(data)

            self.progress_bar.value = 90

            # Update UI with results
            self.update_ui(
                ticker_symbol, current_price, week_52_high, drop_percent,
                dma_50, dma_200, rsi, stoch_k, stoch_d
            )

            self.progress_bar.value = 100
            self.status_label.text = f"✓ {ticker_symbol} updated: {datetime.now().strftime('%H:%M:%S')}"

        except Exception as e:
            self.show_error(str(e))

        finally:
            self.is_fetching = False

    def update_ui(self, ticker_symbol, current_price, week_52_high, drop_percent, dma_50, dma_200, rsi, stoch_k, stoch_d):
        """Update UI with calculated values"""
        self.data_labels["Current Price"].text = f"${current_price:.2f}"
        self.data_labels["52W High"].text = f"${week_52_high:.2f}"
        self.data_labels["Drop %"].text = f"{drop_percent:.2f}%"
        self.data_labels["50 DMA"].text = f"${dma_50:.2f}"
        self.data_labels["200 DMA"].text = f"${dma_200:.2f}"
        self.data_labels["RSI (14)"].text = f"{rsi:.2f}"
        self.data_labels["Stoch %K"].text = f"{stoch_k:.2f}"
        self.data_labels["Stoch %D"].text = f"{stoch_d:.2f}"

        decision, reason, color = self.apply_trading_logic(
            ticker_symbol, drop_percent, dma_50, dma_200, rsi, stoch_k, stoch_d
        )

        self.decision_label.text = decision
        self.decision_label.color = color
        self.reason_label.text = reason

    def apply_trading_logic(self, ticker_symbol, drop_percent, dma_50, dma_200, rsi, stoch_k, stoch_d):
        """Apply trading logic"""
        k_above_d = stoch_k > stoch_d
        k_below_d = stoch_k < stoch_d

        # EXIT
        if drop_percent > 18 and dma_50 < dma_200 and rsi < 40 and stoch_k < 20 and k_below_d:
            return (
                f"🔴 EXIT {ticker_symbol}",
                f"All indicators confirm exit:\nDrop: {drop_percent:.2f}%\nRSI: {rsi:.2f}\nStoch %K: {stoch_k:.2f}",
                (1, 0.27, 0.27, 1)
            )

        # EXIT WARNING
        elif drop_percent <= 18 and dma_50 < dma_200 and rsi < 40 and stoch_k < 20 and k_below_d:
            return (
                f"🟠 EXIT WARNING {ticker_symbol}",
                f"Technical breakdown detected.\nPrepare for exit.\nDrop: {drop_percent:.2f}%",
                (1, 0.65, 0, 1)
            )

        # TAKE PROFIT
        elif drop_percent < 5 and rsi > 70 and stoch_k > 80 and k_below_d:
            return (
                f"🟡 TAKE PROFIT {ticker_symbol}",
                f"Overbought + bearish crossover.\nConsider taking profits.\nRSI: {rsi:.2f}",
                (1, 0.84, 0, 1)
            )

        # PROFIT WARNING
        elif drop_percent < 5 and rsi > 70 and stoch_k > 80 and k_above_d:
            return (
                f"🟠 PROFIT WARNING {ticker_symbol}",
                f"Overbought - wait for crossover.\nRSI: {rsi:.2f}\nStoch %K: {stoch_k:.2f}",
                (1, 0.65, 0, 1)
            )

        # RE-ENTRY
        elif drop_percent > 30 and 35 <= rsi <= 45 and k_above_d:
            return (
                f"🟢 RE-ENTRY {ticker_symbol}",
                f"Strong entry signal.\nDrop: {drop_percent:.2f}%\nBullish crossover confirmed",
                (0.27, 1, 0.27, 1)
            )

        # ENTRY WARNING
        elif drop_percent > 30 and 35 <= rsi <= 45 and k_below_d:
            return (
                f"🟠 ENTRY WARNING {ticker_symbol}",
                f"Entry conditions nearly met.\nWaiting for bullish crossover.\nDrop: {drop_percent:.2f}%",
                (1, 0.65, 0, 1)
            )

        # HOLD
        else:
            return (
                f"🔵 HOLD {ticker_symbol}",
                f"Hold position.\nRSI: {rsi:.2f}\nStoch %K: {stoch_k:.2f}\nDrop: {drop_percent:.2f}%",
                (0.29, 0.62, 1, 1)
            )

    def show_error(self, message):
        """Show error message"""
        self.decision_label.text = "ERROR"
        self.decision_label.color = (1, 0.27, 0.27, 1)
        self.reason_label.text = f"Error: {message}"
        self.status_label.text = f"❌ {message[:40]}"
        self.progress_bar.value = 0

    def start_analysis(self, *args):
        """Start analysis in a thread"""
        if self.is_fetching:
            return

        self.analyze_btn.disabled = True
        self.progress_bar.value = 0
        thread = threading.Thread(target=self.fetch_and_analyze, daemon=True)
        thread.start()
        self.analyze_btn.disabled = False

    def toggle_auto_refresh(self, *args):
        """Toggle auto-refresh"""
        self.auto_refresh = not self.auto_refresh

        if self.auto_refresh:
            self.refresh_btn.background_color = (0.27, 1, 0.27, 1)
            self.refresh_btn.color = (0, 0, 0, 1)
            self.auto_refresh_cycle()
        else:
            self.refresh_btn.background_color = (0.3, 0.3, 0.3, 1)
            self.refresh_btn.color = (1, 1, 1, 1)

    def auto_refresh_cycle(self):
        """Auto-refresh cycle (30 seconds)"""
        if self.auto_refresh:
            self.start_analysis()
            self.refresh_job = threading.Timer(30, self.auto_refresh_cycle)
            self.refresh_job.daemon = True
            self.refresh_job.start()


if __name__ == '__main__':
    TradingApp().run()
