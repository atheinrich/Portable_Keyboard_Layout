##########################################################################################################
# Portable Keyboard Layout (redux)
#
# pyinstaller --onefile --windowed --add-data "layouts;layouts" main.py
##########################################################################################################

##########################################################################################################
# User settings
taskbar_icon = True

##########################################################################################################
# Imports
import keyboard                                # Key replacement
import tkinter as tk                           # Image management
from PIL import Image, ImageTk                 # Image management; pillow
import os                                      # Image management
import ctypes                                  # Image management
import sys                                     # Executable
import traceback                               # Debugging
import threading                               # Taskbar icon
import pystray                                 # Taskbar icon

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
replace        = False                         # Turns app on/off
current_layout = 0                             # Notes current layout; alphanumeric order of Layout folders
layout_state   = 0                             # Notes current variant; order of [0Norm, 1Sh]

##########################################################################################################
# Data
def _find_paths(return_all=False):
    """ Returns the directory path for each layout folder in /root/Layouts. """
    
    def resource_path(relative_path):
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, relative_path)
        base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)
    layouts_path = resource_path("layouts")
    utility_path = resource_path("utility")

    layout_paths = []
    for directory in os.listdir(layouts_path):
        path = os.path.join(layouts_path, directory)
        if os.path.isdir(path): layout_paths.append(path)
    
    if return_all: return root, utility_path, layouts_path, layout_paths
    else:          return layout_paths

class Layout:
    """ Represents one layout folder. Processes replacement dictionaries and images. """

    def __init__(self, dir_path):
        
        # Directories
        self.path     = dir_path
        self.name     = os.path.basename(self.path)
        self.ini_path = os.path.join(self.path, "layout.ini")
        
        # Variants
        self.variant_map = {
            0: "0Norm",
            1: "1Sh"}
        self.vars = list(self.variant_map.values())

        # Key bindings
        self.mapping = {
            self.vars[0]: {},
            self.vars[1]: {}}
        self._import_mapping()

        # Images
        self.images = {
            self.vars[0]: None,
            self.vars[1]: None}
        self._import_images()

    def _import_mapping(self):
        """ Parse layout.ini and populate mapping for 0Norm and 1Sh. """
        
        # Handle non-alphabetic characters
        VK_dict = {
            "1":          ["1",  "!"],
            "2":          ["2",  "@"],
            "3":          ["3",  "#"],
            "4":          ["4",  "$"],
            "5":          ["5",  "%"],
            "6":          ["6",  "^"],
            "7":          ["7",  "&"],
            "8":          ["8",  "*"],
            "9":          ["9",  "("],
            "0":          ["0",  ")"],            
            "OEM_MINUS":  ["-",  "_"],
            "OEM_PLUS":   ["=",  "+"],

            "OEM_4":      ["[",  "{"],
            "OEM_6":      ["]",  "}"],
            "OEM_5":      ["\\", "|"],

            "OEM_1":      [";",  ":"],
            "OEM_7":      ["'",  '"'],
            
            "OEM_COMMA":  [",",  "<"],
            "OEM_PERIOD": [".",  ">"],
            "OEM_2":      ["/",  "?"],

            "SPACE":      ["space",   "space"],
            "DECIMAL":    ["decimal", "decimal"],
            "OEM_3":      ["",   ""]}
        
        # Verify ini file exists
        if not os.path.exists(self.ini_path):
            print("(!) Run INI_image_creator in the layout folder.")
            return
        
        # Extract all lines from the ini file
        with open(self.ini_path, "r", encoding="utf-8") as file:
            
            # Process each row of data
            for line in file.readlines():
                
                # Look for data
                ## Skip first and second rows
                if (not line) or line.startswith("[") or line.startswith(";"): continue

                ## Select a row of data
                _, right = line.split("=", 1)
                parts = [part for part in right.split("\t") if part != ""]
                parts = {
                    "VK":    parts[0].strip(),
                    "0Norm": parts[2],
                    "1Sh":   parts[3]}
                
                # Partition columns as variants
                for key, val in parts.items():
                    if key in self.mapping.keys():
                        
                        # Handle non-alphabetic characters
                        if parts["VK"] in VK_dict:
                            if key == "0Norm": VK = VK_dict[parts["VK"]][0]
                            else:              VK = VK_dict[parts["VK"]][1]
                        
                        # Handle alphabetic characters
                        else: VK = parts["VK"].lower()
                        
                        # Handle blank characters
                        if val == "--": val = parts["VK"]
                        
                        # Add to map
                        self.mapping[key][VK] = val

    def _import_images(self):
        """ Find an image for each variant. """
        
        for idx, name in self.variant_map.items():
            img_path = os.path.join(self.path, f"state{idx}.png")
            if os.path.exists(img_path):
                self.images[name] = Image.open(img_path)

##########################################################################################################
# Tkinter
def move_window():
    """ Moves the window if the cursor overlaps with it. """
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
        place_window()
    
    # Check again in 100 ms
    root.after(100, move_window)

def place_window():
    """ Sets the location of the window. """
    global screen_width, screen_height
    
    screen_width  = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - img_width) // 2
    y = 0
    if not position_top: y = screen_height - img_height - lower_margin
    root.geometry(f"{img_width}x{img_height}+{x}+{y}")

def show_window():
    """ Loads image and displays it in a window. """
    
    # Import layout image
    if layout_state: state = layouts[0].vars[1]
    else:            state = layouts[0].vars[0]
    img   = layouts[current_layout].images[state]
    photo = ImageTk.PhotoImage(img)
    
    # Apply image to window
    label.config(image=photo)
    label.image = photo
    
    # Show window
    root.deiconify()
    raise_window()

def raise_window():
    """ Places the window above all else. """
    
    root.lift()
    root.attributes("-topmost", True)
    root.after(1000, raise_window)

##########################################################################################################
# Icon
def create_icon(file="off"):
    _, utility_path, _, _ = _find_paths(return_all=True)
    path = os.path.join(utility_path, file + ".ico")
    img = Image.open(path)
    return img

def on_quit(item):
    icon.stop()
    root.destroy()

def flip_toggle():
    if replace: icon.icon = create_icon("on")
    else:       icon.icon = create_icon("off")

def run_tray():
    global icon

    icon = pystray.Icon(
        "test",
        create_icon(),
        "My App",
        menu=pystray.Menu(
            pystray.MenuItem("Flip Toggle", flip_toggle),
            pystray.MenuItem("Quit",        on_quit)))
    
    icon.run()

##########################################################################################################
# Mapping
def toggle_layout(event):
    """ Toggles application and switches between layouts. """
    global replace, current_layout
    
    # Toggle replacement/layout
    if (event.event_type == 'down') and (event.name == '`'):
        
        # Switch layouts
        if keyboard.is_pressed('ctrl'):
            if replace:
                current_layout = (current_layout + 1) % len(layouts)
                show_window()
        
        # Close application
        elif keyboard.is_pressed('esc'):
            keyboard.unhook_all()
            root.destroy()
            root.after(0, root.destroy)
        
        # Toggle replacement
        else:
            replace = not replace
            if taskbar_icon: flip_toggle()
            if replace:      show_window()
            else:            root.withdraw()
    
    # Close application
    elif (event.event_type == 'down') and (event.name == 'esc'):
        if keyboard.is_pressed('`'):
            keyboard.unhook_all()
            root.destroy()
            root.after(0, root.destroy)

def toggle_state(event):
    """ Switches between variants for the current layout. """
    global layout_state

    key = event.name.lower()
    new_state = None

    if (key == 'shift')   and (layout_state == 0): new_state = 1 # Queue shift
    elif (key != 'shift') and (layout_state == 1): new_state = 2 # Note that shift has been used
    elif (key == 'shift') and (layout_state == 2): new_state = 3
    elif (key == 'shift') and (layout_state == 3): new_state = 0 # Check when shift is lifted
    elif (key == 'shift') and (event.event_type == "up"): new_state = 0 # Handle independent presses

    if (new_state != layout_state) and (new_state is not None):
        layout_state = new_state
        show_window()

def key_replacement(event):
    """ Handles replacement. """
    
    if replace:

        # Check if shift is held
        toggle_state(event)
        
        # Check for input
        key = event.name.lower()
        if event.event_type == 'down':
            
            # Set layout
            if layout_state: mapping = layouts[current_layout].mapping["1Sh"]
            else:            mapping = layouts[current_layout].mapping["0Norm"]
            
            # Replace and update cache
            if key in mapping:
                keyboard.write(mapping[key], delay=0)
                return False
    
    return True

##########################################################################################################
# Main
def main():
    global root, layouts, label
    
    # Load data
    layouts = [Layout(path) for path in _find_paths()]
    
    # Initialize tkinter
    root = tk.Tk()               # Create window
    label = tk.Label(root)       # Initialize photo container
    label.pack()

    root.overrideredirect(True)  # Hide window minimize bar
    root.withdraw()              # Hide window at startup

    place_window()               # Set window size and location
    root.after(100, move_window) # Move window when cursor hovers over it
    
    # Initialize mapping
    keyboard.hook(key_replacement, suppress=True)
    keyboard.hook_key("`", toggle_layout, suppress=True)
    keyboard.hook_key("esc", toggle_layout, suppress=True)

    # Run loop
    if taskbar_icon: threading.Thread(target=run_tray, daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        input("Press Enter to close...")

##########################################################################################################