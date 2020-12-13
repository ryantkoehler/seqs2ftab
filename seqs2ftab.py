#!/usr/bin/env python
#
# Sequences to Feature Table
# Replacement for run_scores.csh
#
# Take a sequence file and file defining (the command line for) how to 
#   calculate various features, then build a feature table with all the 
#   calculated values for each sequence. 
# 
# 12/15/17 V0.1 RTK
# 2020-12-12 V0.12 RTK 
# 
import argparse
import subprocess
import re
import sys
import time
import pandas as pd
from pandas import DataFrame


__version__ = "V0.12; RTK 2020-12-12"


BARLINE = '=' * 75

# Help / explain details story
def explain_story():
    print(BARLINE)
    print(__version__)
    print(BARLINE)
    story="""
Parses command line definition file, calls commands with sequences as
inputs, collects outputs and builds a sequence feature table.")

Requires that command line functions generate single line outputs per
input sequence, starting with sequence name and followed by one or more
data fields. Any non-data lines should start with a comment '#'.

Sequences should be in raw format, each line: <name> <seq>
"""
    print(story)


def main():
    parser = argparse.ArgumentParser(description='Sequences to feature table')
    parser.add_argument("-c", "--cfile",
        help="Score definition (command line spec) filename\n"),
    parser.add_argument("-s", "--seqfile",
        help="Sequence file name (raw format: <name> <seq> per line)")
    parser.add_argument("-o", "--outfile",
        help="Output file name")
    parser.add_argument("--outcsv", action='store_true', 
        help="Output csv; i.e. values,separated,by,commas; Default is tabs")
    parser.add_argument("--dump", action='store_true', 
        help="Dump summary of score defs")
    parser.add_argument("--dryrun", action='store_true', 
        help="Only check inputs; Don't actually call commands")
    parser.add_argument("-e", "--explain", action='store_true',
        help="Print some info explaining use")

    args = parser.parse_args()
    if args.explain:
        explain_story()
        return

    if not args.cfile:
        print("No score definition file ... nothing more to do")
        return

    # Load definitions
    s2f = Seqs2ftab(args.cfile)
    if not s2f:
        print("Sorry, problem loading score defs")
        return
    print("# Loaded score definitions")
    if args.dump:
        s2f.dump_comcalls(comcalls=True)
    else:
        s2f.dump_comcalls(comcalls=False, names=False)

    if not args.seqfile:
        print("No sequence file ... nothing more to do!")
        return

    if args.dryrun:
        return

    # Process sequences
    df = s2f.process_df(args.seqfile)
    if df is None:
        print("Sorry, problem getting feature table (DataFrame)")
        return
    print(f"# Got feature table: {df.shape}")

    # Set output 
    if args.outfile:
        try:
            OFILE = open(args.outfile, 'w')
        except IOError:
            print("Failed to open output", args.outfile)
            return 
    else:
        OFILE = sys.stdout

    # Write output 
    if args.outcsv:
        sep = ','
    else:
        sep = '\t'
    df.to_csv(path_or_buf=OFILE, sep=sep, index_label="SeqName")

    # If new file, close and report
    if OFILE is not sys.stdout:
        OFILE.close()
        print("New file: {0}".format(args.outfile))


class Seqs2ftab:
    """ Top level object for seqs-to-feature-table
    
    sdef = 'score' definition file; i.e. command line calling recipe to get features
    sd_fmt = score def format
    
    """
    def __init__(self, sdef, sd_fmt='txt', verb=True, sd_seq='PDNA', name=''):
        self.sdef = sdef
        self.sd_fmt = sd_fmt.lower()
        self.verb = verb
        self.name = name
        # Set up score calls
        self._init_comcalls_()
        
        
    def __repr__(self):
        ostring =  "Seqs2ftab object\n"
        ostring += "NumCalls:  {0}\n".format(self.num_comcalls())
        ostring += "TotalCols: {0}\n".format(self.num_totcols())
        return ostring
    
    
    # Private
    # Parse command line definitions into comcall objects
    def _init_comcalls_(self):
        self.comcalls = []
        if self.sd_fmt == 'txt':
            self._parse_txt_sdef()
        elif self.sd_fmt == 'json':
            self._parse_raw_sdef()
        else:
            sham = "Unkown score def format: '{0}'".format(self.sd_fmt)
            raise ValueError(sham)
            
  
    # Private
    # Parse score defs in (newer) text format
    # Lines as: 
    #    <command,arg[,arg]> <outcol>=<name> [<outcol>=<name>]
    def _parse_txt_sdef(self):
        with open(self.sdef) as INFILE:
            # Regex for cigar segment parsing
            COLOUT_REGEX = re.compile('(\d+)=(\w+)')
            for line in INFILE:
                line = line.strip()
                # Ignore blank / comment lines
                if not line or line.startswith('#'):
                    continue
                # Parse out parts
                #    <command,arg[,arg]> <outcol>=<name> [<outcol>=<name>]
                lparts = line.split()
                comline = lparts[0].replace(',', ' ')
                colouts = []
                for part in lparts[1:]:
                    m = COLOUT_REGEX.match(part)
                    if not m:
                        sham = "Misformed score def col=name: |{0}|\tLine: |{1}|".format(part,line)
                        raise ValueError(sham)
                    colouts.append(m.groups())
                self.comcalls.append(ComCall(comline, colouts, rawdef=line))
    

    #    xxx TODO json format (someday?)
    def _parse_json_sdef(self):
        pass
    
    
    def dump_comcalls(self, OFILE=sys.stdout, pref='# ', comcalls=False, names=False):
        print(pref + "Seqs2ftab sequence score definitions", file=OFILE)
        print(pref + "Number command calls: {0}".format(self.num_comcalls()), file=OFILE)
        print(pref + "Total feature cols: {0}".format(self.num_totcols()), file=OFILE)
        if comcalls:
            for n,comcall in enumerate(self.comcalls):
                print(pref + "{0:2d}\t{1}".format(n+1, comcall.call_string()), file=OFILE)
                if names:
                    print(pref + "\tN={0}:\t{1}".format(comcall.num_cols(), comcall.name_list()), file=OFILE)


    # Number of command cols (features to be extracted)
    def num_comcalls(self):
        return len(self.comcalls)
    
    
    # Number of total feature cols to be generated (calculated not counted)
    def num_totcols(self):
        tot = 0
        for comcall in self.comcalls:
            tot += comcall.num_cols()
        return tot
    
    
    def process_df(self, seqfile, verb=True):
        """ Process all command calls with given sequence file
        
        seqfile = sequence filename to be processed
        
        returns DataFrame if all goes well
        returns None if problem
        """
        stime = time.time()
        for comcall in self.comcalls:
            if not comcall.process(seqfile, verb=verb):
                print('!' * 30 + ' PROBLEM ' + '!' * 30)
                print(comcall)
                print('!' * 30 + ' ABORTING ' + '!' * 30)
                return None
        
        # Concatentate each comcall dataframe into single one
        #    xxx TODO Error handling? try / except?
        df = pd.concat([x.df for x in self.comcalls], axis=1)
        if verb:
            nrow, ncol = df.shape
            print("# Total {0} rows X {1} cols".format(nrow, ncol))
            print("# Total time {:0.1f} sec".format(time.time()-stime))
        return df
        
    
class ComCall:
    """ Object to handle one command line call
    
    comcall = command line call (string)
    colouts = column output mapping as list of (<col>,<name>) tuples
    namecol = output column with name (i.e. sequence name)
    rawdef = raw definition (e.g. score def file line); just for reporting
    
    """
    def __init__(self, comcall, colouts, namecol=1, rawdef=None):
        # Command call; Replace any commas with space
        self.comcall = comcall.replace(',', ' ')
        self.colouts = colouts
        self.namecol = namecol
        self.rawdef = rawdef
        # Split tuples into two lists: cols (zero-base index), names
        self.cols = []
        self.names = []
        for col, name in self.colouts:
            self.cols.append(int(col)-1)
            self.names.append(name)
        self.col_max = max(self.cols)
        # Check no duplicate cols or names specified
        if len(self.cols) != len(set(self.cols)) or len(self.names) != len(set(self.names)):
            if rawdef is not None:
                sham = "Duplicated col / name specified: |{0}|".format(rawdef)
            else:
                sham = "Duplicated col / name specified: |{0}|".format(colouts)
            raise ValueError(sham)      
        # Name col from one-based to zero-base index
        if self.namecol is not None:
            self.namecol -= 1
        
        
    def __repr__(self):
        ostring =  "ComCall object\n"
        ostring += "Call:  '{0}'\n".format(self.comcall)
        ostring += "Num:   {0}\n".format(self.num_cols())
        ostring += "Defs:  {0}\n".format(self.colouts)
        return ostring
    
    
    # Number of cols (features to be extracted from output lines)
    def num_cols(self):
        return len(self.cols)
    

    def call_string(self):
        return self.comcall


    def name_list(self):
        return self.names


    def process(self, seqfile, verb=True):
        """ Call to process command line with given sequence file
        
        seqfile = sequence filename
        
        If all good, creates DataFrame with output data and returns True
        Any problems, returns False
        """
        stime = time.time()
        # Full command line = comcall part plus sequence filename
        comargs = self.comcall + ' ' + seqfile
        # Get list of output lines for call; 
        # shell=True means shell gets spawned (e.g. so env vars good)
        out = call_exec(comargs, shell=True, verb=verb)
        # False if problem (None)
        if out is None:
            return False
        # Process output into dataframe (maybe cleaner way?)
        # Row name list and dict of lists to collect col values
        rownames = []
        tdic = {}
        for name in self.names:
            tdic[name] = []
        # Collect values from each row into separate lists
        for r, row in enumerate(out):
            parts = row.split()
            if len(parts) <= self.col_max:
                sham = "Output row too few cols; max {0}\t|{1}|".format(self.col_max, row)
                raise ValueError(sham)    
            if self.namecol is None:
                rownames.append("row_{:05d}".format(r))
            else:
                rownames.append(parts[self.namecol])
            for name, col in zip(self.names, self.cols):
                tdic[name].append(parts[col])
        self.df = DataFrame(index=rownames, data=tdic)
        if verb:
            nrow, ncol = self.df.shape
            print("#  Data for {0} rows, {1} cols".format(nrow, ncol))
            print("#  Time for call {:0.2f} ms".format(1000 * (time.time()-stime)))
        return True


# ---------------------------------------------------------------------------
# Utility functions
def call_exec(com_args, shell=True, verb=False, vpref='# Call:', strip_com=True, strip_blank=True):
    """
    Call executable via command line.
        com_args = command line given as string or list; If list join as strings
        shell = flag to call with shell (so env vars good, etc)
        verb = verbosity flag; If true, print before call
        vpref = prefix string for verbose prints; '' for none

    Returns output split into list of lines
    """
    if type(com_args) is list:
        com_args = ' '.join([str(x) for x in com_args])

    if not isinstance(com_args, str):
        raise Exception("com_args not string or list.\ntype: %s\n" % type(com_args))

    if verb:
        if vpref is None:
            print(com_args)
        else:
            print(vpref, com_args)

    try:
        # universal_newlines=True makes output (and input?) have newline rather than '\n'
        # shell=True means spawn shell
        callout = subprocess.check_output(com_args, universal_newlines=True, shell=shell)
    except Exception as e:
        print("Subprocess failed: %s" % (str(e)))
        return None

    # Split into list of lines then clean / filter this
    callout = callout.splitlines()

    if callout and strip_com:
        callout = [x for x in callout if (x and not x.startswith('#'))]
    if callout and strip_blank:
        callout = [x for x in callout if (x and not x.isspace())]

    return callout


# ---------------------------------------------------------------------------
# Top level
if __name__ == "__main__":
    main()


