import pickle
import argparse
import sys


def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Gets user ratings for sonnets in an input pickle")
    parser.add_argument("--input",
                        "-i",
                        required=True,
                        help="Input filename (Required)")
    parser.add_argument("--output",
                        "-o",
                        required = True,
                        help = "Output filename (Required)")
    parsed_args = parser.parse_args(args)
    return vars(parsed_args)

def rate_section(section):
    print section.text
    print "\n"
    section.get_user_rating()

def rate_sonnet(sonnet):
    for section in sonnet.sections:
        rate_section(section)


def main(args):
    with open(args["input"], "r") as f:
        all_sonnets = pickle.load(f)
    unrated_sonnets = [sonnet for sonnet in all_sonnets if not sonnet.sections[0].interesting]
    rated_sonnets = [sonnet for sonnet in all_sonnets if sonnet.sections[0].interesting]
    for sonnet in unrated_sonnets:
        rate_sonnet(sonnet)

    with open(args["output"], "wb") as f:
        pickle.dump(rated_sonnets, f)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args)