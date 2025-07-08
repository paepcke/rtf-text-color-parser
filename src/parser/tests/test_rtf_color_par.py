 # **********************************************************
 #
 # @Author: Andreas Paepcke
 # @Date:   2025-07-05 14:07:41
 # @File:   /Users/paepcke/VSCodeWorkspaces/rtf-text-color-parser/src/parser/__tests__/test_rtf_color_par.py
 # @Last Modified by:   Andreas Paepcke
 # @Last Modified time: 2025-07-08 12:45:22
 #
 # **********************************************************

import unittest
from striprtf.striprtf import rtf_to_text
from parser.rtf_color_parser import RTFParser

class RTFColorParserTester(unittest.TestCase):
    
    def setUp(self):
        self.rtf_content = self.make_rtf_content()        
        self.tagmap = self.make_tagmap()
        # The is_unittest prevents the RTFParser
        # constructor from running most of its code.
        self.parser = RTFParser(None, tagmap=self.tagmap, is_unittest=True)

        # Normally, the RTFParser's contructor initializes
        # a char that can be used to replace backslashes
        # that initiate color tags in RTF texts. Since we
        # bypass the constructor, we must set that char
        # ourselves:
        self.parser.color_tag_marker_char = '\x00'

        self.rtf_color_dict = self.parser.make_color_tbl(self.rtf_content)

# ------------- Tests ------------

    #------------------------------------
    # test_make_color_tbl
    #-------------------    

    def test_make_color_tbl(self):
        color_tbl = self.parser.make_color_tbl(self.rtf_content)
        expected = {
            1: 'RGB(255,255,255)', 
            2: 'RGB(74,21,148)', 
            3: 'RGB(255,255,255)', 
            4: 'RGB(11,93,162)',
            5: 'RGB(26,26,26)' 
        }
        self.assertDictEqual(color_tbl, expected)

    #------------------------------------
    # test_check_tagmap
    #-------------------

    def test_check_tagmap(self):
        # Our test tagmap is:
        #tagmap = {
        #    'Expert': 'RGB(74,21,48)',
        #    'AI'    : 'RGB(11,93,162)' 
        #}        
        check_res = self.parser.check_tagmap(self.tagmap)
        self.assertTrue(check_res)

        # Does it catch errors?

        # Key must be a string:
        bad_tagmap = {
            1: 'RGB(256,0,0)'
        }
        with self.assertRaises(ValueError):
            check_res = self.parser.check_tagmap(bad_tagmap)
        
        # RGB values must be within bounds:
        bad_tagmap = {
            'Fred': 'RGB(256,0,0)'
        }
        with self.assertRaises(ValueError):
            check_res = self.parser.check_tagmap(bad_tagmap)



    #------------------------------------
    # test_validate_rgb_string
    #-------------------    

    def test_validate_rgb_string(self):
        rgb = 'RGB( 134, 1,     5)'
        self.assertTrue(self.parser.validate_rgb_string(rgb))

        # Out of RGB range:
        rgb = 'RGB(0,0,-1)'
        with self.assertRaises(ValueError):
            self.parser.validate_rgb_string(rgb)
        rgb = 'RGB(0,0,300)'
        with self.assertRaises(ValueError):
            self.parser.validate_rgb_string(rgb)

        # Bad format:
        rgb = '(0,0,4)'
        with self.assertRaises(ValueError):
            self.parser.validate_rgb_string(rgb)

    #------------------------------------
    # test_rgb_hex_string
    #-------------------

    def test_rgb_hex_string(self):
        rgb = '#BaCD12'
        self.assertTrue(self.parser.validate_rgb_hex_string(rgb))

        # No hash:
        rgb = 'BBCAFF'
        with self.assertRaises(ValueError):
            self.parser.validate_rgb_hex_string(rgb)

        # Not valid HEX number:
        rgb = '#GGCAFF'
        with self.assertRaises(ValueError):
            self.parser.validate_rgb_hex_string(rgb)
        
    #------------------------------------
    # test_find_rtf_controls
    #-------------------

    def test_find_rtf_controls(self):
        rtf_content = ("\\cssrgb\\c13333\\c13333\\c13333;}"
                       "\\nosupersub \\ulnone What risks do you run?"
                       "Foobar")
        control_set = self.parser.find_rtf_controls(rtf_content)
        expected = set (['\\cssrgb','\\c13333', '\\nosupersub', '\\ulnone'])
        self.assertSetEqual(control_set, expected)

    #------------------------------------
    # test_rm_color_cntls_from_set
    #-------------------    

    def test_rm_color_cntls_from_set(self):
        rtf_set = set(['\\rtf1', '\\cf1', '\\ansi', '\\ansicpg1252', '\\cf10'])
        no_color_tags_set = self.parser.rm_color_cntls_from_set(rtf_set)

        expected_set = set(['\\rtf1', '\\ansi', '\\ansicpg1252'])

        self.assertSetEqual(no_color_tags_set, expected_set)

    #------------------------------------
    # test__next_rtf_color_tag_idx
    #-------------------

    def test__next_rtf_color_tag_idx(self):
        rtf_content = ("\\cssrgb\\cf4\\c13333 I am here."
                       "\\i your are \\cf2 there")
        controls = ['\\cf4', '\\cf2']
        start = 0
        for ctrl in controls:
            tag_dict  = self.parser._next_rtf_color_tag_idx(rtf_content[start:])
            tag_start = tag_dict['tag_start']
            tag_len   = tag_dict['tag_len']
            tag       = rtf_content[start+tag_start:start+tag_start+tag_len]
            # Pt past the tag for the next round:
            start = tag_start + tag_len
            self.assertEqual(tag, ctrl)
            if tag == '\\cf4':
                self.assertEqual(tag_dict['color_num'], 4)
            elif tag == '\\cf2':
                self.assertEqual(tag_dict['color_num'], 2)
        # Test malformed color code:
        rtf_content = "foo\\cf bar"
        with self.assertRaises(ValueError):
            self.parser._next_rtf_color_tag_idx(rtf_content)

    #------------------------------------
    # test_color_tag_gen
    #-------------------

    def test_color_tag_gen(self):
        rtf_txt = ("\\cssrgb\\cf4\\c13333 I am here."
                   "\\i You are \\cf2 there")
        tag_gen = self.parser.color_tag_gen(rtf_txt, self.rtf_color_dict)
        first_res = next(tag_gen)
        expected = {
            'tag_start': 7,
            'tag_len'  : 4,
            'rgb_str'  : self.rtf_color_dict[4]
        }
        self.assertDictEqual(first_res, expected)

        second_res = next(tag_gen)
        expected = {
            'tag_start': 40,
            'tag_len'  : 4,
            'rgb_str'  : self.rtf_color_dict[2]
        }
        self.assertDictEqual(second_res, expected)

        # Should throw StopIteration:
        with self.assertRaises(StopIteration):
            next(tag_gen)

        # Now longer txt:
        rtf_txt = "{\\rtf1\\ansi\\ansicpg1252\\cocoartf2822\n\\cocoatextscaling0\\cocoaplatform0{\\fonttbl\\f0\\fswiss\\fcharset0 Helvetica;\\f1\\fswiss\\fcharset0 ArialMT;}\n{\\colortbl;\\red255\\green255\\blue255;\\red74\\green21\\blue148;\\red255\\green255\\blue255;\\red11\\green93\\blue162;\n\\red26\\green26\\blue26;}\n{\\*\\expandedcolortbl;;\\cssrgb\\c36863\\c17255\\c64706;\\cssrgb\\c100000\\c100000\\c100000;\\cssrgb\\c0\\c44706\\c69804;\n\\cssrgb\\c13333\\c13333\\c13333;}\n\\margl1440\\margr1440\n\\deftab720\n\\pard\\pardeftab720\\partightenfactor0\n\n\\f0\\fs32 \\cf2 \\cb3 \\up0 \\nosupersub \\ulnone What risks do you run?\\\n\\pard\\pardeftab720\\partightenfactor0\n\\cf4 In ISTDP, we want to ensure will.\\\n\\\n\\cf4 That's a thoughtful approach.\n\\cf2 I want that too.\\\n           }\n"
        tag_gen = self.parser.color_tag_gen(rtf_txt, self.rtf_color_dict)
        # Expected
        exp_starts    = [492,588,630,665]
        exp_rgb_strs  = ['RGB(74,21,148)',
                         'RGB(11,93,162)', 
                         'RGB(11,93,162)', 
                         'RGB(74,21,148)']
        
        for i, tag_info in enumerate(tag_gen):
            self.assertEqual(tag_info['tag_start'], exp_starts[i])
            self.assertEqual(tag_info['rgb_str'], exp_rgb_strs[i])
                                                        
    #------------------------------------
    # test_clean_rtf
    #-------------------

    def test_clean_rtf(self):
        rtf_txt = ("\\cssrgb\\cf4\\c13333 I am here."
                   "\\i You are \\cf2 there")
        cleaned  = self.parser.clean_rtf(rtf_txt)
        expected = "\\cf4 I am here. You are \\cf2 there"
        self.assertEqual(cleaned, expected)

    #------------------------------------
    # test_output_txt_script
    #-------------------

    def test_output_txt_script(self):

        jsonl_arr = self.parser.output_txt_script(
            self.rtf_content,
            self.rtf_color_dict,
            self.tagmap,
            collect_output=True
        )
        expected = [{'Expert': 'What risks do you run?\n'},
                    {'AI': 'In ISTDP, we want to ensure will.\n\n'},
                    {'AI': "That's a thoughtful approach."},
                    {'Expert': 'I want that too.\n           '}
                    ]
        self.assertListEqual(jsonl_arr, expected)

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
\cf2 I want that too.\
           }
'''
        return content
    
    #------------------------------------
    # make_tagmap
    #-------------------

    def make_tagmap(self):
        tagmap = {
            'RGB(74,21,148)' : 'Expert',
            'RGB(11,93,162)' :'AI'
        }
        return tagmap

# ------------- Main -----------
if __name__ == '__main__':
    unittest.main()