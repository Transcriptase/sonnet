# Author: Russell Williams
# Email: russell.d.williams@gmail.com
# Copyright 2016

# Attempt at automated sonnet generation

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import nltk
import logging
import re
import random
import csv
import glob
from itertools import tee, islice, chain, izip

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import the CMU Pronouncing Dictionary as a dictionary
logging.info("Loading dictionary...")
dictionary = nltk.corpus.cmudict.dict()
logging.info("Done.")

syllable_marks = re.compile("0|1|2")
stressed_syllable_marks = re.compile("1|2")


# Create the regular expression recognizing CMU syllable stress marks

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
            self.not_in_dict = True
            logging.warning("Word \'{}\' not found in CMU dictionary.".format(self.text))
            return
        self.not_in_dict = False
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
                return [sound.strip("012") for sound in pron[-(index + 1):]]

    def find_last_sounds(self):
        self.last_sounds = []
        if not self.multi_prons:
            self.last_sounds.append(self.last_sound(self.pron))
        else:
            self.last_sounds = [self.last_sound(pron) for pron in self.pron if self.last_sound(pron) is not None]
            # Some words have totally unstressed pronounciations, which leads them returning "None" for last sound
            # Then, if you get two, you get incorrect rhymes as None matches None.
            # Have to filter them out.

    def rhymes_with(self, other_word):
        if other_word.text == self.text:
            return False
        # Prevent "rhyming" the same word.
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
        self.choices = []

    def __repr__(self):
        return "Line({})".format(self.text)

    def make_word_list(self):
        word_list = nltk.word_tokenize(self.text)
        # Combine contractions
        contractions = ["n't", "'s", "'m", "'re", "'ll"]
        for contraction in contractions:
            while contraction in word_list:
                cont_index = word_list.index(contraction)
                word_list[cont_index - 1] = "".join([word_list[cont_index - 1], contraction])
                word_list.pop(cont_index)
        strippable_punc = [".", ",", ":", "(", ")", ";", "?", "!", "\"", "", "''", "``", "'"]
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
                # For each possible pronunciation, create a syllable string
                # with that pronunciation added to the end
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
                            result = False
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

    def same_choices(self, other_line):
        for choice in self.choices:
            if choice in other_line.choices and choice != "":
                return True
        return False

    def capitalize_first_word(self):
        words = self.text.split()
        words[0] = words[0].capitalize()
        self.text = " ".join(words)

    def lowercase_first_word(self):
        words = self.text.split()
        if words[0] != "I":
            words[0] = words[0].lower()
        self.text = " ".join(words)

    def end_with_period(self):
        self.text = self.text.rstrip(",")
        self.text = "".join([self.text, "."])

    def no_repeated_choices(self):
        seen = set()
        for choice in self.choices:
            if choice != "" and choice in seen:
                return False
            seen.add(choice)
        return True

    def change_a_to_an(self):
        all_words = self.text.split(" ")
        previous_words, words, next_words = tee(all_words, 3)
        next_words = chain(islice(next_words, 1, None), [None])
        linked_words = izip(words, next_words)
        vowels = ["a", "e", "i", "o", "u"]
        for index, (word, next_word) in enumerate(linked_words):
            for original, altered in zip(["A", "a"], ["An", "an"]):
                if word == original:
                    for vowel in vowels:
                        if next_word.startswith(vowel) or next_word.startswith(vowel.upper()):
                            all_words[index] = altered
                            self.text = " ".join(all_words)


class Template(object):
    """A Template for a Line we hope to fill
    with some convincing fakery of skill."""

    def __init__(self, raw_text, blanks, intro_required=False, outro_required=False, intro=False, outro=False):
        self.raw_text = raw_text
        self.blanks = blanks
        self.intro = intro
        self.outro = outro
        self.intro_required = intro_required
        self.outro_required = outro_required
        self.filled_line = None
        self.sentence_start = False
        self.sentence_end = False

    def __repr__(self):
        return "Template({})".format(self.raw_text)

    def populate(self):
        choices = ["" for _ in self.blanks]
        unfilled_optionals = [blank for blank in self.blanks if blank.optional]
        for index, blank in enumerate(self.blanks):
            if not blank.optional:
                choices[index] = blank.fill()
        candidate = self.make_line(choices)
        while candidate.too_short() and unfilled_optionals:
            next_optional_blank = random.choice(unfilled_optionals)
            unfilled_optionals.remove(next_optional_blank)
            optional_word = "{} ".format(next_optional_blank.fill())
            # Needed to insert space between optional word and next word.
            choices[self.blanks.index(next_optional_blank)] = optional_word
            candidate = self.make_line(choices)
        return candidate

    def make_line(self, choices):
        line = Line(self.raw_text.format(*choices))
        line.choices = choices
        return line

    def make_scanning_line(self, attempts=10000):
        finished = False
        fail_count = 0
        while not finished:
            candidate = self.populate()
            if candidate.scans() and candidate.no_repeated_choices():
                return candidate
            else:
                fail_count += 1
            if fail_count >= attempts:
                msg = "No scanning completions found for template: {}".format(self.raw_text)
                raise ScanFailure(self, msg)

    def make_candidates(self, depth=20):
        self.candidates = [self.make_scanning_line() for _ in xrange(depth)]

    def convert_to_rhyme(self, words):
        self.blanks[-1] = RhymeBlank(self.blanks[-1].pos_tag, words, self.blanks[-1].optional)

    def restore_from_rhyme(self):
        self.blanks[-1] = Blank(self.blanks[-1].pos_tag, self.blanks[-1].optional)

    def is_flexible(self):
        return not any(c.isalpha() for c in self.raw_text.split("{}")[-1])
        # Convoluted, but checks to see if there is a word after the last blank
        # (Split on the blanks, grab the last section, see if there are any letters in it)

    def last_words(self):
        last_words = set([cand.word_list[-1].text for cand in self.candidates])
        last_words = [Word(text) for text in last_words]
        return last_words

    def make_pools(self, vocab):
        for blank in self.blanks:
            blank.make_pools(vocab)

    def polish(self):
        self.filled_line.change_a_to_an()
        if self.sentence_start:
            self.filled_line.capitalize_first_word()
        sentence_ending_punc = [".", "?", "!"]
        last_char = self.filled_line.text[-1]
        if self.sentence_end and last_char not in sentence_ending_punc:
            self.filled_line.end_with_period()

    def cleanup(self):
        self.candidates = []
        self.filled_line = None
        self.sentence_start = False
        self.sentence_end = False


class TemplateReader(object):
    """Pulls Templates from a file"""

    def __init__(self, filename):
        self.filename = filename

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
                blanks = [Blank(tag, optional=(opt_flag == "T")) for tag, opt_flag in zip(tags, optional_flags)]
                templates.append(
                    Template(row["raw_text"], blanks, intro=intro, outro=outro, intro_required=intro_required,
                             outro_required=outro_required))
        return templates

    def translate_tags(self, tag):
        if tag == "F":
            return False
        else:
            return tag


class Blank(object):
    """docstring for Blank"""

    def __init__(self, pos_tag, optional=False, collection_prob=0.7):
        self.pos_tag = pos_tag
        self.optional = optional
        self.collection_pool = []
        self.collection_prob = collection_prob

    def fill(self):
        if self.collection_pool:
            use_collection = random.random()
            if use_collection < self.collection_prob:
                return random.choice(self.collection_pool)
        return random.choice(self.common_pool)

    def make_pools(self, vocab):
        self.common_pool = vocab.make_common_pool(self.pos_tag)
        self.collection_pool = vocab.make_collection_pool(self.pos_tag)


class RhymeBlank(Blank):
    def __init__(self, pos_tag, words, optional=False):
        super(RhymeBlank, self).__init__(pos_tag, optional)
        self.words = words
        self.rhyme_pool = []

    def fill(self):
        return random.choice(self.rhyme_pool)

    def make_pools(self, vocab):
        self.rhyme_pool = vocab.make_rhyme_pool(self.words, self.pos_tag)
        if not self.rhyme_pool:
            msg = "Unable to find rhymes in {} for {}".format(self.pos_tag, [word.text for word in self.words])
            raise RhymeFailure(self, msg)


class CollectionReader(object):
    def __init__(self, coll_file):
        self.coll_file = coll_file

    def read(self):
        tagged_words = []
        with open(self.coll_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                word = row["word"]
                pos_tag = row["pos_tag"]
                pron = row["pron"]
                tagged_words.append((word, pos_tag))
                if pron:
                    dictionary[word.lower()] = [pron]
        return tagged_words


class Collection(object):
    def __init__(self, tagged_words):
        self.tagged_words = tagged_words
        self.id = None

    def check(self):
        for word, pos_tag in self.tagged_words:
            if word.lower() not in dictionary:
                print ("{} not found in CMU dict. Enter custom pronunciation in file.".format(word))


class CollectionManager(object):
    def __init__(self):
        self.collections = {}
        self.coll_pattern = "_collection.csv"

    def coll_file_list(self):
        return glob.glob("".join(["*", self.coll_pattern]))

    def read_all(self):
        for filename in self.coll_file_list():
            reader = CollectionReader(filename)
            collection = Collection(reader.read())
            collection.id = filename.split(self.coll_pattern)[0]
            collection.check()
            self.collections[collection.id] = collection


class Vocab(object):
    """Processes the Brown corpus to find the most common
    words for each part of speech, and stores the results so
    the slow lookup only happens once."""

    def __init__(self, common_depth=1000, uncommon_depth=20000):
        logging.info("Initializing vocabulary...")
        logging.info("Loading Brown corpus...")
        self.corpus = nltk.corpus.brown.tagged_words()
        logging.info("Done.")
        logging.info("Making frequency distribution...")
        self.cfd = nltk.ConditionalFreqDist((tag, word) for word, tag in self.corpus)
        logging.info("Done.")
        logging.info("Loading collections...")
        cm = CollectionManager()
        cm.read_all()
        self.collections = cm.collections
        logging.info("Done")

        self.common_depth = common_depth
        self.uncommon_depth = uncommon_depth
        self.common_tag_words = {}
        self.collection_pool = {}
        self.uncommon_tag_words = {}
        self.used = []
        self.blacklist = ["TV", "Q", "C", "UN", "n", "A", "T", "queers", "faggot", "faggots", "nigger", "niggers",
                          "gay"]
        # Words in the dictionary that I don't want to use,
        # Unnatural sounding or... well.

    def find_common_words(self, tag, depth):
        logging.debug("Initializing {} to depth {}...".format(tag, depth))
        word_list = [word for word, count in self.cfd[tag].most_common(depth)]
        return self.wordlist_filter(word_list)

    def wordlist_filter(self, word_list):
        def word_filter(word):
            in_dict = word.lower() in dictionary
            unneeded_cap = word[0].isupper() and word.lower() in word_list
            on_blacklist = word in self.blacklist
            return in_dict and word.isalpha() and not unneeded_cap and not on_blacklist

        return [word for word in word_list if word_filter(word)]

    def common_words(self, tag):
        if tag not in self.common_tag_words.keys():
            self.common_tag_words[tag] = self.find_common_words(tag, self.common_depth)
            logging.debug("{} initialized.".format(tag))
        return self.common_tag_words[tag]

    def collection_words(self, tag):
        if tag not in self.collection_pool:
            self.collection_pool[tag] = []
        return self.collection_pool[tag]

    def add_collection(self, collection_id):
        if collection_id not in self.collections:
            logging.warning("Collection not found: {}".format(collection_id))
        else:
            collection = self.collections[collection_id]
            for word, pos_tag in collection.tagged_words:
                if pos_tag not in self.collection_pool:
                    self.collection_pool[pos_tag] = []
                self.collection_pool[pos_tag].append(word)

    def clear_collections(self):
        self.collection_pool = {}

    def rhyming_words(self, source_word, pos_tag):
        rhymes = [word for word in self.common_words(pos_tag) if source_word.rhymes_with(Word(word))]
        if not rhymes:
            logging.debug("No common rhymes found for \'{}\' in {}".format(source_word.text, pos_tag))
            rhymes = [word for word in self.uncommon_words(pos_tag) if source_word.rhymes_with(Word(word))]
            if not rhymes:
                logging.debug("No uncommon rhymes found for \'{}\' in {}".format(source_word.text, pos_tag))
        return rhymes

    def uncommon_words(self, tag):
        if tag not in self.uncommon_tag_words.keys():
            self.uncommon_tag_words[tag] = self.find_common_words(tag, self.uncommon_depth)
            logging.debug("{} initialized.".format(tag))
        return self.uncommon_tag_words[tag]

    def make_common_pool(self, tag):
        return self.not_used(self.common_words(tag))

    def make_collection_pool(self, tag):
        return self.not_used(self.collection_words(tag))

    def make_rhyme_pool(self, source_words, tag):
        rhyme_pool = []
        for source_word in source_words:
            rhyme_pool.extend(self.not_used(self.rhyming_words(source_word, tag)))
        return rhyme_pool

    def not_used(self, word_list):
        return [word for word in word_list if word not in self.used]

    def add_random_collections(self, number=2):
        coll_ids = random.sample(self.collections.keys(), number)
        for coll_id in coll_ids:
            self.add_collection(coll_id)


class SonnetWriter(object):
    """docstring for SonnetWriter"""

    def __init__(self, vocab):
        self.vocab = vocab
        self.lines, self.line_groups = [], []

    def load_templates(self, filename):
        self.template_pool = TemplateReader(filename).read()

    def pick_lines(self):
        while len(self.lines) < sum(self.current_poem.section_lengths):
            available_templates = [template for template in self.template_pool if template not in self.lines]
            new_template = random.choice(available_templates)
            new_lines = self.match_transitions(new_template)
            if new_lines:
                if len(self.lines) + len(new_lines) <= sum(self.current_poem.section_lengths):
                    self.add_lines(new_lines)

    def add_lines(self, lines):
        self.lines.extend(lines)
        self.line_groups.append(lines)
        lines[0].sentence_start = True
        lines[-1].sentence_end = True

    def match_transitions(self, start_template):
        complete_sentence = [start_template]
        while complete_sentence[0].intro_required:
            candidates = [template for template in self.template_pool if template.outro == complete_sentence[
                0].intro_required and template not in self.lines and template not in complete_sentence]
            try:
                intro = random.choice(candidates)
                complete_sentence.insert(0, intro)
            except IndexError:
                logging.warning(
                    "No {} match found for template: {}".format(start_template.intro_required, start_template.raw_text))
                return False
        while complete_sentence[-1].outro_required:
            candidates = [template for template in self.template_pool if template.intro == complete_sentence[
                -1].outro_required and template not in self.lines and template not in complete_sentence]
            try:
                outro = random.choice(candidates)
                complete_sentence.append(outro)
            except IndexError:
                logging.warning(
                    "No {} match found for template: {}".format(start_template.outro_required, start_template.raw_text))
                return False
        return complete_sentence

    def force_line(self, template):
    # Used to force inclusion of a particular template, for building sample size.
        new_lines = self.match_transitions(template)
        if new_lines and len(self.lines) + len(new_lines) <= sum(self.current_poem.section_lengths):
            self.add_lines(new_lines)


    def arrange_lines(self):
        for section in sorted(self.current_poem.sections, key= lambda x: len(x.template_list)):
            # Go smallest to largest because small sections are more restrictive
            fail_count = 0
            new_section = []
            while len(new_section) < len(section.template_list):
                candidate = random.choice(self.line_groups)
                if len(new_section) + len(candidate) <= len(section.template_list):
                    new_section.extend(candidate)
                    self.line_groups.remove(candidate)
                else:
                    fail_count += 1
                if fail_count >= 20:
                    msg = "Unable to fill section of length {} from remaining templates.".format(len(section.template_list))
                    raise ConstructionFailure(self.line_groups, msg)
            section.template_list = new_section

    def pick_rhymes(self, template_pair, retries=5):
        fail_count = 0
        logging.debug(
            "Finding rhymes for templates:\n{}\n{}".format(template_pair[0].raw_text, template_pair[1].raw_text))
        while True:
            self.force_rhyme_cands(template_pair)
            rhymes = self.select_rhyming_candidates(template_pair)
            if rhymes:
                for template, rhyming_line in zip(template_pair, random.choice(rhymes)):
                    template.filled_line = rhyming_line
                    self.vocab.used.extend(rhyming_line.choices)
                return
            else:
                fail_count += 1
            if fail_count >= retries:
                msg = "No rhymes found for lines:\n {}\n {}".format(template_pair[0].raw_text,
                                                                    template_pair[1].raw_text)
                raise PairFailure(template_pair, msg)

    def select_rhyming_candidates(self, template_pair):
        rhyme_pairs = []
        for candidate1 in template_pair[0].candidates:
            for candidate2 in template_pair[1].candidates:
                if candidate1.rhymes_with(candidate2) and not candidate1.same_choices(candidate2):
                    rhyme_pairs.append([candidate1, candidate2])
        return rhyme_pairs

    def pick_hold_template(self, template_pair):
        nonflexible = [template for template in template_pair if not template.is_flexible()]
        if len(nonflexible) > 1:
            msg = "Template pair cannot be matched:\n{}\n{}".format(template_pair[0].raw_text,
                                                                    template_pair[1].raw_text)
            raise PairFailure(template_pair, msg)
        if len(nonflexible) == 1:
            return nonflexible[0]
        else:
            return random.choice(template_pair)

    def force_rhyme_cands(self, template_pair):
        hold_line = self.pick_hold_template(template_pair)
        reach_line = template_pair[template_pair.index(hold_line) - 1]
        # Slightly magic: if hold_line is [0], then -1 gets you [1]
        # If hold_line is [1], -1 gets you [0]
        hold_line.make_pools(self.vocab)
        hold_line.make_candidates()
        reach_line.convert_to_rhyme(hold_line.last_words())
        try:
            reach_line.make_pools(self.vocab)
            reach_line.make_candidates()
        except RhymeFailure as e:
            logging.warning(e.msg)
            return
        finally:
            reach_line.restore_from_rhyme()

    def set_coll_prob(self, coll_prob):
        for template in self.template_pool:
            for blank in template.blanks:
                blank.collection_prob = coll_prob

    def populate(self):
        while self.current_poem.unfilled_sections():
            next_section = random.choice(self.current_poem.unfilled_sections())
            for template_pair in next_section.template_pairs():
                self.pick_rhymes(template_pair)
            next_section.filled = True

    def reset(self):
        logging.info("Resetting...")
        self.lines = []
        self.current_poem.reset()
        self.vocab.used = []
        for template in self.template_pool:
            template.cleanup()

    def new_poem(self, poem):
        self.current_poem = poem
        successful = False
        while not successful:
            self.reset()
            try:
                self.pick_lines()
                self.arrange_lines()
                self.populate()
                successful = True
            except (ConstructionFailure, PairFailure, ScanFailure) as e:
                logging.warning(e.msg)
        self.current_poem.make_text()
        logging.info("Sonnet creation successful.")
        return self.current_poem


class Section(object):
    def __init__(self, num_lines):
        self.template_list = [None for _ in xrange(num_lines)]
        self.filled = False


        self.interesting = None
        self.human = None
        self.offensive = None

    def polish(self):
        for template in self.template_list:
            template.polish()

    def make_text(self):
        self.polish()
        self.lines = [template.filled_line for template in self.template_list]
        self.text = "".join(["{}\n".format(line.text) for line in self.lines])

    def template_pairs(self):
        if len(self.template_list) == 4:
            template_pairs = [[self.template_list[0], self.template_list[2]],
                                   [self.template_list[1], self.template_list[3]]]
        if len(self.template_list) == 2:
            template_pairs = [self.template_list]
        return template_pairs

    def get_user_rating(self):
        self.interesting = input("Interesting? (0-10):")
        self.human = input("Human? (0-10):")
        self.offensive = input("Offensive? (0-10):")

class Poem(object):
    def __init__(self, section_lengths):
        self.section_lengths = section_lengths
        self.sections = [Section(length) for length in section_lengths]

    def __str__(self):
        return self.text

    def reset(self):
        for section in self.sections:
            section.filled = False

    def ordered_templates(self):
        ordered_templates = []
        for section in self.sections:
            ordered_templates.extend(section.template_list)
        return ordered_templates

    def polish(self):
        for section in self.sections:
            section.polish()
            section.make_text()

    def make_text(self):
        for section in self.sections:
            section.make_text()
        self.text = "".join([section.text for section in self.sections])

    def unfilled_sections(self):
        return [section for section in self.sections if not section.filled]


class Sonnet(Poem):
    def __init__(self):
        super(Sonnet, self).__init__([4, 4, 4, 2])




class HeroicCouplets(Poem):
    def __init__(self, num_couplets):
        super(HeroicCouplets, self).__init__([2 for _ in xrange(num_couplets)])



class SonnetFailure(Exception):
    """Base class for non-error things that cause sonnet creation to fail"""
    pass


class ConstructionFailure(SonnetFailure):
    """Raised when the selected lines are not properly assembled
    into quatrains and couplets"""

    def __init__(self, line_groups, msg):
        self.line_groups = line_groups
        self.msg = msg


class RhymeFailure(SonnetFailure):
    def __init__(self, rhyme_blank, msg):
        """Raised when unable to form a rhyme pool."""
        self.rhyme_blank = rhyme_blank
        self.msg = msg


class PairFailure(SonnetFailure):
    """Raised when unable to rhyme a pair of lines"""

    def __init__(self, template_pair, msg):
        self.template_pair = template_pair
        self.msg = msg


class ScanFailure(SonnetFailure):
    def __init__(self, template, msg):
        self.template = template
        self.msg = msg


if __name__ == '__main__':
    vocab = Vocab()
    sw = SonnetWriter(vocab)
    sw.load_templates("line_templates.csv")
    finished = False
    while not finished:
        s  = Sonnet()
        sw.new_poem(s)
        s.make_text()
        print s.text
        prompt = raw_input("\nAnother? (y/n)")
        if prompt != "y":
            finished = True
