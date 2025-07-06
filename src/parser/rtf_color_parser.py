 # **********************************************************
 #
 # @Author: Andreas Paepcke
 # @Date:   2025-07-04 19:24:58
 # @File:   /Users/paepcke/VSCodeWorkspaces/rtf-text-color-parser/src/parser/rtf_color_parser.py
 # @Last Modified by:   Andreas Paepcke
 # @Last Modified time: 2025-07-05 18:59:22
 #
 # **********************************************************

import argparse
import os
import sys
from striprtf.striprtf import rtf_to_text
import re

# Example of RTF material being processed here:
#        ...
#      {\colortbl;\red255\green0\blue0;\red11\green93\blue162;
#        \cf1 I'm looking for my glasses.
#        \cf2 They are on your head
#        ...
  
class RTFParser:
    '''
    Runs through an RTF file of colored text, and generates
    a new text file, like a movie script. For example, if
    red text is associated with actor Fred, and blue is associated
    with Susie, then the RTF text example above the class def
    Would generate:
    
    Fred: I'm looking for my glasses.
    Susie: They are on your head

    This facility finds and parses the color table inside the file.
    It accepts a tag map from the caller in the constructor:

       {'RGB(255,0,0)'   : 'Fred',
        'RGB(11,93,162)' : 'Susie
       }

    If no tag map is provided, the facility is still useful for separating
    differently colored text each into its own paragraph.
    '''

    #------------------------------------
    # Constructor
    #-------------------    

    def __init__(self, fname, tagmap={}, is_unittest=False):
        '''
        Given an RTF file, and a mapping from RGB colors to 
        script names, generate a script file.

        :param fname: full path to RTF file
        :type fname: string
        :param colortags: map from RGB specs to text tags, defaults to {}
        :type colortags: Dict[str, str], optional
        '''

        # Allow unittests to call service methods
        # directly
        if is_unittest:
            return
            
        # Get a big string that is the file:
        try:
            with open(fname, 'r') as fd:
                rtf_content = fd.read()
        except Exception as e:
            print(f"File {fname} cannot be found or read: {e}")
            return

        # The following will print an error to console,
        # and leave the program
        try:
            res = self.check_tagmap(tagmap)
        except ValueError as e:
            print(f"Bad tagmap dict: {e.message}")
            return
        # Extract the RTF color table from the RTF string:
        #   {1 : 'RGB(24,20,105')'
        #    2 : 'RGB(1,204,105')
        #         ...
        #   }
        rtf_color_dict = self.make_color_tbl(rtf_content)

        # Get set of all RTF control sequences used in the text,
        # so we can remove all but the color specs:
        control_pattern = r'\\[a-zA-Z]+\d*|\\\S'
        rtf_controls = set(re.findall(control_pattern, rtf_content))
        # We have to retain the \cf color controls:
        rtf_controls.remove('\\cf')

        clean_rtf = self.remove_rtf_controls(rtf_content, rtf_controls)

        self.output_txt_script(clean_rtf, rtf_color_dict, tagmap)

    #------------------------------------
    # output_txt_script
    #-------------------

    def output_txt_script(self, rtf_content, rtf_color_dict, tagmap):
        '''
        Output line JSON to stdout. Like:
           {"Fred"  : "I said this"}
           {"Susie} : "I said that"}

        :param rtf_content: the content of the RTF file with colored roles
        :type rtf_content: str
        :param rtf_color_dict: dict mapping RTF color tags to RGB colors,
            such as {"cf2" : "RGB(23, 20, 103)", ...}
        :type rtf_color_dict: Dict[str,str]
        :param tagmap: map from color to role tag, like:
            {"RGB(23,20,103)" : "Fred", ...}
        :type tagmap: Dict[str,str]
        '''
        json_objs = []
        cur_jsonl = {}
        cur_idx = 0
        plain_txt_start = None

        while (span_and_color_dict := self._next_rtf_color_tag_idx(rtf_content[cur_idx:])):
            tag_len   = span_and_color_dict['tag_len']
            color_num = span_and_color_dict['color_num']
            txt_tag = tagmap[color_num]
            if plain_txt_start is not None:
                cur_jsonl[txt_tag] = rtf_color_dict[plain_txt_start:cur_idx]
                json_objs.append(cur_jsonl)
                cur_jsonl = {}
            else:
                # First segment of plain text:
                cur_jsonl[txt_tag] = ''
                plain_txt_start = cur_idx + tag_len
            cur_idx += tag_len

        return json_objs

    #------------------------------------
    # remove_rtf_controls
    #-------------------

    def remove_rtf_controls(self, rtf_txt, controls_set):
        '''
        Given an RTF string, remove all the control sequences
        and return a new string with the sequences removed.

        Example controls_set: set(['\\i', '\\cb'])

        :param rtf_txt: the text to be cleaned
        :type rtf_txt: str
        :param controls_set: set of RTF control sequences to remove
        :type controls_set: set[str]
        :return: new string with control sequences removed
        :rtype: str
        '''
        # Escape special regex characters and join with OR
        escaped = [re.escape(s) for s in controls_set]
        pattern = '|'.join(escaped)
        return re.sub(pattern, '', rtf_txt)        

    #------------------------------------
    # _next_rtf_color_tag_idx
    #-------------------    

    def _next_rtf_color_tag_idx(self, rtf_str):
        match = re.search(r'\\\\cf(\d)', rtf_str)
        if not match:
            return None
        # Got a match of somthind like '\cf2', with
        # group 1 being '2':
        try:
            color_num = int(match.group[1])
            return {"tag_len" : len(match[0]),
                    "color_num" : color_num
                    }
        except IndexError:
            # Match did not have a number after the \cf
            raise ValueError(f"Found '{match[0]}' in RTF, but this does not end with a number")
        except ValueError:
            # Group 1 existed, but is not an int:
            raise ValueError(f"Found '{match[0]}' in RTF, which does not end with a proper integer")
        
    #------------------------------------
    # _plain_text_start
    #-------------------

    def _plain_text_start(self, rtf_str):
        rtf_controls_pat = r'\\\\[^\s]*'
        idx = 0
        while (match := re.search(rtf_controls_pat, rtf_str[idx:])):
            idx += len(match[0])
        return idx

    #------------------------------------
    # check_tagmap
    #-------------------

    def check_tagmap(self, tagmap):
        '''
        Ensure that tagmap properly maps string tag names
        to legal RGB values. Return True if OK, else False.
        Print error message if fault is found

        :param tagmap: the map to be checked
        :type tagmap: Dict[str, str]
        :return: a True or False, depending on the test outcome
        :rtype: boolean
        '''
        if len(tagmap) == 0:
             return True
        # All keys must be strings:
        for key, rgb in tagmap.items():
            if type(key) != str:
                print(f"Tabmap keys must be strings, not {key}")
                return False
            # Values must be of the form
            # 'RGB(<int>,<int>,<int>,[float])' with <int> between 0 and 255,
            #                                  and the float being 0 to 1, or
            # '#xxyyzz' with x, y, and z being Hex chars, 00 to FF
            rgb = rgb.upper()
            if rgb.startswith('RGB'):
                return self.validate_rgb_string(rgb)
            elif rgb.startswith('#'):
                return self.validate_rgb_hex_string(rgb)

    #------------------------------------
    # validate_rgb_string
    #-------------------

    def validate_rgb_string(rgb_string):
        '''
        Checks if a given string conforms to the RGB(int,int,int) format
        with integers between 0 and 255, tolerant of spaces after commas.

        Returns either True or throws a ValueError

        :param rgb_string: string to check
        :type rgb_string: str
        :throws ValueError if error found
        '''
        # Regex to match RGB(int,int,int) with optional spaces after commas.
        # It captures the three integer values.
        # \s* allows for zero or more spaces.
        # (\d+) captures one or more digits.
        pattern = r"^RGB\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$"
        match = re.match(pattern, rgb_string)

        if not match:
            msg = (f"RGB specification must be of the form RGB(<int>,<int>,<int>), "
                   f"with ints between 0 and 255; not {rgb_string}")
            raise ValueError(msg)

        # Extract the captured integer strings
        r_str, g_str, b_str = match.groups()

        try:
            # Convert to integers
            r = int(r_str)
            g = int(g_str)
            b = int(b_str)

            # Check if each integer is within the valid range [0, 255]
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                return True
            else:
                msg = f"Valid RGB ints are between 0 and 255; was given {r}, {g}, and {b}"
                raise ValueError(msg)

        except ValueError as e:
            # This case should ideally be caught by the regex if it only matches digits,
            # but it's good practice for robustness if the regex were more lenient.
            raise e
        
        return True

    #------------------------------------
    # validate_rgb_hex_string
    #-------------------

    def validate_rgb_hex_string(hex_string):
        '''
        Checks if a given string conforms to the #RRGGBB hexadecimal format.
        If failure, raises ValueError

        :param hex_string: The string to validate.
        :type hex_string: str
        '''
        # Regex to match a string starting with '#' followed by exactly 6 hexadecimal characters.
        # [0-9a-fA-F] matches any digit (0-9) or any letter from a to f (case-insensitive).
        # {6} ensures there are exactly six such characters.
        pattern = r"^#[0-9a-fA-F]{6}$"
        match = re.match(pattern, hex_string)
        if not match:
            msg = f"String '{hex_string}' is not of form '#rrggbb' of hex numbers"
            raise ValueError(msg)
        return True

    #------------------------------------
    # make_color_tbl
    #-------------------

    # Example of a color table in RTF files 
    #   (line breaks for clearity only)
    # {\colortbl;\red255\green255\blue255;
    #  \red74\green21\\blue148;
    #  \red255\green255\\blue255;
    #  \red11\green93\\blue162;}

    # Example for color reference inside RTF text:
    #
    #  \f0\fs32 \cf2 \cb3 \up0 \nosupersub \ulnone I wonder what risks ...
     
    def make_color_tbl(self, rtf_content):
        '''
        Given RTF content, find the color table entry, and 
        return a dict {colorTagName : RGB-color}. Example color tbl:

            see above this method definition:
        
        The line breaks are for clarity only; the table is one long
        string. The table results in tags cf1 through cf4. Example 
        string in a doc body:

            see above color reference example:

        That text would be purple: RGB(74, 21, 148)

        Return a dict mapping RTF tags to RGB(<int>,<int>,<int>) strings:
           {1 : 'RGB(255,255,255)',
            2 : 'RGB(71,21,148)',
            3 : 'RGB(255,255,255)',
            4 : 'RGB(11,93,162)'
           }

        :param rtf_content: the RTF file content; at least enough to 
        :type rtf_content: string
        :return: dict mapping RTF color numbers to RGB colors
        :rtype: Dict[int, str]
        '''
        
        # Extract color table
        color_table_match = re.search(r'\\colortbl;([^}]+)', rtf_content)
        if not color_table_match:
            raise ValueError(f"File does not contain an RTF color table")
        
        color_table = color_table_match.group(1)
        colors = {}
        
        # Parse individual colors
        color_entries = re.findall(r'\\red(\d+)\\green(\d+)\\blue(\d+);', color_table)
        for i, (r, g, b) in enumerate(color_entries):
            # Creat color table entries like:
            #    {3 : (10,40,200)}
            colors[i] = (int(r), int(g), int(b))
        
        return colors        
        
# --------------------- Main ------------------
if __name__ == "__main__":
    desc = ("Parses an RTF file, and outputs a movie-script-like text\n"
            "based on colors provided on the CLI. Example\n"
            "RGB(20,154,200) Fred rgb(30,53,24) Susie #B3a8C4 Bob path/to/rtfFile.rtf")

    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]),
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     description=desc
                                     )
    
    # Use nargs='+' to capture all positional arguments into a list.
    # We will then manually separate the filename from the pairs:
    parser.add_argument(
        'arguments',
        nargs='+', # Requires at least one argument (the filename)
        help=(
            "A series of color-name string pairs followed by the final filename.\n"
            "Example: RGB(20,154,200) Fred #B3a8C4 Susie  path/to/rtfFile.rtf"
        )
    )

    args = parser.parse_args()

    # All positional arguments are collected in args.arguments
    all_input_args = args.arguments

    # Check if there are enough arguments to form at least a filename
    if not all_input_args:
        print("Error: No arguments provided. A filename is required.")
        parser.print_help()
        sys.exit(1)
        
    # The last argument is always the filename
    filename = all_input_args[-1]
    # The arguments before the last one are the potential pairs
    pair_components = all_input_args[:-1]

    # Validate the filename (optional, but good practice)
    if not os.path.exists(filename):
        print(f"File '{filename}' does not exist")
        sys.exit(1)

    # Check if the remaining arguments (pair_components) have 
    # an even number of elements:
    if len(pair_components) % 2 != 0:
        print("Error: The number of color-name arguments must be even to form complete pairs.")
        print(f"Received {len(pair_components)} pair components: {pair_components}")
        parser.print_help()
        sys.exit(1)

    # Process the pairs
    color_name_pairs = {}
    for i in range(0, len(pair_components), 2):
        color = pair_components[i]
        name = pair_components[i+1]
        color_name_pairs[color] = name

    RTFParser(filename, color_name_pairs)
