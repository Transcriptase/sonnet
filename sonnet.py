#Author: Russell Williams
#Email: russell.d.williams@gmail.com

#Attempt at automated sonnet generation

import nltk
import logging
import re
import random
import csv

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

dictionary = nltk.corpus.cmudict.dict()
#Import the CMU Pronouncing Dictionary as a dictionary

syllable_marks = re.compile("0|1|2")
stressed_syllable_marks = re.compile("1|2")
#Create the regular expression recognizing CMU syllable stress marks

class Word(object):
    """A word: a poem's elemental cell.
    Count syllables. Find stresses. Do it well."""
    def __init__(self, text):
        super(Word, self).__init__()
        self.text = text.lower()
        self.look_up()
        self.syl_count()

    def look_up(self):
        try:
            pronunciations = dictionary[self.text]
        except KeyError:
            logging.debug("Word \'{}\' not found in CMU dictionary.".format(self.text))
            return
        if len(pronunciations) > 1:
            self.multi_prons = True
            self.pron = pronunciations
        else:
            self.multi_prons = False
            self.pron = pronunciations[0]

    def make_syl_string(self, pron):
        syl_string = []
        for symbol in pron:
            if "0" in symbol:
                syl_string.append(0)
            elif "1" in symbol:
                syl_string.append(1)
            elif "2" in symbol:
                syl_string.append(2)
        return self.stresses(syl_string)

    def syl_count(self):
        self.multi_syls = False
        if not self.multi_prons:
            self.syl_string = self.make_syl_string(self.pron)
            self.syllables = len(self.syl_string)
        else:
            syl_strings = [self.make_syl_string(pron) for pron in self.pron]
            for syl_string in syl_strings:
                if syl_string != syl_strings[0]:
                    self.multi_syls = True
            if not self.multi_syls:
                self.syl_string = syl_strings[0]
                self.syllables = len(self.syl_string)
            else:
                self.syl_string = list(set(syl_strings))
                self.syllables = [len(syl_string) for syl_string in self.syl_string]

    def stresses(self, syl_string):
        stresses = []
        if len(syl_string) == 1:
            stresses.append("x")
        else:
            for syl in syl_string:
                if syl > 0:
                    stresses.append("s")
                else:
                    stresses.append("u")
        return "".join(stresses)

    def last_sound(self, pron):
        for index, sound in enumerate(reversed(pron)):
            if stressed_syllable_marks.search(sound):
                return [sound.strip("012") for sound in pron[-(index +1):]]

    def find_last_sounds(self):
        self.last_sounds = []
        if not self.multi_prons:
            self.last_sounds.append(self.last_sound(self.pron))
        else:
            self.last_sounds = [self.last_sound(pron) for pron in self.pron]

    def rhymes_with(self, other_word):
        if other_word.text == self.text:
            return False
        #Prevent "rhyming" the same word.
        self.find_last_sounds()
        other_word.find_last_sounds()
        for sound in other_word.last_sounds:
            if sound in self.last_sounds:
                return True
        return False


class Line(object):
    """Does it scan? Does it rhyme? A line's
    what happens when some Words combine."""
    def __init__(self, text):
        self.text = text
        self.make_word_list()
        self.make_syl_strings()

    def make_word_list(self):
        word_list = nltk.word_tokenize(self.text)
        #Combine contractions
        contractions = ["n't", "'s", "'m", "'re"]
        for contraction in contractions:
            while contraction in word_list:
                cont_index = word_list.index(contraction)
                word_list[cont_index -1] = "".join([word_list[cont_index-1], contraction])
                word_list.pop(cont_index)
        strippable_punc = [".", ",", ":", "(", ")", ";", "?", "!", "\"", "", "''", "``"]
        word_list = [word for word in word_list if word not in strippable_punc]
        self.word_list = [Word(word) for word in word_list]

    def make_syl_strings(self):
        syl_strings = [[]]
        for word in self.word_list:
            if not word.multi_syls:
                for line_string in syl_strings:
                    line_string.append(word.syl_string)
            else:
                new_syl_strings = []
                for line_string in syl_strings:
                    for word_string in word.syl_string:
                        new_syl_strings.append(line_string + [word_string])
                syl_strings = new_syl_strings
            #For each possible pronunciation, create a syllable string
            #with that pronunciation added to the end
        joined_strings = ["".join(string) for string in syl_strings]
        self.syl_strings = joined_strings

    def too_short(self):
        for syl_string in self.syl_strings:
            if len(syl_string) >= 10:
                return False
        return True

    def scans(self):
        results = []
        for syl_string in self.syl_strings:
            result = True
            if not len(syl_string) == 10:
                result = False
            else:
                for position, char in enumerate(syl_string):
                    if position % 2 == 0:
                        if char == "s":
                            result =  False
                    else:
                        if char == "u":
                            result = False
            results.append(result)
        if True in results:
            return True
        else:
            return False

    def rhymes_with(self, other_line):
        if self.word_list[-1].rhymes_with(other_line.word_list[-1]):
            return True
        else:
            return False


class Template(object):
    """A Template for a Line we hope to fill
    with some convincing fakery of skill."""
    def __init__(self, raw_text, blanks, intro_required = False, outro_required = False, intro = False, outro = False):
        self.raw_text = raw_text
        self.blanks = blanks
        self.intro = intro
        self.outro = outro
        self.intro_required = intro_required
        self.outro_required = outro_required

    def populate(self):
        choices = ["" for blank in self.blanks]
        unfilled_optionals = [blank for blank in self.blanks if blank.optional]
        for index, blank in enumerate(self.blanks):
            if not blank.optional:
                choices[index] = blank.fill()
        candidate = Line(self.raw_text.format(*choices))
        while candidate.too_short() and unfilled_optionals:
            next_optional_blank = random.choice(unfilled_optionals)
            unfilled_optionals.remove(next_optional_blank)
            optional_word = "{} ".format(next_optional_blank.fill())
            #Needed to insert space between optional word and next word.
            choices[self.blanks.index(next_optional_blank)] = optional_word
            candidate = Line(self.raw_text.format(*choices))
        return candidate



    def make_scanning_line(self, attempts = 50):
        finished = False
        give_up = False
        fail_count = 0
        while not finished and not give_up:
            candidate = self.populate()
            if candidate.scans():
                return candidate
            else:
                fail_count += 1
            if fail_count >= attempts:
                give_up = True
                logging.warning("No scanning completions found for template: {}".format(self.raw_text))

    def make_candidates(self, depth = 20):
        self.candidates = [self.make_scanning_line() for ii in xrange(depth)]

    def more_candidates(self, depth = 10):
        self.candidates.extend([self.make_scanning_line() for ii in xrange(depth)])

class TemplateReader(object):
    """Pulls Templates from a file"""
    def __init__(self, filename, list_maker):
        self.filename = filename
        self.list_maker = list_maker

    def read(self):
        templates = []
        with open(self.filename, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tags = row["pos_tags"].split()
                optional_flags = row["optional"].split()
                intro = self.translate_tags(row["intro"])
                outro = self.translate_tags(row["outro"])
                intro_required = self.translate_tags(row["intro_required"])
                outro_required = self.translate_tags(row["outro_required"])
                blanks = [Blank(tag, self.list_maker, optional = (opt_flag == "T")) for tag, opt_flag in zip(tags, optional_flags)]
                templates.append(Template(row["raw_text"], blanks, intro = intro, outro = outro, intro_required = intro_required, outro_required = outro_required))
        return templates

    def translate_tags(self, tag):
        if tag == "F":
            return False
        else:
            return tag

        


class Blank(object):
    """docstring for Blank"""
    def __init__(self, pos_tag, pool_maker, optional = False):
        super(Blank, self).__init__()
        self.pos_tag = pos_tag
        self.optional = optional
        self.pool_maker = pool_maker
        self.make_pool()

    def make_pool(self):
        self.pool = self.pool_maker.common_words(self.pos_tag)

    def fill(self):
        return random.choice(self.pool)

class SonnetWriter(object):
    """docstring for SonnetWriter"""
    def __init__(self):
      self.lines = []
      self.quatrains = []
      self.couplet = []

    def pick_lines(self, templates):
        self.lines = []
        lines_added = 0
        while lines_added < 14:
            new_template = random.choice(templates)
            new_lines = self.match_transitions(new_template, templates)
            if new_lines:
                if lines_added + len(new_lines) <= 14:
                    self.lines.append(new_lines)
                    lines_added += len(new_lines)
                    templates = [template for template in templates if template not in new_lines]
                    #remove used templates from pool

    def match_transitions(self, start_template, all_templates):
        complete_sentence = [start_template]
        while complete_sentence[0].intro_required:
            candidates = [template for template in all_templates if template.outro == complete_sentence[0].intro_required]
            try:
                intro = random.choice(candidates)
                complete_sentence.insert(0, intro)
            except IndexError:
                logging.warning("No {} match found for template: {}".format(start_template.intro_required, start_template.raw_text))
                return False
        while complete_sentence[-1].outro_required:
            candidates = [template for template in all_templates if template.intro == complete_sentence[-1].outro_required]
            try:
                outro = random.choice(candidates)
                complete_sentence.append(outro)
            except IndexError:
                logging.warning("No {} match found for template: {}".format(start_template.outro_required, start_template.raw_text))
                return false
        return complete_sentence

    def arrange_lines(self):
        self.quatrains = []
        self.couplet = []
        while len(self.couplet) < 2:
            couplet_candidate = random.choice(self.lines)
            if len(self.couplet) + len(couplet_candidate) <= 2:
                self.couplet.extend(couplet_candidate)
                self.lines.remove(couplet_candidate)
        for ii in xrange(3):
            new_quatrain = []
            while len(new_quatrain) < 4:
                quatrain_candidate = random.choice(self.lines)
                if len(new_quatrain) + len(quatrain_candidate) <= 4:
                    new_quatrain.extend(quatrain_candidate)
                    self.lines.remove(quatrain_candidate)
            self.quatrains.append(new_quatrain)

    def pick_rhymes(self, line1, line2, retries = 5):
        finished = False
        give_up = False
        fail_count = 0
        line1.make_candidates()
        line2.make_candidates()
        while not finished and not give_up:
            for candidate1 in line1.candidates:
                for candidate2 in line2.candidates:
                    if candidate1.rhymes_with(candidate2):
                        return (candidate1, candidate2)
                        finished = True
            fail_count += 1
            line1.more_candidates()
            line2.more_candidates()
            if fail_count >= retries:
                give_up = True
                logging.warning("No rhymes found for lines:\n {}\n {}".format(line1.raw_text, line2.raw_text))

    def populate(self):
        self.filled_sonnet = []
        for quatrain in self.quatrains:
            filled_quat = ["unfilled line" for line in quatrain]
            filled_quat[0], filled_quat[2] = self.pick_rhymes(quatrain[0], quatrain[2])
            filled_quat[1], filled_quat[3] = self.pick_rhymes(quatrain[1], quatrain[3])
            self.filled_sonnet.extend(filled_quat)
        filled_couplet = ["unfilled line" for line in self.couplet]
        filled_couplet[0], filled_couplet[1] = self.pick_rhymes(self.couplet[0], self.couplet[1])
        self.filled_sonnet.extend(filled_couplet)

    def display(self):
        for line in self.filled_sonnet:
            print line.text

class CommonWordListMaker(object):
    '''Processes the Brown corpus to find the most common
    words for each part of speech, and stores the results so
    the slow lookup only happens once.'''
    def __init__(self, depth = 400):
        self.corpus = nltk.corpus.brown.tagged_words()
        self.cfd = nltk.ConditionalFreqDist((tag, word) for word, tag in self.corpus)
        self.depth = depth
        self.common_tag_words = {}

    def find_common_words(self, tag):
        return [word for word, count in self.cfd[tag].most_common(self.depth)]

    def common_words(self, tag):
        if tag not in self.common_tag_words.keys():
            self.common_tag_words[tag] = [word for word in self.find_common_words(tag) if word.lower() in dictionary.keys()]
        return self.common_tag_words[tag]
        
class CoupletMaker(object):
    def __init__(self, templates):
        self.all_templates = templates

    def generate(self):
        self.templates = random.sample(self.all_templates, 2)
        for template in self.templates:
            template.make_candidates()
        self.couplet = self.pick_rhymes(self.templates[0], self.templates[1])

    def pick_rhymes(self, line1, line2, retries = 3):
        finished = False
        give_up = False
        fail_count = 0
        retries = 3
        while not finished and not give_up:
            for candidate1 in line1.candidates:
                for candidate2 in line2.candidates:
                    if candidate1.rhymes_with(candidate2):
                        return [candidate1, candidate2]
                        finished = True
            fail_count += 1
            line1.more_candidates()
            line2.more_candidates()
            if fail_count >= retries:
                give_up = True

if __name__ == '__main__':
    vocab = CommonWordListMaker()
    reader = TemplateReader("line_templates.csv", vocab)
    templates = reader.read()
    cm = CoupletMaker(templates)
    finished = False
    while not finished:
        cm.generate()
        for line in cm.couplet:
            print line.text
        another = raw_input("Another couplet? (Y/N)")
        if another != "y":
            finished = True


