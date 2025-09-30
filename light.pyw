##########################################################################################################
# Portable Keyboard Layout (light)
#
# pyinstaller --onefile --windowed --add-data "layouts;layouts" light.py
##########################################################################################################

##########################################################################################################
# Imports
import keyboard                                # Key replacement
import os                                      # Image management
import sys                                     # Executable

##########################################################################################################
# Parameters
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

##########################################################################################################
# Mapping
def toggle_layout(event):
    """ Toggles application and switches between layouts. """
    global replace, current_layout
    
    # Toggle replacement/layout
    if (event.event_type == 'down') and (event.name == '`'):
        
        # Switch layouts
        if keyboard.is_pressed('ctrl'):
            if replace: current_layout = (current_layout + 1) % len(layouts)
        
        # Close application
        elif keyboard.is_pressed('esc'): keyboard.unhook_all()
        
        # Toggle replacement
        else: replace = not replace
            
    # Close application
    elif (event.event_type == 'down') and (event.name == 'esc'):
        if keyboard.is_pressed('`'): keyboard.unhook_all()

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

    if (new_state != layout_state) and (new_state is not None): layout_state = new_state

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
    
    # Initialize mapping
    keyboard.hook(key_replacement, suppress=True)
    keyboard.hook_key("`", toggle_layout, suppress=True)
    keyboard.hook_key("esc", toggle_layout, suppress=True)

    # Run loop
    keyboard.wait("esc")

if __name__ == "__main__":
    main()

##########################################################################################################