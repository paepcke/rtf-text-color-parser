 # **********************************************************
 #
 # @Author: Andreas Paepcke
 # @Date:   2025-07-05 14:07:41
 # @File:   /Users/paepcke/VSCodeWorkspaces/rtf-text-color-parser/src/parser/__tests__/test_rtf_color_par.py
 # @Last Modified by:   Andreas Paepcke
 # @Last Modified time: 2025-07-05 19:53:22
 #
 # **********************************************************

import unittest

from parser.rtf_color_parser import RTFParser

class RTFColorParserTester(unittest.TestCase):
    
    def setUp(self):
        self.rtf_content = self.make_rtf_content()        
        self.tagmap = self.make_tagmap()
        # The is_unittest prevents the RTFParser
        # constructor from running most of its code.
        self.parser = RTFParser(None, tagmap=self.tagmap, is_unittest=True)

# ------------- Tests ------------

    #------------------------------------
    # test_make_color_tbl
    #-------------------    

    def test_make_color_tbl(self):
        color_tbl = self.parser.make_color_tbl(self.rtf_content)
        expected = {
            1: 'RGB(255,255,255)', 
            2: 'RGB(74,21,48)', 
            3: 'RGB(255,255,255)', 
            4: 'RGB(11,93,162)' 
        }
        self.assertDictEqual(color_tbl, expected)

    #------------------------------------
    # test_check_tagmap
    #-------------------

    def test_check_tagmap(self):
        pass

    #------------------------------------
    # test_validate_rgb_string
    #-------------------    

    def test_validate_rgb_string(self):
        pass

    #------------------------------------
    # test_rgb_hex_string
    #-------------------

    def test_rgb_hex_string(self):
        pass

    #------------------------------------
    # test_remove_rtf_controls
    #-------------------    

    def test_remove_rtf_controls(self):
        pass

    #------------------------------------
    # test_next_rtf_color_tag_idx
    #-------------------

    def test_next_rtf_color_tag_idx(self):
        pass

    #------------------------------------
    # test_output_txt_script
    #-------------------

    def test_output_txt_script(self):
        pass

# ------------- Utilities ------------

    #------------------------------------
    # make_rtf_content
    #-------------------    

    def make_rtf_content(self):
        content = r'''{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;\f1\fswiss\fcharset0 ArialMT;}
{\colortbl;\red255\green255\blue255;\red74\green21\blue148;\red255\green255\blue255;\red11\green93\blue162;
\red26\green26\blue26;}
{\*\expandedcolortbl;;\cssrgb\c36863\c17255\c64706;\cssrgb\c100000\c100000\c100000;\cssrgb\c0\c44706\c69804;
\cssrgb\c13333\c13333\c13333;}
\margl1440\margr1440
\deftab720
\pard\pardeftab720\partightenfactor0

\f0\fs32 \cf2 \cb3 \up0 \nosupersub \ulnone What risks do you run?\
\pard\pardeftab720\partightenfactor0
\cf4 In ISTDP, we want to ensure will.\
\
\cf4 That's a thoughtful approach.
\cf2 I want that too.
'''
        return content
    
    #------------------------------------
    # make_tagmap
    #-------------------

    def make_tagmap(self):
        tagmap = {
            'Expert': 'RGB(74,21,48)',
            'AI'    : 'RGB(11,93,162)' 
        }
        return tagmap

# ------------- Main -----------
if __name__ == '__main__':
    unittest.main()