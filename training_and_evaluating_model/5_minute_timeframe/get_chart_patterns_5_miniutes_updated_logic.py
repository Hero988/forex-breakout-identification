import MetaTrader5 as mt5
import mplfinance as mpf
from dotenv import load_dotenv
import pandas as pd
import os
from datetime import datetime, timedelta
import shutil
import matplotlib.pyplot as plt
import random
import time

# Load environment variables for MT5 login credentials
load_dotenv()
login = int(os.getenv('MT5_LOGIN'))  # Replace with your login ID
password = os.getenv('MT5_PASSWORD')  # Replace with your password
server = os.getenv('MT5_SERVER')  # Replace with your server name

# Initialize MetaTrader 5 connection
if not mt5.initialize(login=login, password=password, server=server):
    print("Failed to initialize MT5, error code:", mt5.last_error())
    quit()

# Define symbols and randomly assign to train/validation or test
symbols = [
    "EURUSD", "GBPUSD", "USDCHF", "USDJPY", "USDCAD",
    "AUDUSD", "AUDNZD", "AUDCAD", "AUDCHF", "AUDJPY",
    "NZDUSD", "CHFJPY", "EURGBP", "EURAUD", "EURCHF",
    "EURJPY", "EURNZD", "EURCAD", "GBPCHF", "GBPJPY",
    "CADCHF", "CADJPY", "GBPAUD", "GBPCAD", "GBPNZD",
    "NZDCAD", "NZDCHF", "NZDJPY"
]

# Define parameters
timeframe = mt5.TIMEFRAME_M5
interval = timedelta(minutes=85)

# Output directories
output_dir = "output"
output_future_dir = os.path.join(output_dir, "output_future")
output_train_val_dir = os.path.join(output_dir, "output_hourly_price_action_patterns_training_and_validation")
output_test_dir = os.path.join(output_dir, "output_hourly_price_action_patterns_testing")
screenshots_dir = "temporary_screenshots"
debug_log_file = os.path.join(output_dir, "debug_log.txt")

# Limits for samples
bullish_limit = 1000
bearish_limit = 1000

# Ensure necessary directories exist
os.makedirs(output_train_val_dir, exist_ok=True)
os.makedirs(output_test_dir, exist_ok=True)
os.makedirs(screenshots_dir, exist_ok=True)

def breakout_identify(df):
    """
    Analyze 12 candles to identify if there is a bullish or bearish breakout.
    """
    if len(df) < 17:
        return "not_enough_data"

    # Extract the relevant data
    last_12 = df.iloc[-17:-5]
    next_5 = df.iloc[-5:]
    prior_8_candles = last_12.iloc[:-4]
    
    # Resistance and support levels based on the first 8 candles
    resistance = prior_8_candles['high'].max()
    support = prior_8_candles['low'].min()
    
    # Last 4 candles data
    last_4_highs = last_12['high'].iloc[-4:]
    last_high_of_last_4 = last_4_highs.iloc[-1]  # High of the last candle in the last 4 candles

    # Last 4 candles data
    last_4_lows = last_12['low'].iloc[-4:]
    last_low_of_last_4 = last_4_lows.iloc[-1]  # High of the last candle in the last 4 candles

    last_4_closes = last_12['close'].iloc[-4:]
    last_close_of_last_4 = last_4_closes.iloc[-1]  # Close of the last candle in the last 4 candles
    
    # Latest candle from the next 5 candles
    latest_close_of_next_5 = next_5['close'].iloc[-1]  # Close of the latest (5th) candle

    # Check for bullish breakout: latest close of the latest next 5 > high of the last of last 4
    if latest_close_of_next_5 > last_high_of_last_4 and last_close_of_last_4 > resistance:
        return "bullish_breakout"

    # Check for bearish breakout: latest close of the latest next 5 < low of the last of last 4
    if latest_close_of_next_5 < last_low_of_last_4 and last_close_of_last_4 < support:
        return "bearish_breakout"

    # No breakout detected
    return "no_breakout"

def adjust_no_breakout_folder(breakout_dir):
    """
    Ensure the "no_breakout" folder matches the length of the "bullish_breakout" 
    and "bearish_breakout" folders. Excess files are deleted randomly.
    """
    bullish_path = os.path.join(breakout_dir, "bullish_breakout")
    bearish_path = os.path.join(breakout_dir, "bearish_breakout")
    no_breakout_path = os.path.join(breakout_dir, "no_breakout")

    bullish_count = len(os.listdir(bullish_path)) if os.path.exists(bullish_path) else 0
    bearish_count = len(os.listdir(bearish_path)) if os.path.exists(bearish_path) else 0
    no_breakout_count = len(os.listdir(no_breakout_path)) if os.path.exists(no_breakout_path) else 0

    target_count = max(bullish_count, bearish_count)

    if no_breakout_count > target_count:
        excess_files = random.sample(os.listdir(no_breakout_path), no_breakout_count - target_count)
        for file in excess_files:
            file_path = os.path.join(no_breakout_path, file)
            os.remove(file_path)

def save_candlestick_chart(df, filename, num_candles=12):
    """
    Save a candlestick chart showing only the last `num_candles` candles.
    """
    df = df.iloc[-17:-5]
    df = df[['open', 'high', 'low', 'close']].apply(pd.to_numeric, errors='coerce').dropna()
    fig, ax = plt.subplots()
    mpf.plot(df, type='candle', style='charles', ax=ax)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    plt.savefig(filename, dpi=100, bbox_inches='tight', pad_inches=0)
    plt.close()

def save_full_chart(df, filename):
    """
    Save a candlestick chart showing all 17 candles, including the next 5.
    """
    df = df[['open', 'high', 'low', 'close']].apply(pd.to_numeric, errors='coerce').dropna()
    fig, ax = plt.subplots()
    mpf.plot(df, type='candle', style='charles', ax=ax)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    plt.savefig(filename, dpi=100, bbox_inches='tight', pad_inches=0)
    plt.close()

def get_rates(symbol, timeframe, start, end):
    rates = mt5.copy_rates_range(symbol, timeframe, start, end)
    if rates is None or len(rates) == 0:
        with open(debug_log_file, "a") as log:
            log.write(f"No data for {symbol} from {start} to {end}.\n")
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    return df

def get_label_counts(output_dir, label):
    """
    Count the number of files for a specific label in training, validation, and testing directories.
    """
    train_count = len(os.listdir(os.path.join(output_train_val_dir, "train", label))) if os.path.exists(
        os.path.join(output_train_val_dir, "train", label)) else 0
    val_count = len(os.listdir(os.path.join(output_train_val_dir, "validation", label))) if os.path.exists(
        os.path.join(output_train_val_dir, "validation", label)) else 0
    test_count = len(os.listdir(os.path.join(output_test_dir, "test", label))) if os.path.exists(
        os.path.join(output_test_dir, "test", label)) else 0
    return train_count, val_count, test_count

start_date = datetime.now() - timedelta(days=365 * 1)  # Time range: last 1 year
end_date = datetime.now()

val_bullish_count = 0
test_bullish_count = 0
val_bearish_count = 0
test_bearish_count = 0
train_bullish_count = 0
train_bearish_count = 0

# Keep track of used symbols
used_symbols = set()

# Processing loop
# Iterate randomly over symbols, ensuring no duplicates
for _ in range(len(symbols)):
    remaining_symbols = list(set(symbols) - used_symbols)
    if not remaining_symbols:
        break  # Exit if no symbols are left
    symbol = random.choice(remaining_symbols)  # Randomly pick a symbol from the remaining ones
    used_symbols.add(symbol)  # Mark the symbol as used
    print(
        f"Processing: {symbol} - Current time: {datetime.now()} | "
        f"Train Bullish: {train_bullish_count}, Val Bullish: {val_bullish_count}, Test Bullish: {test_bullish_count} | "
        f"Train Bearish: {train_bearish_count}, Val Bearish: {val_bearish_count}, Test Bearish: {test_bearish_count}"
    )
    current_date = start_date

    while current_date < end_date:
        next_date = current_date + interval
        main_filename = os.path.join(screenshots_dir, f"{symbol}_{current_date.strftime('%Y%m%d%H%M')}.png")
        future_filename = os.path.join(screenshots_dir, f"future_{symbol}_{current_date.strftime('%Y%m%d%H%M')}.png")
        df = get_rates(symbol, timeframe, current_date, next_date)

        if df is not None and len(df) >= 17:
            save_candlestick_chart(df, main_filename)
            save_full_chart(df, future_filename)

            pattern_label = breakout_identify(df)
            if pattern_label != "not_enough_data":
                destination_dir = (
                    os.path.join(output_train_val_dir, "train")
                    if random.random() < 0.5
                    else os.path.join(output_train_val_dir, "validation")
                    if random.random() < 0.5
                    else os.path.join(output_test_dir, "test")
                )
                future_destination_dir = destination_dir.replace(output_dir, output_future_dir)

                label_dir = os.path.join(destination_dir, pattern_label)
                os.makedirs(label_dir, exist_ok=True)
                shutil.move(main_filename, os.path.join(label_dir, os.path.basename(main_filename)))

                future_label_dir = os.path.join(future_destination_dir, pattern_label)
                os.makedirs(future_label_dir, exist_ok=True)
                shutil.move(future_filename, os.path.join(future_label_dir, os.path.basename(future_filename)))

                adjust_no_breakout_folder(destination_dir)
                adjust_no_breakout_folder(future_destination_dir)  # Apply to future folder

            train_bullish_count, val_bullish_count, test_bullish_count = get_label_counts(output_dir, "bullish_breakout")
            train_bearish_count, val_bearish_count, test_bearish_count = get_label_counts(output_dir, "bearish_breakout")

            if (
                val_bullish_count >= bullish_limit
                and test_bullish_count >= bullish_limit
                and val_bearish_count >= bearish_limit
                and test_bearish_count >= bearish_limit
                and train_bullish_count >= bullish_limit
                and train_bearish_count >= bearish_limit
            ):
                print("Limits reached, stopping loop.")
                break
        current_date = next_date

# Cleanup
shutil.rmtree(screenshots_dir)
mt5.shutdown()
