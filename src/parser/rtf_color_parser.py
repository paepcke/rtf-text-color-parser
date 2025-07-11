#!/usr/bin/env python
 # **********************************************************
 #
 # @Author: Andreas Paepcke
 # @Date:   2025-07-04 19:24:58
 # @File:   /Users/paepcke/VSCodeWorkspaces/rtf-text-color-parser/src/parser/rtf_color_parser.py
 # @Last Modified by:   Andreas Paepcke
 # @Last Modified time: 2025-07-09 14:43:25
 #
 # **********************************************************

import argparse
import os
import sys
from striprtf.striprtf import rtf_to_text
import re

# Example of RTF material being processed here:
#        ...
#      {\\colortbl;\\red255\\green0\\blue0;\\red11\\green93\\blue162;
#        \\cf1 I'm looking for my glasses.
#        \\cf2 They are on your head
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

    This facility first finds and parses the color table inside the file.
    The result is an RTF color table of the form:
       {1: 'RGB(20,156,20)',
        2: 'RGB(1,35,60)',
             ...
       }
    where the keys correspond to the \\cf<int> tags in the RTF file.

    The constructor accepts a tagmap from the caller:

       {'RGB(255,0,0)'   : 'Fred',
        'RGB(11,93,162)' : 'Susie
       }

    The two tables together enable the final 'movie script'.

    If no tagmap is provided, the facility is still useful for separating
    differently colored text each into its own paragraph.
    '''

    # Define unlikely characters for RTF
    UNLIKELY_CHARS = [
        '\x00',  # null character
        '\x01',  # SOH - Start of Heading
        '\x02',  # STX - Start of Text
        '\x03',  # ETX - End of Text
        '\x04',  # EOT - End of Transmission
    ]    

    #------------------------------------
    # Constructor
    #-------------------    

    def __init__(self, fname, tagmap={}, collect_output=False, is_unittest=False):
        '''
        Given an RTF file, and a mapping from RGB colors to 
        script names, generate a script file. Callers have a 
        choice whether the final instance variable json_objs
        will contain a list of jsonl conversation turn objects
        or simply True/False for success. 

        If collect_output is False, the jsonl objects are written 
        to stdout as they are created.

        :param fname: full path to RTF file
        :type fname: string
        :param tagmap: map from RGB specs to 'movie-script' tags, defaults to {}
        :type tagmap: Dict[str, str], optional
        :param collect_output: if True, the instance will 
        :type collect_output: bool
        :param is_unittest: if set to True, the constructor takes no
            action other than creating the RTFParser instance.
        :type is_unittest: bool
        '''

        # Allow unittests to call service methods
        # directly
        if is_unittest:
            return

        # Clients way to check whether conversion was
        # successful
        self.success = False

        # Check the given tagmap.
        try:
            res = self.check_tagmap(tagmap)
        except ValueError as e:
            print(f"Bad tagmap dict: {e.message}")
            return

        # Get a big string that is the file:
        try:
            with open(fname, 'r') as fd:
                rtf_content = fd.read()
        except Exception as e:
            print(f"File {fname} cannot be found or read: {e}")
            return

        # Extract the RTF color table from the RTF string:
        #   {1 : 'RGB(24,20,105')'
        #    2 : 'RGB(1,204,105')
        #         ...
        #   }
        try:
            rtf_color_dict = self.make_color_tbl(rtf_content)
        except Exception as e:
            print(f"Failed: {e}")
            return

        # Pick a character we can use to protect RTF
        # color tags in the text (\cf<int>) from RTF removal.
        self.color_tag_marker_char = None
        for char_candidate in self.UNLIKELY_CHARS:
            if re.search(char_candidate, rtf_content) is None:
                self.color_tag_marker_char = char_candidate
                break
        if self.color_tag_marker_char is None:
            print("Cannot find safe text marker char in RTF content")
            return

        try:
            self.jsonl_objs = self.output_txt_script(
                rtf_content, 
                rtf_color_dict, 
                tagmap,
                collect_output=collect_output)
        except Exception as e:
            print(f"Failed in final phase: {e}")
            return
        

    #------------------------------------
    # output_txt_script
    #-------------------

    def output_txt_script(
            self, 
            rtf_content, 
            rtf_color_dict, 
            tagmap,
            collect_output=False
            ):
        '''
        Given RTF text that has been cleaned of all
        RTF tags, except for RTF color tags (such as '\\cf3'),
        print line JSON to stdout. Like:

           {"Fred"  : "I said this"}
           {"Susie} : "I said that"}

        Line json (jsonl) are correct JSON objects individually, 
        but the entire output taken together is not JSON, because
        there is no array or object wrapper.

        Alternatively, if collect_output is set to True,
        no printing, and an array of jsonl objects is returned.

        Inputs:
           o rtf_color_dict: maps RTF color numbers to 
             RGB colors: 
                {1 : 'RGB(2,40,156)',
                 2 : 'RGB(60,20,25)',
                      ...
                }

           o tagmap maps colors to human readable 
             'movie script' text tags:

                { 
                  'RGB(2,40,156)': 'Fred,
                  'RGB(60,20,25)': 'Susie
                     ...
                }

        :param rtf_content: the content of the RTF file with colored roles
        :type rtf_content: str
        :param rtf_color_dict: dict mapping RTF color tags to RGB colors,
            such as {"cf2" : "RGB(23,20,103)", ...}
        :type rtf_color_dict: Dict[str,str]
        :param tagmap: map from color to role tag, like:
            {"RGB(23,20,103)" : "Fred", ...}
        :type tagmap: Dict[str,str]
        :param collect_output: whether to print jsonl, or return
            an array of the jsonl objects. Default: print
        :type collect_output: bool
        :raises ValueError if anything goes wrong
        '''
        jsonl_objs = []

        # Replace the opening backslashes of RTF color
        # tags in the RTF text with a different char that
        # does not otherwise occur in the text (as verified
        # in the constructor):
        color_tag_gen = self.color_tag_gen(rtf_content, rtf_color_dict)
        # For each tag, look up the 'movie-script' name, 
        # and save it in order of occurrence:
        tags_info = []

        # Gather info about the color sections.
        # The tags_info array will contain dicts
        # with info about tag_start, and 'movie-script'
        # name:
        for tag_info in color_tag_gen:
            try:
                name = tagmap[tag_info['rgb_str']]
                tag_info['name'] = name
            except KeyError:
                bad_pos = tag_info['tag_start']
                bad_color = tag_info['rgb_str']
                msg = (f"Color spec at RTF txt pos {bad_pos} is {bad_color}, " 
                       f"which is not found in tagmap {tagmap}")
                raise ValueError(msg)
            # Remember info about this tag:
            tags_info.append(tag_info)

        # Replace the backslashes of color tags with
        # a special char (which we identified in the 
        # constructor):

        protected_rtf = re.sub(r'\\cf(\d+)', '\x00cf\\1', rtf_content)

        # Next, clean out all RTF from the text. This
        # won't include the modified \cf<int> color tags,
        # b/c we replaced the backslash:
        clean_txt = rtf_to_text(protected_rtf)

        # Now remove the remaining pseudo RTF color tags, 
        # and build the jsonl objects as we go:
        idx = 0
        # Default color: black
        cur_color = 'RGB(0,0,0)'
        try:
            cur_name = tagmap[cur_color]
        except KeyError:
            cur_name = ''
        # Pattern to find the protected color tags:
        tag_pat = '\x00cf(\\d+)'
        color_place_iter = re.finditer(tag_pat, clean_txt)
        for i, nxt_tag_match in enumerate(color_place_iter):
            tag_start = nxt_tag_match.start()
            # Color control seqs end in space, the backslash of
            # another control seq, a group-associated brace,
            # or the end of the text. We eliminated all but
            # the trailing space; remove that:
            if clean_txt[idx] == ' ':
                txt = clean_txt[idx+1:tag_start]
            else:
                txt = clean_txt[idx:tag_start]
            idx = tag_start + len(nxt_tag_match.group())

            if len(txt) == 0:
                # Usually happens when color spec
                # are the first chars of the cleaned
                # txt. Update the 'movie-script' name:
                cur_name = tags_info[i]['name']
                continue

            # Remove non-printable chars, which will be
            # like '\xyz  with yz being two hex digits:
            #*******clean_txt = re.sub(r'[^\x20-\x7E]', '', clean_txt)
            #*******clean_txt = re.sub(r'[\x00-\x1F\x7F]', '', clean_txt)
            #*******clean_txt = re.sub("'\xa0", '', clean_txt)

            jsonl_obj = {cur_name : txt}
            cur_name = tags_info[i]['name']
            if collect_output:
                jsonl_objs.append(jsonl_obj)
            else:
                print(jsonl_obj)

        # All done, except for last bit of text after the 
        # last color spec:
        if clean_txt[idx] == ' ':
            last_jsonl_obj = {cur_name: clean_txt[idx+1:]}
        else:
            last_jsonl_obj = {cur_name: clean_txt[idx:]}
        if collect_output:
            jsonl_objs.append(last_jsonl_obj)
            return jsonl_objs
        else:
            print(last_jsonl_obj)
            return True

    #------------------------------------
    # color_tag_gen
    #-------------------

    def color_tag_gen(self, rtf_txt, rtf_color_dict):
        '''
        On the first call, returns a generator that on 
        subsequent calls returns successive dicts with 
        RTF color tags in given RTF text. 
        Each dict contains:

          {
            'tag_start' : <int>,
            'tag_len'   : <int>,
            'rgb_str    : <int>
          }

        The rtf_color_dict is a map from RTF color tag
        ints to RGB color texts, like:

          {2: 'RGB(24,103,40)',
           4: 'RGB(100,230,1)'
            ...
          }

        :param rtf_txt: rtf_txt over which the iterator
            will scan
        :type rtf_txt: str
        :param rtf_color_dict: map from RTF color tag number
            to RGB string 
        :type rtf_color_dict: Dict[int, str]
        :raises ValueError: for any error that occurs
        :yield: a dict describing the next RTF color tag
        :rtype: Dict[str, int]
        '''

        new_end = 0
        while (span_and_color_dict := 
               self._next_rtf_color_tag_idx(
                   rtf_txt[new_end:])):
            tag_start = new_end + span_and_color_dict['tag_start']
            tag_len   = span_and_color_dict['tag_len']
            color_num = span_and_color_dict['color_num']
            # Which RGB string is the found RTF color number?
            try:
                rgb_str = rtf_color_dict[color_num]
            except KeyError:
                msg = f"Cannot find RGB string from RTF color number {color_num}: "
                raise ValueError(msg)
            
            # Pt to just before the next color tag,
            # that is where the text of the current
            # color ends:
            new_end = tag_start + tag_len
            yield {
                'tag_start': tag_start,
                'tag_len'  : tag_len,
                'rgb_str'  : rgb_str
            }
        # Will call StopIteration automatically
        return

    #------------------------------------
    # find_rtf_controls
    #-------------------

    def find_rtf_controls(self, rtf_content):
        '''
        Given RTF content, return a set of control
        characters, such as '\\cf3' or '\\i'

        :param rtf_content: RTF content to examen
        :type rtf_content: str
        :returns a set of control strings
        '''
        control_pattern = r'\\[a-zA-Z]+\d*|\\\S'
        rtf_controls = set(re.findall(control_pattern, rtf_content))
        return rtf_controls

    #------------------------------------
    # remove_rtf_controls
    #-------------------

    def remove_rtf_controls(self, rtf_txt, controls_set):
        '''
        Given an RTF string, remove all the given control sequences
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
    # rm_color_cntls_from_set
    #-------------------

    def rm_color_cntls_from_set(self, rtf_ctrl_set):
        '''
        Given a set of RTF control chars, find all color
        controls, and remove them from the set. Color
        controls are \\cf<int>

        :param rtf_ctrl_set: set to be culled
        :type rtf_ctrl_set: set[str]
        :return: culled rtf_ctrl_set
        :rtype: set[str]
        '''
        pat = r"\\cf[\d]+"
        remaining_set = set(filter(lambda cntrl: not re.search(pat, cntrl), rtf_ctrl_set))
        return remaining_set

    #------------------------------------
    # remove_rtf_header
    #-------------------

    def remove_rtf_header(self, content):
        '''
        Removes the RTF header to best effort. We do 
        it by finding particular tables, which reside in the 
        header. Some control chars may be left of the header,
        but we will filter them later, as long as they 
        start with a backslash.

        NOTE: This removes the color table. So call this
              *after* parsing the color table in make_color_tbl()

        :param content: RTF text to rid of header tables
        :type content: str
        :returns new string with tables removed
        :rtype string
        '''
        # Remove complete table blocks including opening braces
        content = re.sub(r'\{\\fonttbl[^}]*\}', '', content)
        content = re.sub(r'\{\\colortbl[^}]*\}', '', content)  
        content = re.sub(r'\{\\\*\\expandedcolortbl[^}]*\}', '', content)
        content = re.sub(r'\{\\stylesheet[^}]*\}', '', content)
        content = re.sub(r'\{\\listtable[^}]*\}', '', content)
        content = re.sub(r'\{\\cocoaplatform0\{[^}]*\}', 
                         r'\\cocoaplatform0', 
                         content)
        return content

    #------------------------------------
    # clean_rtf
    #-------------------

    def clean_rtf(self, dirty_rtf):
        '''
        Given an RTF string, remove all RTF tags, other
        than color tags (like '\\cf2')

        :param dirty_rtf: RTF text to clean
        :type dirty_rtf: str
        :return: new, clean string
        :rtype: str
        '''

        # Get rid of header info as best as possible, because
        # its tables have controls that do not start with 
        # backslashes:

        dirty_rtf = self.remove_rtf_header(dirty_rtf)

        # Get set of all RTF control sequences used in 
        # remaining text, so we can remove all but the 
        # color specs:
        rtf_controls = self.find_rtf_controls(dirty_rtf)
        # Retain the \cf color controls:
        rtf_controls = self.rm_color_cntls_from_set(rtf_controls)
        clean_rtf = self.remove_rtf_controls(dirty_rtf, rtf_controls)
        return clean_rtf

    #------------------------------------
    # _next_rtf_color_tag_idx
    #-------------------    

    def _next_rtf_color_tag_idx(self, rtf_str):
        '''
        Given an RTF string, find the next RTF control
        tag that designates a color. Return a dict:
           {"tag_start" : <int>,
            "tag_len"   : <int>,
            "color_num" : <int>
            }

        :param rtf_str: RTF string to examine
        :type rtf_str: str
        :raises ValueError: for malformed color tag
        :return: dict describing the next tag
        :rtype: Dict[str, int]
        '''
        match = re.search(r'\\cf([\d]*)', rtf_str)
        if not match:
            return None
        # Got a match of somthing like '\cf2', with
        # group 1 being '2':
        try:
            color_num = int(match[1])
            return {"tag_start": match.span()[0],
                    "tag_len"  : len(match[0]),
                    "color_num": color_num
                    }
        except IndexError:
            # Match did not have a number after the \cf
            msg = f"Found '{match[0]}' in RTF, but this does not end with a number"
            raise ValueError(msg)
        except ValueError:
            # Group 1 existed, but is not an int:
            msg = f"Found '{match[0]}' in RTF, which does not end with a proper integer"
            raise ValueError(msg)
        
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
        to legal RGB values. Return True if OK, else ValueError

        :param tagmap: the map to be checked
        :type tagmap: Dict[str, str]
        :return: a True if OK, else error
        :rtype: boolean
        :raises: ValueError for format errors
        '''
        if len(tagmap) == 0:
             return True
        # All keys must be strings:
        for key, rgb in tagmap.items():
            if type(key) != str:
                raise ValueError(f"Tabmap keys must be strings, not {key}")
            # Values must be of the form
            # 'RGB(<int>,<int>,<int>,[float])' with <int> between 0 and 255,
            #                                  and the float being 0 to 1, or
            # '#xxyyzz' with x, y, and z being Hex chars, 00 to FF
            rgb = rgb.upper()
            if rgb.startswith('RGB'):
                return self.validate_rgb_string(rgb)
            elif rgb.startswith('#'):
                return self.validate_rgb_hex_string(rgb)
            
        # We haven't bombed out, so:
        return True

    #------------------------------------
    # validate_rgb_string
    #-------------------

    def validate_rgb_string(self, rgb_string):
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

    def validate_rgb_hex_string(self, hex_string):
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
            #    {3 : 'RGB(10,40,200)'}
            # The i+1 is because RTF color tables and tags
            # are 1-origin:
            colors[i+1] = f"RGB({int(r)},{int(g)},{int(b)})"
        
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
