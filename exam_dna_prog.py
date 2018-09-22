#!/usr/bin/env python
#
# example sequence-to-feature command line program
# 9/18/18 V0.1 RTK
#
import argparse


def main():
    parser = argparse.ArgumentParser(description='Sequences to features')
    parser.add_argument("seqfile", help="Sequence file name")
    parser.add_argument("-x", "--xfactor", help="Scale scores by X")

    args = parser.parse_args()

    with open(args.seqfile) as INFILE:
        for line in INFILE:
            line = line.strip()
            # Ignore blank / comment lines
            if not line or line.startswith('#'):
                continue
            # Name and seq
            name, seq = line.split()
            seq = seq.upper()

            # sequence-based numbers
            scores = []
            scores.append(len(seq))
            scores.append(seq.count('A'))
            scores.append(seq.count('C'))
            scores.append(seq.count('G'))
            scores.append(seq.count('T'))
            
            if args.xfactor:
                scores = [x * float(args.xfactor) for x in scores]
            
            ostring = '\t'.join([str(x) for x in scores])
            print(name, ostring)

# Called directly
if __name__ == "__main__":
    main()


