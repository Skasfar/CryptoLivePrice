import requests
import tkinter as tk
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import threading
from decimal import Decimal

# Binance API endpoint for the latest prices of all trading pairs
price_url = "https://api.binance.com/api/v3/ticker/price"
klines_url = "https://api.binance.com/api/v3/klines"

pairs = ["BTCUSDT", "ETHUSDT", "ENAUSDT", "ADAUSDT", "SOLUSDT","AGLDUSDT"]

# Creating main application window
app = tk.Tk()
app.withdraw() 

# Create a transparent floating window
floating_window = tk.Toplevel(app)
floating_window.title("Crypto Prices")
floating_window.geometry("500x200")
floating_window.attributes("-topmost", True)      
floating_window.attributes("-alpha", 0.1)         
floating_window.overrideredirect(True)           
floating_window.configure(bg="black")          

# Variables to track dragging
drag_data = {"x": 0, "y": 0}

# Dictionary to store label widgets for each pair
price_labels = {}
cool_text_color = "#8BDC49"  # White text color

# Create a label for each pair and add it to the dictionary
for pair in pairs:
    label = tk.Label(floating_window, text=f"{pair}: Fetching...", font=("Arial", 12), fg=cool_text_color, bg="black")
    label.pack(pady=5)
    price_labels[pair] = label
    
    
# Function to get the current price for a pair
def get_current_price(pair):
    response = requests.get(price_url, params={"symbol": pair})
    if response.status_code == 200:
        data = response.json()
        return data['price']
    return None

# Function to get the Kline (OHLCV) data for a pair
def get_klines(pair):
    response = requests.get(klines_url, params={"symbol": pair, "interval": "1d", "limit": 1})
    if response.status_code == 200:
        data = response.json()
        # Extracting Open, High, Low, Close, Volume (OHLCV) for the most recent candlestick
        kline = data[0]
        # open_price = kline[1]  # Open price
        high_price = kline[2]  # High price
        low_price = kline[3]   # Low price
        # close_price = kline[4] # Close price
        # volume = kline[5]      # Volume traded
        return  high_price, low_price
    return None


# Function to update the prices
def update_prices():
   for pair in pairs:
        price = get_current_price(pair)
        klines = get_klines(pair)

        if price and klines:
            high_price, low_price = klines
            price_labels[pair].config(text=f"{pair} : {price if pair not in ["BTCUSDT","ETHUSDT",'SOLUSDT'] else round(Decimal(price))} H: {high_price if pair not in ["BTCUSDT","ETHUSDT",'SOLUSDT'] else round(Decimal(high_price))} L: {low_price if pair not in ["BTCUSDT","ETHUSDT",'SOLUSDT'] else round(Decimal(low_price))}  ")
        else:
            price_labels[pair].config(text=f"{pair}: Data fetch failed")

    # Schedule the function to run again after 500 ms (0.5 seconds)
   app.after(900, update_prices)
# Function to create the system tray icon
def create_tray_icon():
    # Create an image for the tray icon
    icon_image = Image.new("RGB", (64, 64), "green")
    draw = ImageDraw.Draw(icon_image)
    draw.ellipse((16, 16, 48, 48), fill="blue")  # Simple white circle as icon

    # Define the system tray menu
    menu = Menu(
        MenuItem("Show", lambda: show_window()),
        MenuItem("Hide", lambda: hide_window()),
        MenuItem("Exit", lambda: exit_app())
    )

    # Create the system tray icon with a menu
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
    floating_window.destroy()  # Destroy the tkinter window
    app.quit()                 # Quit the tkinter app

def hideWindow(event):
    floating_window.withdraw()

# Function to start dragging
def on_drag_start(event):
    # Record the current mouse position
    drag_data["x"] = event.x
    drag_data["y"] = event.y

# Function to handle dragging the window (optimized for smoother performance)
def on_drag_motion(event):
    # Calculate the movement of the mouse
    dx = event.x - drag_data["x"]
    dy = event.y - drag_data["y"]

    # Apply the change to the window's position
    new_x = floating_window.winfo_x() + dx
    new_y = floating_window.winfo_y() + dy

    # Apply the movement only when there's a significant difference to avoid redundant updates
    if abs(dx) > 1 or abs(dy) > 1:
        floating_window.geometry(f"+{new_x}+{new_y}")

    # Update the starting mouse position for the next move
    drag_data["x"] = event.x
    drag_data["y"] = event.y

# Bind mouse events to make the window draggable
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
