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


def main(args):
    with open(args["input"], "r") as f:
        all_sonnets = pickle.load(f)
    unrated_sonnets = [sonnet for sonnet in all_sonnets if not sonnet.sections[0].interesting]
    rated_sonnets = [sonnet for sonnet in all_sonnets if sonnet.sections[0].interesting]
    for sonnet in unrated_sonnets:
        for section in sonnet.sections:
            print section.text
            section.get_user_rating()
        rated_sonnets.append(sonnet)

    with open(args["output"], "wb") as f:
        pickle.dump(rated_sonnets, f)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args)