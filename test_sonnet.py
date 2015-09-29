#Author: Russell Williams
#Email: ruwilliams@genedx.com

from nose.tools import *
import sonnet as snt
import random

listmaker = snt.CommonWordListMaker()
templates = snt.TemplateReader("line_templates.csv", listmaker).read()

class TestWord(object):
    def test_look_up(self):
        a = snt.Word("dog")
        a.look_up()
        ok_(not a.multi_prons)
        ok_(isinstance(a.pron, list))

        b = snt.Word("fire")
        b.look_up()
        ok_(b.multi_prons)
        ok_(isinstance(b.pron, list))

    def test_syl_count(self):
        a = snt.Word("dog")
        a.syl_count()
        ok_(not a.multi_syls)
        eq_(a.syllables, 1)

        b = snt.Word("fire")
        b.syl_count()
        ok_(b.multi_syls)
        ok_(1 in b.syllables)
        ok_(2 in b.syllables)

        c = snt.Word("illusion")
        c.syl_count()
        eq_(c.syllables, 3)

    def test_meter(self):
        a = snt.Word("dog")
        a.syl_count()
        eq_(a.syl_string, "x")

        b = snt.Word("fractal")
        b.syl_count()
        eq_(b.syl_string, "su")

        c = snt.Word("proprietary")
        c.syl_count()
        eq_(c.syl_string, "ususu")

    def test_last_sounds(self):
        a = snt.Word("dog")
        a.find_last_sounds()

        ok_(isinstance(a.last_sounds, list))
        eq_(a.last_sounds, [["AO", "G"]])

        b = snt.Word("frog")
        b.find_last_sounds()
        eq_(b.last_sounds, [["AA", "G"]])

        c = snt.Word("thirst")
        c.find_last_sounds()
        eq_(c.last_sounds, [["ER", "S", "T"]])

        d = snt.Word("go")
        d.find_last_sounds()
        eq_(d.last_sounds, [["OW"]])

        e = snt.Word("proprietary")
        e.find_last_sounds()
        eq_(e.last_sounds, [["EH", "R", "IY"]])


    def test_rhymes(self):
        #ok_(snt.Word("frog").rhymes_with(snt.Word("dog")))
        #Will need to put in some flexibility about slant rhymes
        #(At least slant according to the CMU, these just rhyme when I say them)
        #Do people really say "FRAHG" and not "FROWG"?
        ok_(snt.Word("dog").rhymes_with(snt.Word("log")))
        ok_(not snt.Word("frog").rhymes_with(snt.Word("fraud")))
        ok_(snt.Word("proprietary").rhymes_with(snt.Word("dairy")))

class TestLine(object):
    def test_make_word_list(self):
        a = snt.Line("dog fire radiant fractal")
        eq_(len(a.word_list), 4)
        ok_(isinstance(a.word_list[0], snt.Word))
        eq_(a.word_list[0].text, "dog")

        b = snt.Line("In October, I ate an apple.")
        eq_(len(b.word_list), 6)
        eq_(b.word_list[2].text, "i")

        c = snt.Line("He said, \"Of course.\"")
        eq_(len(c.word_list), 4)
        eq_(c.word_list[-1].text, "course")

        d = snt.Line("It doesn't work. He's angry.")
        eq_(len(d.word_list), 5)
        eq_(d.word_list[3].text, "he's")

    def test_make_syl_strings(self):
        a = snt.Line("Whose lips my lips have kissed, and how, and when")
        a.make_syl_strings()
        eq_(len(a.syl_strings), 1)
        eq_(len(a.syl_strings[0]), 10)

        b = snt.Line("fire radiant")
        #words with ambiguous number of syllables
        b.make_syl_strings()
        eq_(len(b.syl_strings), 4)
        ok_("xsu" in b.syl_strings)
        ok_("susuu" in b.syl_strings)

    def test_scans(self):
        a = snt.Line("test")
        a.syl_strings = ["xxxxxxxxxx"]
        ok_(a.scans())
        a.syl_strings = ["ususususus"]
        ok_(a.scans())
        a.syl_strings = ["usususus"]
        ok_(not a.scans())
        a.syl_strings = ["usuusususu"]
        ok_(not a.scans())
        a.syl_strings = ["usususus", "xxxxxxxxxx"]
        ok_(a.scans())

        b = snt.Line("Whose lips my lips have kissed, and how, and when")
        ok_(b.scans())

        c = snt.Line("When I consider how my light is spent")
        ok_(c.scans())

        d = snt.Line("that alters when it alteration finds")
        ok_(d.scans())

        e = snt.Line("If we shadows have offended, think but")
        #10 syllables, trochaic
        ok_(not e.scans())

        f = snt.Line("that alters when it bananas finds")
        ok_(not f.scans())

class TestTemplate(object):
    def test_list_maker(self):
        nouns = listmaker.common_words("NN")
        eq_(len(nouns), 398)
        ok_("time" in nouns)
        
    def test_blank_fill(self):
        random.seed(1)
        a = snt.Blank("VB", listmaker)
        eq_(a.fill(), "continue")

    def test_template_populate(self):
        tags = ["VB", "VB", "NN", "VB"]
        blanks = [snt.Blank(tag, listmaker) for tag in tags]
        a = snt.Template("Let's {} and {} some {} we can't {}.", blanks)
        ok_(isinstance(a.populate(), snt.Line))

    def test_template_reader(self):
        t = templates
        ok_(isinstance(t, list))
        ok_(isinstance(t[0], snt.Template))
        ok_(not t[0].intro_required)
        ok_(not t[0].intro)
        eq_(t[10].intro_required, "NP")
        eq_(t[10].intro, "VP")

class TestSonnetWriter(object):
    def test_match_transitions(self):
        sw = snt.SonnetWriter()
        t1 = templates[0]
        #No transitions, should not be extended
        matched_t1 = sw.match_transitions(t1, templates)
        eq_(len(matched_t1), 1)

        t2 = templates[10]
        #Needs intro, no outro
        matched_t2 = sw.match_transitions(t2, templates)
        eq_(len(matched_t2), 2)
        eq_(matched_t2[-1], t2)
        #Should be last in the list since no outro will be added

    def test_pick_lines(self):
        sw = snt.SonnetWriter()
        sw.pick_lines(templates)
        #Should return a list of lists of templates, with 14 total templates
        ok_(isinstance(sw.lines, list))
        ok_(isinstance(sw.lines[0], list))
        ok_(isinstance(sw.lines[0][0], snt.Template))
        eq_(sum([len(line_list) for line_list in sw.lines]), 14)

    def test_arrange_lines(self):
        sw = snt.SonnetWriter()
        sw.pick_lines(templates)
        sw.arrange_lines()
        eq_(len(sw.couplet), 2)
        eq_(len(sw.quatrains), 3)
        for quatrain in sw.quatrains:
            eq_(len(quatrain), 4)
            ok_(not quatrain[0].intro_required)
            ok_(not quatrain[-1].outro_required)

    def test_populate(self):
        sw = snt.SonnetWriter()
        sw.pick_lines(templates)
        sw.arrange_lines()
        sw.populate()
        eq_(len(sw.filled_sonnet), 14)

