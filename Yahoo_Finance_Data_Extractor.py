import yfinance as yf
import tkinter as tk
from tkinter import filedialog
import os

# Download NIFTY 50 (^NSEI) data for the last 15 years
print("Downloading 15 years of NIFTY 50 data...")
df = yf.download("^NSEI", start="2010-10-15", end="2025-10-16", progress=False)

# Open a file dialog to let the user choose where to save the CSV
root = tk.Tk()
root.withdraw()  # hide main tkinter window

save_path = filedialog.asksaveasfilename(
    title="Save NIFTY 50 data as...",
    defaultextension=".csv",
    filetypes=[("CSV files", "*.csv")],
    initialfile="nsei.csv"
)

if save_path:
    df.to_csv(save_path)
    print(f"✅ Data saved successfully at: {os.path.abspath(save_path)}")
else:
    print("❌ Save cancelled. File not saved.")
