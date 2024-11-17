import requests
import tkinter as tk
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import threading
from decimal import Decimal

# Binance API endpoint for the latest prices of all trading pairs
price_url = "https://api.binance.com/api/v3/ticker/price"
klines_url = "https://api.binance.com/api/v3/klines"

pairs = ["BTCUSDT", "ETHUSDT", "ENAUSDT", "ADAUSDT", "SOLUSDT", "AGLDUSDT"]

# Creating main application window
app = tk.Tk()
app.withdraw() 

# Create a transparent floating window
floating_window = tk.Toplevel(app)
floating_window.title("Crypto Prices")
floating_window.geometry("200x300")
floating_window.attributes("-topmost", True)      
floating_window.attributes("-alpha", 0.8)         
floating_window.overrideredirect(True)           
floating_window.configure(bg="white")          

# Variables to track dragging
drag_data = {"x": 0, "y": 0}

# Dictionary to store label widgets for each pair
price_labels = {}
cool_text_color = "#000000"  # White text color

volume_canvases = {}
previous_day_volumes = {}

# Create a label for each pair and add it to the dictionary
for pair in pairs:
    frame = tk.Frame(floating_window, bg="white")
    frame.pack(pady=3, fill="x")

    # Label for price and volume information
    label = tk.Label(frame, text=f"{pair}: Fetching...", font=("Arial", 9), fg="#000000", bg="white")
    label.pack(side="left")
    price_labels[pair] = label

    # Canvas for volume bar
    canvas = tk.Canvas(frame, width=10, height=30, bg="lightgray", bd=0, highlightthickness=0)
    canvas.pack(side="right")
    volume_canvases[pair] = canvas

# Function to get the current price for a pair
def get_current_price(pair):
    response = requests.get(price_url, params={"symbol": pair})
    if response.status_code == 200:
        data = response.json()
        return data['price']
    return None

# Function to get the Kline (OHLCV) data for a pair
def get_klines(pair, interval="1d"):
    response = requests.get(klines_url, params={"symbol": pair, "interval": interval, "limit": 1})
    if response.status_code == 200:
        data = response.json()
        kline = data[0]
        high_price = kline[2]  # High price
        low_price = kline[3]   # Low price
        volume = kline[5]  # Volume
        return high_price, low_price, volume
    return None

# Function to get the previous day's volume
def get_previous_day_volume(pair):
    response = requests.get(klines_url, params={"symbol": pair, "interval": "1d", "limit": 2})
    if response.status_code == 200:
        data = response.json()
        previous_day_kline = data[-2]  # Second to last Kline for the previous day
        previous_day_volume = float(previous_day_kline[5])
        return previous_day_volume
    return None

# Function to get the 5-minute volume for a pair
def get_5min_volume(pair):
    response = requests.get(klines_url, params={"symbol": pair, "interval": "5m", "limit": 1})
    if response.status_code == 200:
        data = response.json()
        kline = data[0]
        volume = float(kline[5])  # 5-minute volume
        return volume
    return None

# Function to normalize the volume to fit the bar
def normalize_volume(volume, max_volume):
    # Normalize based on the max volume value and target height of the volume bar
    return (volume / max_volume) * 30

# Function to update the prices
previous_prices = {pair: None for pair in pairs}

def normalize_price(value):
    return Decimal(value).normalize()

# Function to update the prices
def update_prices():
    for pair in pairs:
        price = get_current_price(pair)
        klines = get_klines(pair)
        volume = get_5min_volume(pair)

        if pair not in previous_day_volumes:
            previous_day_volume = get_previous_day_volume(pair)
            previous_day_volumes[pair] = previous_day_volume * 0.01

        max_volume = previous_day_volumes[pair]

        if price and klines and volume is not None:
            high_price, low_price, _ = klines

            # Normalize the prices to remove unnecessary zeros
            price = normalize_price(price)
            high_price = normalize_price(high_price)
            low_price = normalize_price(low_price)

            # Determine the text color based on the price change
            if previous_prices[pair] is not None:
                if price > previous_prices[pair]:
                    text_color = "green"  # Price went up
                elif price < previous_prices[pair]:
                    text_color = "red"    # Price went down
                else:
                    text_color = "black"  # Price stayed the same
            else:
                text_color = "black"  # For the first update (no previous price)

            # Update the label with the formatted text and color
            price_labels[pair].config(
                text=f"{pair}: {price}\nH: {high_price} L: {low_price}",
                fg=text_color
            )

            # Normalize volume and update the volume bar with dynamic color
            normalized_volume = normalize_volume(volume, max_volume)

            # Clear previous bar and draw the new volume bar with green color
            volume_canvases[pair].delete("all")
            volume_canvases[pair].create_rectangle(0, 30 - normalized_volume, 20, 30, fill="green")

            # Update the previous price for the next comparison
            previous_prices[pair] = price
        else:
            price_labels[pair].config(text=f"{pair}: Data fetch failed")

    # Schedule the function to run again after 500 ms (0.5 seconds)
    app.after(500, update_prices)

# Function to create the system tray icon
def create_tray_icon():
    icon_image = Image.new("RGB", (64, 64), "green")
    draw = ImageDraw.Draw(icon_image)
    draw.ellipse((16, 16, 48, 48), fill="blue")

    menu = Menu(
        MenuItem("Show", lambda: show_window()),
        MenuItem("Hide", lambda: hide_window()),
        MenuItem("Exit", lambda: exit_app())
    )

    icon = Icon("Crypto Prices", icon_image, menu=menu)
    icon.run()

# Function to show the floating window
def show_window():
    floating_window.deiconify()

# Function to hide the floating window
def hide_window():
    floating_window.withdraw()

# Function to exit the application
def exit_app():
    floating_window.destroy()
    app.quit()

def hideWindow(event):
    floating_window.withdraw()

# Dragging functions
def on_drag_start(event):
    drag_data["x"] = event.x
    drag_data["y"] = event.y

def on_drag_motion(event):
    dx = event.x - drag_data["x"]
    dy = event.y - drag_data["y"]
    new_x = floating_window.winfo_x() + dx
    new_y = floating_window.winfo_y() + dy

    if abs(dx) > 1 or abs(dy) > 1:
        floating_window.geometry(f"+{new_x}+{new_y}")

    drag_data["x"] = event.x
    drag_data["y"] = event.y

floating_window.bind("<Button-1>", on_drag_start)
floating_window.bind("<B1-Motion>", on_drag_motion)
floating_window.bind("<Button-3>", hideWindow)

# Start the system tray icon in a separate thread
icon_thread = threading.Thread(target=create_tray_icon, daemon=True)
icon_thread.start()

# Start the first price update
update_prices()

# Run the application
app.mainloop()
