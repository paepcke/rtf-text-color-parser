 # **********************************************************
 #
 # @Author: Andreas Paepcke
 # @Date:   2025-07-09 10:57:37
 # @File:   /Users/paepcke/VSCodeWorkspaces/rtf-text-color-parser/src/parser/batch_conversion/ai_discussions.py
 # @Last Modified by:   Andreas Paepcke
 # @Last Modified time: 2025-07-09 14:15:45
 #
 # **********************************************************

import os
from pathlib import Path
import re
import sys
from typing import List

from parser.rtf_color_parser import RTFParser


class DiscussionConverter:
    '''
    Runs through RTF files in a given directory. Converts each into
    a separate .jsonl file in which each conversation turn is represented
    in a jsonl object {<rolename>: <utterance>}.

    Then generates a single file that combines the .jsonl files into a
    single .json file with this structure:

    [
       {"clientName" : <str>,
        "defense".   : <str>,
        "conversation" : [
            {'Expert': <str>},
            {'AI'.   : <str>},
            {'Expert': <str>},
                 ...
        ]
       },
       {"clientName" : <str>,
        "defense".   : <str>,
        "conversation" : [
            {'Expert': <str>},
            {'AI'.   : <str>},
            {'Expert': <str>},
                 ...
        ],
        ...
    ]

    Assumptions:
        o in_dir is a directory with all the .rtf files
        o each .rtf file's name is a concatenation of 
          client name and defense.
    '''

    #------------------------------------
    # Constructor
    #-------------------

    def __init__(self, rtf_dir, jsonl_dir, outfile=None, unittesting=False):
        '''
        Run conversion for each .rtf file in the given rtf_dir, create a
        corresponding .jsonl file in the jsonl_dir, and generate one
        .json file with the combined result. This result will be in
        <inst>.discussion

        :param rtf_dir: where the .rtf files are
        :type rtf_dir: str
        :param jsonl_dir: where the jsonl files will be
        :type jsonl_dir: str
        :param outfile: file to place the result, defaults to None
        :type outfile: str, optional
        :param unittesting: suppress all processing during instance creation, defaults to False
        :type unittesting: bool, optional
        '''
        if unittesting:
            return                
        if not os.path.exists(jsonl_dir) or not os.path.isdir(jsonl_dir):
            # Need to create the jsonl directory:
            os.mkdir(jsonl_dir)
        if os.path.exists(outfile):
            if not self.confirm_overwrite(outfile):
                print("Aborting operation; nothing overwritten")
                sys.exit()

        tagmap = {
            'RGB(74,21,148)' : 'Expert',
            'RGB(11,93,162)' : 'AI'
        }

        rtf_path_iter = filter(lambda fname: fname.endswith('.rtf'), 
                               os.listdir(rtf_dir))
        
        # Convert each file from rtf to a .jsonl file
        # of {<role>: <utterance>} objects:
        for rtf_path in rtf_path_iter:
            self.rtf_to_jsonl(rtf_path, tagmap, jsonl_dir)

        # Create the final JSON structure in memory as
        # lists and dicts:
        # Outermost container:
        self.discussion = []

        jsonl_path_iter = filter(lambda fname: fname.endswith('.jsonl'), 
                               os.listdir(jsonl_dir))

        for jsonl_file in jsonl_path_iter:
            # Extract client name and their defense from
            # the file name:
            (client, defense) = self.parse_fname(jsonl_file)
            with open(jsonl_file, 'r') as fd:
                conversation_turns = fd.readlines()
            new_conversation = {
                "clientName"   : client,
                "defense"      : defense,
                "conversation" : conversation_turns
            }
            self.discussion.append(new_conversation)

    #------------------------------------
    # parse_fname
    #-------------------

    def parse_fname(self, fname):
        '''
        Given a file name such as /foo/bar/adamDenial.jsonl,
        return a two-tuple 'Adam' and 'denial'. The file name is
        assumed to be a camelcased concatenation of a client
        name, and a defense.

        :param fname: path whose name part is to be parsed
        :type fname: str
        :return: the broken out name (capitalized), and the
           lower-cased defense
        :rtype: Tuple[str,str]
        '''

        name_defense_str = Path(fname).stem
        name_parts: List[str] = re.findall(r'[a-z]+|[A-Z][a-z]*', name_defense_str)
        if len(name_parts) != 2:
            raise ValueError(f"File name {fname} is not partitionable into two parts")

        return(name_parts[0].capitalize(), name_parts[1].lower())
        

    #------------------------------------
    # rtf_to_jsonl
    #-------------------        

    def rtf_to_jsonl(self, rtf_path, tagmap, jsonl_dir):
        # Create <jsonl_dir>/<rtf_filename_only>.jsonl:
        jsonl_path = (Path(jsonl_dir) / rtf_path.stem).with_suffix('.jsonl')
        jsonl_list = RTFParser(rtf_path, tagmap, collect_output=True)
        with open(jsonl_path, 'w') as fd:
            fd.writelines(jsonl_list)
        
    #------------------------------------
    # mk_rtf_paths
    #-------------------

    def mk_rtf_paths(self, rtf_dir):
        all_files = os.listdir(rtf_dir)
        


    #------------------------------------
    # confirm_overwrite
    #-------------------

    def confirm_overwrite(self, path, default_confirm=False):
        '''
        Asks for confirmation whether to overwrite the given path.

        :param path: file to be overwritten
        :type path: str
        :param default_confirm: user default action regarding overwriting, defaults to False
        :type default_confirm: bool, optional
        :return: whether or not to overwrite
        :rtype: bool
        '''
        while True:
            prompt = f"Overwrite output file {path}? (y/N)"
            response = input(prompt).strip().lower()
            if response == '':
                return default_confirm
            elif response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Invalid input. Please enter 'y', 'n', or just press Enter to not overwrite.")
        

# ------------------------ Main ------------
if __name__ == '__main__':
    ConvertDiscussions()