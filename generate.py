# Author: Russell Williams
# Email: russell.d.williams@gmail.com

# Generates sonnets in bulk using sonnet.py.

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



import sonnet as snt
import pickle
import argparse
import sys


def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Generates and saves multiple sonnets.")
    parser.add_argument("--number",
                        "-n",
                        type=int,
                        default=20,
                        help="Number of sonnets to generate (Default: 20)")
    parser.add_argument("--output",
                        "-o",
                        required=True,
                        help="Output filename (Required)")
    parsed_args = parser.parse_args(args)
    return vars(parsed_args)


def main(args):
    v = snt.Vocab()
    sw = snt.SonnetWriter(v)
    sw.load_templates("line_templates.csv")

    sonnets = []
    while len(sonnets) < args["number"]:
        sw.vocab.add_random_collections()
        s = snt.Sonnet()
        sw.new_poem(s)
        sw.vocab.clear_collections()
        sonnets.append(s)

    with open(args["output"], "wb") as f:
        pickle.dump(sonnets, f)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args)
