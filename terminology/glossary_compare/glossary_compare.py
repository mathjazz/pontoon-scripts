import argparse
from xml.etree import ElementTree as et

nsmap = {"xml": "http://www.w3.org/XML/1998/namespace"}


def extract_terms_smartling(file):
    """ Returns a set containing all terms extracted from the Smartling glossary export """
    root = et.parse(file).getroot()
    term_list = []
    for termEntry in root.iter("termEntry"):
        term = termEntry.find(
            "./langSet[@xml:lang='en-US']/tig/term",
            nsmap,
        ).text
        term_list.append(term)
    return set(term_list)


def extract_terms_pontoon(file):
    """ Returns a set containing all terms extracted from the Pontoon terminology export """
    root = et.parse(file).getroot()
    term_list = []
    for termEntry in root.iter("termEntry"):
        term = termEntry.find(
            "./langSet[@xml:lang='en-US']/ntig/termGrp/term",
            nsmap,
        ).text
        term_list.append(term)
    return set(term_list)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--smartling",
        required=True,
        dest="smartling_glossary",
        help="Path to .tbx file exported from Smartling",
    )
    parser.add_argument(
        "--pontoon",
        required=True,
        dest="pontoon_glossary",
        help="Path to .tbx file exported from Pontoon",
    )
    args = parser.parse_args()

    smartling = extract_terms_smartling(args.smartling_glossary)
    pontoon = extract_terms_pontoon(args.pontoon_glossary)
    
    smartling_exclusive_terms = list(smartling.difference(pontoon))
    smartling_exclusive_terms.sort()

    with open("output.csv", "w") as f:
        f.write("\n".join(smartling_exclusive_terms))
        print("Smartling exclusive terms saved to output.csv")


if __name__ == "__main__":
    main()
