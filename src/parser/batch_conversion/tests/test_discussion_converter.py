 # **********************************************************
 #
 # @Author: Andreas Paepcke
 # @Date:   2025-07-09 13:03:22
 # @File:   /Users/paepcke/VSCodeWorkspaces/rtf-text-color-parser/src/parser/batch_conversion/tests/test_discussion_converter.py
 # @Last Modified by:   Andreas Paepcke
 # @Last Modified time: 2025-07-09 14:11:22
 #
 # **********************************************************

import os
import tempfile
import unittest

from parser.batch_conversion.discussion_converter import DiscussionConverter

class DiscussionConverterTester(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        self.tst_dir = tempfile.TemporaryDirectory(dir= '/tmp', prefix='convert_test')
        self.rtf_dir_nm = os.path.join(self.tst_dir.name, 'RtfDir')
        self.rtf_dir  = os.mkdir(self.rtf_dir_nm)
        self.jsonl_dir_nm = os.path.join(self.tst_dir.name, 'JsonlDir')
        self.jsonlDir = os.mkdir(self.jsonl_dir_nm)

        # Create RTF test files
        (self.megan_file_nm, self.tamara_file_nm) = self.mk_rtf_files()
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
        client_name, defense = self.converter.parse_fname(self.megan_file_nm)
        self.assertEqual(client_name, 'Megan')
        self.assertEqual(defense, 'denial')

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


# ------------------------ Main ------------

if __name__ == "__main__":
    unittest.main()
