########################################################################################################################################################
# KLC to INI
# PKL Application
# Alex Heinrich
########################################################################################################################################################

########################################################################################################################################################
# Imports
from PIL import Image, ImageDraw, ImageFont

########################################################################################################################################################
# Parameters and data containers
keyboard_layout = [ # default
    ["~", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "←"],
    ["↹", "q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "[", "]", "\\"],
    ["⇪", "a", "s", "d", "f", "g", "h", "j", "k", "l", ";", "'", "↵"],
    ["⇧", "z", "x", "c", "v", "b", "n", "m", ",", ".", "/", "⇧"],
    ["ctrl", "fn", "⊞", "alt", " ", "alt", "⊟", "ctrl"]]

special_key_names = [
    [], ["⇧"], ["ctrl"],
    ["ctrl", "⇧"],
    ["ctrl", "alt"], 
    ["ctrl", "alt", "⇧"]]

special_keys_width_by_index = {
    (0, 13): 2,                                 # backspace
    (1, 0):  1.5,   (1, 13): 1.5,               # tab, \
    (2, 0):  1.75,  (2, 12): 2.42,              # caps lock, enter
    (3, 0):  2.25,  (3, 11): 3.1,               # shift, shift
    (4, 0):  1.08,  (4, 4):  6.25, (4, 7): 3.7} # ctrl, space, ctrl

gray_keys = [
    (1, 12), (1, 11),                           # [ ]
    (2, 11), (2, 10),                           # ; '
    (3, 10), (3, 9), (3, 8)]                    # , . /

key_colors = {
    "Regular":   "#D3D3D3",                      # letters
    "Highlight": "#0000FF",                      # highlight letters
    "Special":   "#A9A9A9",                      # commands and numbers
    "Selected":  "#808080"}                      # layout switch

font              = ImageFont.truetype(r"cambria.ttc", 23, index=1)
default_key_width = 30
key_width         = 32
key_height        = 32
start_x           = 10
start_y           = 10
row_spacing       = 5
col_spacing       = 5

########################################################################################################################################################
# Definitions
def load_klc(klc_name):
    """ Opens a KLC file as a list of lists with entries separated by tabs.
    
        output summary: [[SC, VK, blank, CapStat, 0Norm, 1Sh, 2Ctrl, 6AGr, 7AGrSh, Caps , ...], ...]
        description:    [[UNICODE, other, other, other, NORMAL, SHIFT, CTRL, CTRL+SHIFT, CTRL+ALT, CTRL+ALT+SHIFT, ...], ...]
        example:        [['02', '1', '', '5', '222b', '222e', '-1', '2124', '-1', '2115', '', ...], ...]
    """

    with open(klc_name, 'r', encoding='utf-16') as klc:
        klc_list = list((line.strip().split('\t') for line in klc))
    return klc_list

def klc_to_ini(klc_list):
    """ Formats extracted data to construct INI file.
    
        output summary: ["SC0## = VK	CapStat	0Norm	1Sh	2Ctrl	6AGr	7AGrSh	Caps	CapsSh", ...]
        example:        ["SC002 = 1	5	∫	∮	--	ℤ	--	ℕ", ...]
    """

    # Initialize search through KLC data
    keys, keys_list, trigger = [], [], 0
    for i in range(len(klc_list)):
        
        # Identify first key
        if klc_list[i][0] == "02":
            trigger += 1
        
        # Extract data from line
        if trigger == 1:
        
            # Initialize and set scan code and VK
            key = f"SC0{klc_list[i][0]} = {klc_list[i][1]}\t"
            key_list = [f"SC0{klc_list[i][0]}", klc_list[i][1]]
            for j in range(2, 10):
                if klc_list[i][j] != '':
                
                    if klc_list[i][j][0:2] == "//":
                        break
                    
                    # Set CapStat
                    if len(klc_list[i][j]) == 1:
                        key += f"{klc_list[i][j]}\t"
                        key_list.append(klc_list[i][j])
                        
                    # Set blank keys to --
                    elif klc_list[i][j] == '-1':
                        key += f"--\t"
                        key_list.append("--")
                    else:
                    
                        # Fixed unicode value
                        if klc_list[i][j][-1] == "@":
                            key += f"{chr(int(klc_list[i][j].replace('@', ''), 16))}\t"
                            key_list.append(chr(int(klc_list[i][j].replace('@', ''), 16)))
                        else:
                        
                            # Set key
                            key += f"{chr(int(klc_list[i][j], 16))}\t"
                            key_list.append(chr(int(klc_list[i][j], 16)))

            # Identify last key
            if klc_list[i][0] == "53": 
                trigger -= 1
            
            # Add line to list for export
            keys.append(key)
            keys_list.append(key_list)
    return keys, keys_list

def save_ini(keys):
    with open(f"layout.ini", 'w', encoding='utf-8') as output:
        print("[layout]\n;scan = VK	CapStat	0Norm	1Sh	2Ctrl	6AGr	7AGrSh	Caps	CapsSh", file=output)
        for i in range(len(keys)): print(keys[i], file=output)

def make_layouts(keys_list):
    """ Formats extracted KLC data into the form given by keyboard_layout. """
    
    # Initialize keyboard variants
    trigger = 0
    layout_list_cache = [
        [[],[],[],[],[]],
        [[],[],[],[],[]],
        [[],[],[],[],[]],
        [[],[],[],[],[]],
        [[],[],[],[],[]],
        [[],[],[],[],[]]]
    
    # Set placeholder for problematic key
    SC02b = []
    
    # Populate layout
    for i in range(len(keys_list)):
        if keys_list[i][0] == "SC002":   trigger = 0 # first row  (1, 2, 3, ...)
        elif keys_list[i][0] == "SC010": trigger = 1 # second row (q, w, e, ...)
        elif keys_list[i][0] == "SC01e": trigger = 2 # third row  (a, s, d, ...)
        elif keys_list[i][0] == "SC02c": trigger = 3 # fourth row (z, x, c, ...)
        elif keys_list[i][0] == "SC039": break
        
        # Deal with problematic keys
        if keys_list[i][0] == "SC02b":
            SC02b = keys_list[i]
            continue
        elif keys_list[i][0] == "SC029":
            continue
        
        # Append data
        for j in range(0, len(keys_list[0])-3):
            if keys_list[i][j+3] == "--": layout_list_cache[j][trigger].append("")
            else:                         layout_list_cache[j][trigger].append(keys_list[i][j+3])
    
    # Deal with problematic keys
    if SC02b:
        for i in range(0, len(keys_list[0])-3):
            if SC02b[i+3] == "--": layout_list_cache[i][1].append("")
            else:                  layout_list_cache[i][1].append(SC02b[i+3])

    # Fill in gaps an add special keys (ex. space, enter, ctrl, ...)
    for i in range(len(layout_list_cache)):
        
        if abs(len(layout_list_cache[i][0]) - 14):
            layout_list_cache[i][0].insert(0, keyboard_layout[0][0])
            for j in range(abs(len(layout_list_cache[i][0]) - 13)): layout_list_cache[i][0].append('')
            layout_list_cache[i][0].append(keyboard_layout[0][-1])
        
        if abs(len(layout_list_cache[i][1]) - 14):
            layout_list_cache[i][1].insert(0, keyboard_layout[1][0])
            for j in range(abs(len(layout_list_cache[i][1]) - 14)): layout_list_cache[i][1].append('')
        
        if abs(len(layout_list_cache[i][2]) - 13):
            layout_list_cache[i][2].insert(0, keyboard_layout[2][0])
            for j in range(abs(len(layout_list_cache[i][2]) - 12)): layout_list_cache[i][2].append('')
            layout_list_cache[i][2].append(keyboard_layout[2][-1])            
        
        if abs(len(layout_list_cache[i][3]) - 12):
            layout_list_cache[i][3].insert(0, keyboard_layout[3][0])
            for j in range(abs(len(layout_list_cache[i][3]) - 11)): layout_list_cache[i][3].append('')
            layout_list_cache[i][3].append(keyboard_layout[3][-1])
            
        layout_list_cache[i][-1] = keyboard_layout[4]
    
    # Export data
    return layout_list_cache

def make_image(layout, index):
    global font, start_x, start_y
    
    # Initialize parameters
    font              = ImageFont.truetype(r"cambria.ttc", 23, index=1)
    default_key_width = 30
    key_width         = 32
    key_height        = 32
    start_x           = 10
    start_y           = 10
    row_spacing       = 5
    col_spacing       = 5
    
    # Initialize image
    keyboard_image = Image.new('RGB', (535, 200), color='#274829')
    draw = ImageDraw.Draw(keyboard_image)

    # Draw each key with its corresponding character
    for row_index, row in enumerate(layout):
        for key_index, key in enumerate(row):
            key_width = special_keys_width_by_index.get((row_index, key_index), 1) * default_key_width
            
            # Determine key color by Regular or Special
            key_color = key_colors["Special"] if (row_index, key_index) in special_keys_width_by_index else key_colors["Regular"]
            
            if (row_index, key_index) in special_keys_width_by_index: key_color = key_colors["Special"]
            elif (row_index == 0) or (row_index == 4):                key_color = key_colors["Special"]
            elif (row_index, key_index) in gray_keys:                 key_color = key_colors["Special"]
            else:                                                     key_color = key_colors["Regular"]
            if key in special_key_names[index]:                       key_color = key_colors["Selected"]
            
            if (row_index, key_index) in [(2, 4), (2, 7)]:            font_color = key_colors["Highlight"]
            else:                                                     font_color = "black"
            
            # Fill rectangle with key color
            draw.rectangle([start_x, start_y, start_x + key_width, start_y + key_height], fill=key_color, outline="black")
            
            if row_index == 4:  font = ImageFont.truetype(r"cambria.ttc", 15, index=1)
            
            # Calculate text size and position to center it
            text_bbox = draw.textbbox((0, 0), key, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = start_x + (key_width - text_width) / 2
            text_y = start_y + (key_height - text_height) / 2
            
            draw.text((text_x, text_y), key, font=font, fill=font_color)
            start_x += key_width + col_spacing
            
        start_x = 10
        start_y += key_height + row_spacing

    # Save the image
    keyboard_image.save(f"state{index}.png")

def main():
    
    # Load KLC file
    klc_name = input("Enter {filename}: ") + ".klc"
    klc_list = load_klc(klc_name)
    
    # Extract data
    keys, keys_list = klc_to_ini(klc_list)

    # Create ini file
    save_ini(keys)
    
    # Create images
    layout_list = make_layouts(keys_list)[:2] # 0Norm, 1Sh
    for i in range(len(layout_list)):
        if len(layout_list[i]) > 2: make_image(layout_list[i], i)

########################################################################################################################################################
# Global scripts
main()

########################################################################################################################################################