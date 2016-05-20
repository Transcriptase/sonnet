# Author: Russell Williams
# Email: russell.d.williams@gmail.com
# Copyright 2016

# Interprets a prompt and loads related vocab collections

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

from nltk.corpus import wordnet as wn


class Prompter(object):
    def __init__(self, vocab):
        self.vocab = vocab
        self.user_prompt = None
        self.user_prompt_words = None

    def get_input(self):
        prompt_phrase = "Please enter the prompt:"
        self.user_prompt = raw_input(prompt_phrase)
        self.user_prompt_words = self.user_prompt.split()
        self.prompt_meanings = [wn.synset(word) for word in self.user_prompt_words]