import MetaTrader5 as mt5
import mplfinance as mpf
from dotenv import load_dotenv
import pandas as pd
import os
from datetime import datetime, timedelta
import shutil
import matplotlib.pyplot as plt
import random

# Load environment variables for MT5 login credentials
load_dotenv()
login = int(os.getenv('MT5_LOGIN'))  # Replace with your login ID
password = os.getenv('MT5_PASSWORD')  # Replace with your password
server = os.getenv('MT5_SERVER')  # Replace with your server name

# Initialize MetaTrader 5 connection
if not mt5.initialize(login=login, password=password, server=server):
    print("Failed to initialize MT5, error code:", mt5.last_error())
    quit()

# Define symbols and split into two groups
symbols = [
    "EURUSD", "GBPUSD", "USDCHF", "USDJPY", "USDCAD",
    "AUDUSD", "AUDNZD", "AUDCAD", "AUDCHF", "AUDJPY",
    "NZDUSD", "CHFJPY", "EURGBP", "EURAUD", "EURCHF",
    "EURJPY", "EURNZD", "EURCAD", "GBPCHF", "GBPJPY",
    "CADCHF", "CADJPY", "GBPAUD", "GBPCAD", "GBPNZD",
    "NZDCAD", "NZDCHF", "NZDJPY"
]

# Split symbols into two groups (14 for training/validation, 14 for testing)
train_val_symbols = symbols[:14]  # First 14 symbols
test_symbols = symbols[14:]       # Remaining 14 symbols

# Define parameters
timeframe = mt5.TIMEFRAME_H1  # 1-hour timeframe
interval = timedelta(hours=17)  # Data interval per image

# Output directories
output_dir = "output"
output_train_val_dir = os.path.join(output_dir, "output_hourly_price_action_patterns_training_and_validation")
output_test_dir = os.path.join(output_dir, "output_hourly_price_action_patterns_testing")
screenshots_dir = "temporary_screenshots"
debug_log_file = os.path.join(output_dir, "debug_log.txt")

# Ensure necessary directories exist
os.makedirs(output_train_val_dir, exist_ok=True)
os.makedirs(output_test_dir, exist_ok=True)
os.makedirs(screenshots_dir, exist_ok=True)

def breakout_identify(df):
    """
    Analyze 12 candles to identify if there is a bullish or bearish breakout
    based on the last 4 candles. Additionally, checks if the next 5 candles
    continue the breakout trend.
    """
    if len(df) < 17:
        return "not_enough_data"

    # Extract the relevant data
    last_12 = df.iloc[-17:-5]  # First 12 candles, excluding the last 5
    next_5 = df.iloc[-5:]      # Next 5 candles for breakout continuation check

    # Calculate resistance and support levels based on the first 8 candles
    prior_8_candles = last_12.iloc[:-4]
    resistance = prior_8_candles['high'].max()
    support = prior_8_candles['low'].min()

    # Last 4 candles to check for breakout
    last_4_closes = last_12['close'].iloc[-4:]

    # Check for bullish breakout
    if all(last_4_closes > resistance):  # All last 4 closes are above resistance
        if all(next_5['close'] > resistance):  # Next 5 continue upward
            return "bullish_breakout"
        else:
            return "false_bullish_breakout"

    # Check for bearish breakout
    if all(last_4_closes < support):  # All last 4 closes are below support
        if all(next_5['close'] < support):  # Next 5 continue downward
            return "bearish_breakout"
        else:
            return "false_bearish_breakout"

    # No breakout detected
    return "no_breakout"

def save_candlestick_chart(df, filename, num_candles=12):
    """
    Save a candlestick chart showing only the last `num_candles` candles,
    excluding the next 5 candles used for breakout confirmation.
    """
    # Ensure only the relevant candles (last 12) are visible
    df = df.iloc[-17:-5]  # Exclude the "next 5" candles for the chart

    # Ensure the DataFrame has the necessary columns and no NaN values
    df = df[['open', 'high', 'low', 'close']].apply(pd.to_numeric, errors='coerce').dropna()

    # Plot the candlestick chart
    fig, ax = plt.subplots()
    mpf.plot(df, type='candle', style='charles', ax=ax)

    # Remove axis visibility and spines for a cleaner chart
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    # Save the chart to the specified filename
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

# Time range: last 5 years
start_date = datetime.now() - timedelta(days=365 * 5)
end_date = datetime.now()

# Process training/validation symbols
for symbol in train_val_symbols:
    print(f"Processing train/validation symbol: {symbol}")

    current_date = start_date
    while current_date < end_date:
        next_date = current_date + interval
        main_filename = os.path.join(screenshots_dir, f"{symbol}_{current_date.strftime('%Y%m%d%H%M')}.png")
        df = get_rates(symbol, timeframe, current_date, next_date)
        if df is not None and len(df) >= interval.total_seconds() / 3600:
            save_candlestick_chart(df, main_filename)
            pattern_label = breakout_identify(df)
            if pattern_label:
                # 80% training, 20% validation
                destination_dir = (
                    os.path.join(output_train_val_dir, "train") 
                    if random.random() < 0.8 
                    else os.path.join(output_train_val_dir, "validation")
                )
                label_dir = os.path.join(destination_dir, pattern_label)
                os.makedirs(label_dir, exist_ok=True)
                shutil.move(main_filename, os.path.join(label_dir, os.path.basename(main_filename)))
        current_date = next_date

# Process testing symbols
for symbol in test_symbols:
    print(f"Processing test symbol: {symbol}")

    current_date = start_date
    while current_date < end_date:
        next_date = current_date + interval
        main_filename = os.path.join(screenshots_dir, f"{symbol}_{current_date.strftime('%Y%m%d%H%M')}.png")
        df = get_rates(symbol, timeframe, current_date, next_date)
        if df is not None and len(df) >= interval.total_seconds() / 3600:
            save_candlestick_chart(df, main_filename)
            pattern_label = breakout_identify(df)
            if pattern_label:
                test_dir = os.path.join(output_test_dir, "test")
                os.makedirs(test_dir, exist_ok=True)
                label_dir = os.path.join(test_dir, pattern_label)
                os.makedirs(label_dir, exist_ok=True)
                shutil.move(main_filename, os.path.join(label_dir, os.path.basename(main_filename)))
        current_date = next_date

# Cleanup
shutil.rmtree(screenshots_dir)
mt5.shutdown()