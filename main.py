##########################################################################################################
# Portable Keyboard Layout (redux)
#
# pyinstaller --onefile --windowed --add-data "layouts;layouts" main.py
##########################################################################################################

##########################################################################################################
# Imports
import keyboard                 # Key replacement
import tkinter as tk            # Image management
from PIL import Image, ImageTk  # Image management
import os                       # Image management
import ctypes                   # Image management
import importlib.util           # Image management
import sys                      # Executable

##########################################################################################################
# Parameters
## Tkinter
ctypes.windll.shcore.SetProcessDpiAwareness(1) # Sets image scaling
img_width     = 535                            # Set by image size
img_height    = 200                            # Set by image size
lower_margin  = 100                            # Set by Windows chin
screen_width  = 0                              # Set later
screen_height = 0                              # Set later
position_top  = False                          # Location of window

## Mapping
current_layout = 0                             # Notes current layout
replace        = False                         # Turns app on/off

##########################################################################################################
# Data
## Data containers
layouts       = [] # Holds layout dictionaries
layout_images = [] # Holds image paths

## Find directories
def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
layouts_path = resource_path("layouts")

directories = []
for directory in os.listdir(layouts_path):
    path = os.path.join(layouts_path, directory)
    if os.path.isdir(path): directories.append(path)

## Fill data containers
for d in sorted(directories):
    
    # Tkinter
    img_path = os.path.join(d, "layout.png")
    layout_images.append(img_path)
    
    # Mapping
    data_path = os.path.join(d, "data.py")
    spec = importlib.util.spec_from_file_location("data", data_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    layouts.append(module.mapping)

##########################################################################################################
# Tkinter
## Functions
def move_window():
    global position_top
    
    # Find cursor location
    cursor_x = root.winfo_pointerx()
    cursor_y = root.winfo_pointery()
    
    # Find window boundary
    win_left   = (screen_width - img_width) // 2
    win_right  = win_left + img_width
    win_bottom = 0
    if not position_top: win_bottom += screen_height - img_height - lower_margin
    win_top    = win_bottom + img_height
    
    # Check if cursor is in window
    if (win_left <= cursor_x <= win_right) and (win_bottom <= cursor_y <= win_top):
        position_top = not position_top
        place_window(root)
    
    # Check again in 100 ms
    root.after(100, move_window)

def place_window(window):
    global screen_width, screen_height
    
    screen_width  = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - img_width) // 2
    y = 0
    if not position_top: y = screen_height - img_height - lower_margin
    window.geometry(f"{img_width}x{img_height}+{x}+{y}")

def show_window(index):
    
    # Import layout image
    img   = Image.open(layout_images[index])
    photo = ImageTk.PhotoImage(img)
    
    # Apply image to window
    label.config(image=photo)
    label.image = photo
    
    # Show window
    root.deiconify()
    raise_window()

def raise_window():
    root.lift()
    root.attributes("-topmost", True)
    root.after(1000, raise_window)

## Initialization
root = tk.Tk()               # Create window
label = tk.Label(root)       # Initialize photo container
label.pack()

root.overrideredirect(True)  # Hide window minimize bar
root.withdraw()              # Hide window at startup

place_window(root)           # Set window size and location
root.after(100, move_window) # Move window when cursor hovers over it

##########################################################################################################
# Mapping
## Functions
def toggle_or_switch(event):
    global replace, current_layout
    
    # Toggle replacement/layout
    if (event.event_type == 'down') and (event.name == '`'):
        
        # Switch layouts
        if keyboard.is_pressed('ctrl'):
            if replace:
                current_layout = (current_layout + 1) % len(layouts)
                show_window(current_layout)
        
        # Toggle replacement
        else:
            replace = not replace
            if replace: show_window(current_layout)
            else:       root.withdraw()

def key_replacement(event):
    
    # Check for input
    if (event.event_type == 'down') and replace:
        
        # Load layout
        mapping = layouts[current_layout]
        
        # Replace if necessary
        if event.name in mapping:
            keyboard.write(mapping[event.name], delay=0)
            return False
    
    return True

keyboard.hook(key_replacement, suppress=True)
keyboard.hook_key("`", toggle_or_switch, suppress=True)

##########################################################################################################
# Main
root.mainloop()

##########################################################################################################