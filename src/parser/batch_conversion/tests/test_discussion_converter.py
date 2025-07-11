 # **********************************************************
 #
 # @Author: Andreas Paepcke
 # @Date:   2025-07-09 13:03:22
 # @File:   /Users/paepcke/VSCodeWorkspaces/rtf-text-color-parser/src/parser/batch_conversion/tests/test_discussion_converter.py
 # @Last Modified by:   Andreas Paepcke
 # @Last Modified time: 2025-07-10 18:50:48
 #
 # **********************************************************

import json
import os
from pathlib import Path
import tempfile
import unittest

import jsonlines

from parser.batch_conversion.discussion_converter import DiscussionConverter
from parser.rtf_color_parser import RTFParser

class DiscussionConverterTester(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.tagmap = {
            'RGB(74,21,148)' : 'Expert',
            'RGB(11,93,162)' : 'AI'
        }


    def setUp(self):
        # Test directory, which we wipe between each test
        self.tst_dir = tempfile.TemporaryDirectory(dir= '/tmp', prefix='convert_test')
        # Underneath: one dir for test RTF files:
        self.rtf_dir_nm = os.path.join(self.tst_dir.name, 'RtfDir')
        os.mkdir(self.rtf_dir_nm)
        # Also underneath: destination where module under
        # test will be asked to place jsonl files
        self.jsonl_dir_nm = os.path.join(self.tst_dir.name, 'JsonlDir')
        os.mkdir(self.jsonl_dir_nm)
        # Finally: a reference dir where we place our own conversion of
        # rtf to jsonl files for when testing module portions that
        # operate on .jsonl files:
        self.jsonl_ref_dir_nm = os.path.join(self.tst_dir.name, 'JsonlReferenceDir')
        os.mkdir(self.jsonl_ref_dir_nm)

        # Create RTF test files
        (self.megan_rtf_file_nm, self.tamara_rtf_file_nm) = self.mk_rtf_files()
        (self.megan_jsonl_ref_nm, self.tamara_jsonl_ref_nm) = \
            self.mk_jsonl_reference_files()
        
        # Create a .json file as a JSON discussion: with the 
        # entire combination of Megan and Tamara's names, 
        # defenses, and discussions between expert and AI
        self.discussion_json_nm = self.mk_reference_conversation()

        # A converter instance; constructor does nothing other
        # than instance creation:
        self.converter = DiscussionConverter(
            self.rtf_dir_nm, 
            self.jsonl_dir_nm,
            unittesting=True
            )

    def tearDown(self):
        self.tst_dir.cleanup()
            
    #------------- Tests -----------------    

    #------------------------------------
    # test_parse_fname
    #-------------------    

    def test_parse_fname(self):
        client_name, defense = self.converter.parse_fname(self.megan_rtf_file_nm)
        self.assertEqual(client_name, 'Megan')
        self.assertEqual(defense, 'denial')

        # Try one where defense is a composite:
        fname = 'marcelCharacterDefense'
        client_name, defense = self.converter.parse_fname(fname)
        self.assertEqual(client_name, 'Marcel')
        self.assertEqual(defense, 'characterdefense')


    #------------------------------------
    # test_mk_rtf_path_iter
    #-------------------

    def test_mk_rtf_path_iter(self):
        path_iter = self.converter.mk_rtf_path_iter(self.rtf_dir_nm)
        expected = set([self.megan_rtf_file_nm, self.tamara_rtf_file_nm])
        path_set = set(path_iter)
        self.assertSetEqual(path_set, expected)

    #------------------------------------
    # test_build_one_case_discussion
    #-------------------

    def test_build_one_case_discussion(self):
        conversation = self.converter.build_one_case_discussion(
            self.megan_jsonl_ref_nm)
        self.assertEqual(conversation['clientName'], 'Megan')
        self.assertEqual(conversation['defense'], 'denial')
        dialog = conversation['conversation']
        self.assertEqual(len(dialog), 3)
        first_turn_jsonl = dialog[0]
        self.assertTrue(first_turn_jsonl['Expert'].startswith('You believe'))

    #------------------------------------
    # test_rtf_to_jsonl
    #-------------------

    def test_rtf_to_jsonl(self):
        # Have the module under test take one
        # RTF file, and generate a .jsonl file
        # from it into self.jsonl_dir_nm:
        self.converter.rtf_to_jsonl(
            self.tamara_rtf_file_nm, 
            self.tagmap, 
            self.jsonl_dir_nm)
        # Pull our previously generated reference
        # jsonl, and compare dialog-turn-wise with
        # what the converter created:
        with jsonlines.open(self.tamara_jsonl_ref_nm) as reader:
            ref_jsonl = list(reader)
        try:
            new_jsonl_fname = os.path.join(self.jsonl_dir_nm, 
                                           'tamaraDenial.jsonl')
            with jsonlines.open(new_jsonl_fname) as reader:
                generated_tamara_jsonls = list(reader)
        except Exception as e:
            raise AssertionError(f"Supposed file tamaraDenial.jsonl not found: {e}")
        
        # Each dialog turn is a legal Python dict:
        both_jsonl_streams = zip(generated_tamara_jsonls, ref_jsonl)
        for (generated, reference) in both_jsonl_streams:
            self.assertDictEqual(generated, reference)

    #------------------------------------
    # test_all_together_now
    #-------------------

    def test_all_together_now(self):
        # Given the RTF directory, create one
        # combined JSON structure:
        conversion = DiscussionConverter(
            self.rtf_dir_nm,
            self.jsonl_dir_nm,
            outfile=None
        )
        discussion = conversion.discussion
        self.assertEqual(len(discussion), 2)

        # Get the expected discussion as reference:
        with open(self.discussion_json_nm, 'r') as fd:
            discussion_reference = json.load(fd)

        # Sort both discussions by client name to facilitate
        # comparison:
        discussion_sorted = sorted(discussion, key=lambda one_dict: one_dict['clientName'])
        reference_sorted  = sorted(discussion_reference, 
                                   key=lambda one_dict: one_dict['clientName'])
        self.assertDiscussionsEqual(discussion_sorted, reference_sorted)

    #------------- Utilities -----------------

    def mk_rtf_files(self): 
        rtf1 = r'''{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;\red74\green21\blue148;\red255\green255\blue255;\red11\green93\blue162;
}
{\*\expandedcolortbl;;\cssrgb\c36863\c17255\c64706;\cssrgb\c100000\c100000\c100000;\cssrgb\c0\c44706\c69804;
}
\margl1440\margr1440
\deftab720
\pard\pardeftab720\partightenfactor0

\f0\fs32 \cf2 \cb3 \up0 \nosupersub \ulnone You believe this would be confrontational. However, since the patient has mentioned feeling resentment and regret, we are merely reminding her of the feelings she is currently denying. Further, when I ask about the feelings she has about losing that job, that general question opens up inquiry beyond the feelings she mentioned. As for assurance, I am only asserting the existence of feelings she has already mentioned. Thus, that does not undermine the patient's self-relfection. Regarding the alliance, when I ask "shall we" take a look at your feelings, I am not accusing her. I am inviting her.\
\pard\pardeftab720\partightenfactor0
\cf4 I appreciate your perspective, and it\'92s great that you\'92re thinking critically about these aspects. However, I\'92d like to emphasize the importance of considering how the patient might experience your approach. While you may feel that you are simply bringing up feelings she has already mentioned, it\'92s possible that she could perceive your directness as pressure, especially if she is feeling vulnerable or defensive. It\'92s crucial to create an environment where she feels safe to explore her emotions without feeling cornered. The language we choose can either facilitate this exploration or inadvertently hinder it. How do you think you might adjust your approach to better foster that sense of safety?\cf2 \'a0I think you may be misunderstanding my intervention. Remember, I said, "shall we take a look." That does not pressure her. It leaves space for her to look or not look at her feelings. For instance, let's look at your intervention. When you ask "about what that experience has meant for you" you invite her to intellectualize about the meanings rather than describe her thoughts. Thus, the danger in your intervention is that you invite a defense rather than help her look under defenses.
}'''

        rtf2 = r'''{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;\f1\fswiss\fcharset0 ArialMT;}
{\colortbl;\red255\green255\blue255;\red74\green21\blue148;\red255\green255\blue255;\red11\green93\blue162;
\red26\green26\blue26;}
{\*\expandedcolortbl;;\cssrgb\c36863\c17255\c64706;\cssrgb\c100000\c100000\c100000;\cssrgb\c0\c44706\c69804;
\cssrgb\c13333\c13333\c13333;}
\margl1440\margr1440
\deftab720
\pard\pardeftab720\partightenfactor0

\f0\fs32 \cf2 \cb3 \up0 \nosupersub \ulnone \
\
I wonder what risks you run into when you explore right away without finding out if the patient is willing to explore? Isn't there a risk that the therapy begins with your will and not the will of the patient?\
\pard\pardeftab720\partightenfactor0
\cf4 You raise an important concern. In ISTDP, we want to ensure that the exploration aligns with the patient's willingness and readiness to engage in deeper emotional work. If we push too quickly or without attuning to the patient\'92s readiness, we risk causing defensiveness or resistance, which can create a barrier to the therapeutic alliance. That's why it's crucial to gauge the patient's emotional state and willingness to explore. We might ask questions that invite them to reflect on their feelings, but we also need to be attentive to their reactions and adjust accordingly. The goal is to foster a collaborative environment where the patient feels safe and supported in their exploration.\cf2 \'a0That's why I would ask if it is her will to explore first before exploring so we could develop a collaborative environment based on her will.\
\
\cf4 That's a thoughtful approach. Asking for the patient's will to explore can indeed reinforce the collaborative aspect of the therapy. In ISTDP, it's important to balance the need for exploration with the patient's readiness. You might phrase it like, 'Tamara, I'm curious if you feel ready to explore some of these feelings about work and home life, or do you prefer to focus on something else today?' This way, you're not only respecting her autonomy but also setting the stage for a deeper conversation if she's open to it. It's all about creating a space where the patient feels empowered to choose their path, while also being ready to support them when they express a willingness to go deeper. What do you think about this balance?\cf2 \'a0Yes. Another option might be, "You say it's just a phase, but you also say you are doubting your skills and feeling under a lot of stress. Before we explore what could be driving your stress, let me just check in with you, would you like us to explore what is causing your distress so we can help feel better?
}'''
        megan_denial_path = os.path.join(self.rtf_dir_nm, 'meganDenial.rtf')
        with open(megan_denial_path, 'w') as fd:
            fd.write(rtf1)
        tamara_denial_path = os.path.join(self.rtf_dir_nm, 'tamaraDenial.rtf')
        with open(tamara_denial_path, 'w') as fd:
            fd.write(rtf2)

        return (megan_denial_path, tamara_denial_path)

    #------------------------------------
    # mk_jsonl_reference_files
    #-------------------

    def mk_jsonl_reference_files(self):
        '''
        From the test RTF files created in mk_rtf_files(),
        create corresponding .jsonl files. Place them into
        directory self.jsonl_ref_dir_nm. File names will
        mirror the RTF files, with .rtf extension replaced
        by .jsonl

        Note: must be called after mk_rtf_files(), and assumes
              that self.jsonl_ref_dir_nm is an existing directory
              where the .jsonl files can be placed.
        '''
        jsonl_paths = []
        for rtf_path in [self.megan_rtf_file_nm, self.tamara_rtf_file_nm]:
            jsonl_objs = RTFParser(rtf_path, 
                                   self.tagmap, 
                                   collect_output=True).jsonl_objs
            rtf_pobj: Path = Path(rtf_path)
            jsonl_fn = rtf_pobj.with_suffix('.jsonl').name
            jsonl_dest = Path(self.jsonl_ref_dir_nm) / jsonl_fn
            jsonl_paths.append(jsonl_dest)
            with jsonlines.open(jsonl_dest, mode='w') as writer:
                for jsonl_obj in jsonl_objs:
                    writer.write(jsonl_obj)
        return jsonl_paths

    #------------------------------------
    # mk_reference_conversation
    #-------------------

    def mk_reference_conversation(self):
        '''
        Create a Discussion JSON structure that includes
        all of the Expert/AI discussions around both Megan
        and Tamara. Write it as a JSON structure into the 
        name discussion_all.json into the self.jsonl_ref_dir_nm 
        directory.

        @return path to the discussion_all.json file
        @rtype str
        '''    
        megan_dict = {
            'clientName'   : 'Megan',
            'defense'      : 'denial',
            'conversation' : []
        }
        tamara_dict = {
            'clientName'   : 'Tamara',
            'defense'      : 'denial',
            'conversation' : []
        }
        with jsonlines.open(self.megan_jsonl_ref_nm) as reader:
            megan_dict['conversation'] = list(reader)
        with jsonlines.open(self.tamara_jsonl_ref_nm) as reader:
            tamara_dict['conversation'] = list(reader)

        discussion = [megan_dict, tamara_dict]
        discussion_all_nm = str(Path(self.jsonl_ref_dir_nm) / 'discussion_all.json')
        with open(discussion_all_nm, 'w') as fd:
            json.dump(discussion,fd)
        return discussion_all_nm

    #------------------------------------
    # assertConversationsEqual
    #-------------------
    def assertConversationsEqual(self, conv1, conv2):
        '''
        Return True if two conversations are equal:
            o their 'clientName' values are the same
            o their 'defense'    values are the same
            o each of their conversation jsonl entries are the same

        :param conv1: _description_
        :type conv1: _type_
        :param conv2: _description_
        :type conv2: _type_
        '''
        self.assertEqual(conv1['clientName'], conv2['clientName'])
        self.assertEqual(conv1['defense'], conv2['defense'])
        turns1 = conv1['conversation']
        turns2 = conv2['conversation']
        self.assertEqual(len(turns1), len(turns2))
        for i in range(len(conv1['conversation'])):
            self.assertDictEqual(turns1[i], turns2[i])

    #------------------------------------
    # assertDiscussionsEqual
    #-------------------

    def assertDiscussionsEqual(self, disc1, disc2):
        '''
        Return True if two entire discussions are equal.
        Discussions are lists of conversations. 

        :param disc1: first discussion
        :type disc1: List[Conversation]
        :param disc2: discussion to compare against
        :type disc2: List[Conversation]
        '''
        for conv1, conv2 in zip(disc1, disc2):
            self.assertConversationsEqual(conv2, conv2)

# ------------------------ Main ------------

if __name__ == "__main__":
    unittest.main()
