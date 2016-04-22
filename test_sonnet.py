#Author: Russell Williams
#Email: ruwilliams@genedx.com

from nose.tools import *
import sonnet as snt
import random

vocab = snt.Vocab()
templates = snt.TemplateReader("line_templates.csv").read()

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

    def test_cap(self):
        a = snt.Line("test test test.")

        a.capitalize_first_word()

        eq_(a.text, "Test test test.")

    def test_lower_first_word(self):
        a = snt.Line("Test test Test.")
        b = snt.Line("I should stay capped.")

        a.lowercase_first_word()
        b.lowercase_first_word()

        eq_(a.text, "test test Test.")
        eq_(b.text, "I should stay capped.")

    def end_with_period(self):
        a = snt.Line("This one is easy")
        b = snt.Line("This needs to have the comma stripped,")

        a.end_with_period()
        b.end_with_period()

        eq_(a.text, "This one is easy.")
        eq_(b.text, "This needs to have the coomma stripped.")

class TestTemplate(object):
    def test_list_maker(self):
        nouns = vocab.common_words("NN")
        eq_(len(nouns), 994)
        ok_("time" in nouns)
        
    def test_blank_fill(self):
        a = snt.Blank("VB")
        a.common_pool = vocab.make_common_pool(a.pos_tag)

        w = a.fill()

        ok_(isinstance(w, unicode))
        ok_(w in snt.dictionary)
        ok_(w in vocab.common_tag_words["VB"])

    def test_template_populate(self):
        tags = ["VB", "VB", "NN", "VB"]
        blanks = [snt.Blank(tag) for tag in tags]
        a = snt.Template("Let's {} and {} some {} we can't {}.", blanks)
        a.make_pools(vocab)

        ok_(isinstance(a.populate(), snt.Line))

    def test_template_reader(self):
        t = templates
        ok_(isinstance(t, list))
        ok_(isinstance(t[0], snt.Template))
        ok_(not t[0].intro_required)
        eq_(t[10].intro_required, "NP")
        eq_(t[10].intro, "VP")

    def test_flex(self):
        ok_(templates[0].is_flexible())
        ok_(not templates[23].is_flexible())

    def test_polish(self):
        t = templates[0]
        t.filled_line = snt.Line("this should be capitalized and end in a period")
        t.sentence_start = True
        t.sentence_end = True

        t.polish()

        eq_(t.filled_line.text, "This should be capitalized and end in a period.")

class TestSonnetWriter(object):
    def setup(self):
        self.sw = snt.SonnetWriter(vocab = vocab)
        self.sw.template_pool = templates

    def teardown(self):
        self.sw.reset()

    def test_match_transitions(self):
        self.sw.lines = templates[:13]

        t1 = templates[0]
        #No transitions, should not be extended
        matched_t1 = self.sw.match_transitions(t1)
        eq_(len(matched_t1), 1)

        t2 = templates[10]
        #Needs intro, no outro
        matched_t2 = self.sw.match_transitions(t2)
        ok_(len(matched_t2) >= 2)
        eq_(matched_t2[-1], t2)
        #Should be last in the list since no outro will be added

    def test_pick_lines(self):
        self.sw.pick_lines()

        ok_(isinstance(self.sw.lines, list))
        ok_(isinstance(self.sw.lines[0], snt.Template))
        ok_(len(self.sw.lines), 14)
        ok_(isinstance(self.sw.line_groups, list))
        ok_(isinstance(self.sw.line_groups[0][0], snt.Template))
        eq_(sum([len(line_list) for line_list in self.sw.line_groups]), 14)

    def test_arrange_lines(self):
        self.sw.pick_lines()

        self.sw.arrange_lines()

        eq_(len(self.sw.sections), 4)
        for section in self.sw.sections[:2]:
            eq_(len(section.template_list), 4)
        eq_(len(self.sw.sections[-1].template_list), 2)

    def test_populate(self):
        self.sw.pick_lines()


        fail_count = 0
        give_up = False
        while not give_up: 
            try:
                self.sw.arrange_lines()
                self.sw.populate()
                break
            except (ConstructionFailure, PairFailure, RhymeFailure) as e:
                fail_count += 1
                logging.warning(e.msg)
                if fail_count > 5:
                    give_up = True

        for section in self.sw.sections:
            ok_(section.filled)
            for template in section.template_list:
                ok_(template.filled_line)

    def test_pick_hold_line(self):
        nonflex_t = templates[23]
        flex_t = templates[0]
        eq_(nonflex_t, self.sw.pick_hold_template([flex_t, nonflex_t]))
        eq_(nonflex_t, self.sw.pick_hold_template([nonflex_t, flex_t]))
        ok_(isinstance(self.sw.pick_hold_template([flex_t, templates[1]]), snt.Template))

    def test_rhyme_blank_switch(self):
        tp = [templates[0], templates[1]]

        self.sw.force_rhyme_cands(tp)

        #Make sure the last blank is correctly no longer a rhyme blank after
        #candidates have been generated
        for template in tp:
            ok_(isinstance(template.blanks[-1], snt.Blank))
            ok_(not isinstance(template.blanks[-1], snt.RhymeBlank))



class TestCollectionReader(object):
    def __init__(self):
        self.filename = "autumn_collection.csv"

    def test_read(self):
        cr = snt.CollectionReader(self.filename)
        collection = cr.read()
        ok_(isinstance(collection, list))
        ok_(isinstance(collection[0], tuple))
        eq_(("November", "NN"), collection[0])


class TestCollections(object):
    def test_add_collection(self):
        vocab.add_collection(vocab.collections["autumn"])
        ok_("November" in vocab.collection_pool["NN"])


class TestCollectionManager(object):
    def setup(self):
        self.cm = snt.CollectionManager()

    def test_cm(self):
        self.cm.read_all()

        ok_("autumn" in self.cm.collections)
        ok_(isinstance(self.cm.collections["autumn"], snt.Collection))
        ok_(self.cm.collections["autumn"].id, "autumn")

class TestVocab(object):
    def test_rhyming_words(self):
        rhymes = vocab.rhyming_words(snt.Word("mass"), "NN")
        ok_("class" in rhymes)
        ok_("glass" in rhymes)