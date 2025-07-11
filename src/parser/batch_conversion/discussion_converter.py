#!/usr/bin/env Python
 # **********************************************************
 #
 # @Author: Andreas Paepcke
 # @Date:   2025-07-09 10:57:37
 # @File:   /Users/paepcke/VSCodeWorkspaces/rtf-text-color-parser/src/parser/batch_conversion/ai_discussions.py
 # @Last Modified by:   Andreas Paepcke
 # @Last Modified time: 2025-07-10 18:51:24
 #
 # **********************************************************

import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import List

import jsonlines

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

    This result is available from an instance of DiscussionConverter
    as a the value of inst.discussion. If an outfile is provided, that
    file will contain the structure as legal JSON.

    Assumptions:
        o in_dir is a directory with all the .rtf files
        o each .rtf file's name is a concatenation of 
          client name and defense.
    '''

    #------------------------------------
    # Constructor
    #-------------------

    def __init__(self, rtf_dir, jsonl_dir=None, outfile=None, unittesting=False):
        '''
        Run conversion for each .rtf file in the given rtf_dir, create a
        corresponding .jsonl file in the jsonl_dir, and generate one
        .json file with the combined result. This result will be in
        <inst>.discussion

        :param rtf_dir: where the .rtf files are
        :type rtf_dir: str
        :param jsonl_dir: where the jsonl files will be. If not
            provided, they are not preserved
        :type jsonl_dir: [str]
        :param outfile: file to place the result as a JSON dump, 
            defaults to None
        :type outfile: str, optional
        :param unittesting: suppress all processing during instance creation, defaults to False
        :type unittesting: bool, optional
        '''
        if unittesting:
            return

        try:
            # If the .jsonl files are not requested to be provided,
            # keep them in a temp dir:
            if jsonl_dir is None:
                jsonl_dir_is_tmp = True
                jsonl_dir_obj = tempfile.TemporaryDirectory(dir='/tmp', prefix='discussion_converter_')
                jsonl_dir = jsonl_dir_obj.name
            else:                
                # Caller specified a jsonl dir to use, and preserve
                jsonl_dir_is_tmp = False
                if not os.path.exists(jsonl_dir) or not os.path.isdir(jsonl_dir):
                    # Need to create the jsonl directory:
                    os.mkdir(jsonl_dir)
                if outfile is not None and os.path.exists(outfile):
                    if not self.confirm_overwrite(outfile):
                        print("Aborting operation; nothing overwritten")
                        sys.exit()
            # Ensure dele
            tagmap = {
                'RGB(74,21,148)' : 'Expert',
                'RGB(11,93,162)' : 'AI'
            }

            rtf_path_iter = self.mk_rtf_path_iter(rtf_dir)
            
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
                jsonl_full_path = os.path.join(jsonl_dir, jsonl_file)
                with open(jsonl_full_path, 'r') as fd:
                    conversation_turns = fd.readlines()
                new_conversation = {
                    "clientName"   : client,
                    "defense"      : defense,
                    "conversation" : conversation_turns
                }
                self.discussion.append(new_conversation)

            if outfile is not None:
                with open(outfile, 'w') as fd:
                    json.dump(self.discussion, fd)

        finally:
            if jsonl_dir_is_tmp:
                # Remove the temporary jsonl_dir:
                jsonl_dir.cleanup()

    #------------------------------------
    # build_one_case_discussion
    #-------------------

    def build_one_case_discussion(self, jsonl_file):
        client_nm, defense = self.parse_fname(jsonl_file)
        with jsonlines.open(jsonl_file) as reader:
            conversation_turns = list(reader)

        new_conversation = {
            "clientName"   : client_nm,
            "defense"      : defense,
            "conversation" : conversation_turns
        }
        return new_conversation
        

    #------------------------------------
    # parse_fname
    #-------------------

    def parse_fname(self, fname):
        '''
        Given a file name such as /foo/bar/adamDenial.jsonl,
        return a two-tuple 'Adam' and 'denial'. The file name is
        assumed to be a camelcased concatenation of a client
        name, and a defense. Note that some defenses have more
        than one part: marcelCharacterDefense. For those cases
        the name is still the first part ('marcel'). The rest
        concatenated, and lower-cased (characterdefense).

        :param fname: path whose name part is to be parsed
        :type fname: str
        :return: the broken out name (capitalized), and the
           lower-cased defense
        :rtype: Tuple[str,str]
        '''

        name_defense_str = Path(fname).stem
        name_parts: List[str] = re.findall(r'[a-z]+|[A-Z][a-z]*', name_defense_str)
        if len(name_parts) < 2:
            raise ValueError(f"File name {fname} is not partitionable into two or more parts")
        name = name_parts[0].capitalize()
        defense = ''.join(name_parts[1:]).lower()
        
        return(name,defense)
        

    #------------------------------------
    # rtf_to_jsonl
    #-------------------        

    def rtf_to_jsonl(self, rtf_path, tagmap, jsonl_dir):
        # Create <jsonl_dir>/<rtf_filename_only>.jsonl:
        jsonl_path = (Path(jsonl_dir) / Path(rtf_path).stem).with_suffix('.jsonl')
        jsonl_objs = RTFParser(rtf_path, 
                               tagmap, 
                               collect_output=True).jsonl_objs
        with open(jsonl_path, 'w') as fd:
            fd.writelines(json.dumps(line) + '\n' for line in jsonl_objs)
        
    #------------------------------------
    # mk_rtf_path_iter
    #-------------------

    def mk_rtf_path_iter(self, rtf_dir):
        return filter(lambda fname: fname.endswith('.rtf'), 
               [os.path.join(rtf_dir, fname)
                for fname
                in os.listdir(rtf_dir)]
                )

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

    desc = ("Takes a directory of *.rtf files of Expert/AI casefile "
            "discussions. Generates a JSON file that combines all information "
            "in those RTF files. \n"
            "Each RTF file name should be of the camel case form \n"
            "   <clientName><Defense>.rtf\n" 
            "If outfile is not provided, writes result struct to stdout")

    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]),
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     description=desc
                                     )

    parser.add_argument('-o', '--outfile',
                        help='fully qualified path to result .json file',
                        default=None)
    
    parser.add_argument('-j', '--jsonl_dir',
                        help='where to save .jsonl constituent files; default: discard',
                        default=None)
        
    parser.add_argument('rtf_dir',
                        help='directory containing the RTF files')

    args = parser.parse_args()

    # Expandvars takes care of tilde and ${HOME}
    rtf_dir = os.path.expandvars(os.path.expanduser(args.rtf_dir))
    if not os.path.exists(rtf_dir):
        print(f"RTF directory {rtf_dir} does not exist")
        sys.exit(1)

    # Resolve tilde and $HOME
    jsonl_dir = os.path.expandvars(os.path.expanduser(args.jsonl_dir))
    outfile   = os.path.expandvars(os.path.expanduser(args.outfile))

    # Do the conversion; the constructor will check whether
    # outfile already exist, and allow user to agree to 
    # overwrite:

    #***********
    #print(f"rtf_dir: {rtf_dir}")
    #print(f"jsonl_dir: {args.jsonl_dir}")
    #print(f"outfile: {args.outfile}")
    #***********

    converter = DiscussionConverter(
        rtf_dir, 
        jsonl_dir=jsonl_dir,
        outfile=outfile)

    # If outfile was provided, it will now contain the
    # JSON result:
    if args.outfile:
        print(f"File {args.outfile} contains JSON result")
    else:
        print(converter.discussion)