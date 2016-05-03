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
