import MetaTrader5 as mt5
import mplfinance as mpf
from dotenv import load_dotenv
import pandas as pd
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Load environment variables for MT5 login credentials
load_dotenv()
login = int(os.getenv('MT5_LOGIN'))  # Replace with your login ID
password = os.getenv('MT5_PASSWORD')  # Replace with your password
server = os.getenv('MT5_SERVER')  # Replace with your server name

# Initialize MetaTrader 5 connection
if not mt5.initialize(login=login, password=password, server=server):
    print("Failed to initialize MT5, error code:", mt5.last_error())
    quit()

# Define symbols to process
symbols_to_process = ['AUDJPY', 'CHFJPY', 'EURGBP', 'EURAUD', 'EURJPY', 'EURNZD', 'CADCHF', 'GBPAUD', 'NZDCAD', 'NZDCHF', 'NZDJPY']

def save_candlestick_chart(df, filename):
    """
    Save a candlestick chart showing only the last 12 candles.
    """
    df = df.iloc[-17:-5]  # Select the last 12 candles
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

# Define parameters
timeframe = mt5.TIMEFRAME_M5

# Output directories
output_dir = "output_specific_symbols_multiple_pairs"
os.makedirs(output_dir, exist_ok=True)

def get_rates(symbol, timeframe, start, end):
    """
    Retrieve rates from MetaTrader 5 and return as a DataFrame.
    """
    rates = mt5.copy_rates_range(symbol, timeframe, start, end)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    return df

# Time range
start_date = datetime.now() - timedelta(days=365)  # Last 1 year
end_date = datetime.now()

# Process each symbol
for symbol in symbols_to_process:
    print(f"Processing: {symbol} - Current time: {datetime.now()}")
    symbol_dir = os.path.join(output_dir, symbol)
    data_dir = os.path.join(symbol_dir, "data")
    charts_dir = os.path.join(symbol_dir, "charts")

    # Create separate folders for charts, data, and future charts
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(charts_dir, exist_ok=True)

    # Retrieve the full data for the symbol
    df = get_rates(symbol, timeframe, start_date, end_date)
    if df is not None:
        # Iterate through intervals and save the charts
        current_date = start_date
        while current_date + timedelta(minutes=85) <= end_date:
            # Select the 17 candles for the current interval
            interval_data = df.loc[current_date:current_date + timedelta(minutes=85)]
            if len(interval_data) >= 17:
                # Save the full 17-candle chart
                interval_data_path = os.path.join(data_dir, f"{symbol}_{current_date.strftime('%Y%m%d%H%M')}.csv")
                interval_data.to_csv(interval_data_path, index=True)

                # Save the last 12-candle chart
                chart_filename = os.path.join(charts_dir, f"{symbol}_{current_date.strftime('%Y%m%d%H%M')}.png")
                save_candlestick_chart(interval_data, chart_filename)

            current_date += timedelta(minutes=85)

# Shutdown MT5 connection
mt5.shutdown()