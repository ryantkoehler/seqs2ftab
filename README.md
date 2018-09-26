seqs2ftab
========

### Sequence to Feature Table tool

9/18/18 RTK V0.1

**Overview**

The script *seqs2ftab.py* is used, in conjunction with "score definition" 
and sequence files, to generate sequence feature tables suitable for data
analysis and machine learning.


----------------------------------------------------------------------------
**Dependencies**

The script requires pandas.

It also requires a utility function in (included) 'rtk_io.py'


----------------------------------------------------------------------------
**Background**

The code parses the score definition file, then issues command line calls
for each definition line and parses output(s) into a table. Each score 
definition line includes a command line specificiation, with program name
and options separated by commas (rather than spaces), followed by one or 
more feature specifications (separated from the command specificiation and
each other by spaces). When actually called, the command line is given a
sequence filename as an additional agrument. Feature specifications take 
the form 'name=col' where the 'name' is a user-defined label for the 
feature (should be unique), and 'col' indicates which (command line) output 
column the feature is taken from.

Here is an example score definition line:

    tm_util,-con,1e-7,-sal,0.2,-tmpey,-the  2=tmPey0_f 3=dGPey0_f 4=dHPey0_f 5=dSPey0_f

In this case, the script will call the program *tm_util* to get thermodynamic
features. The command line specification and corresponding command line are
as follows (using 'rand_seqs.dna' as the sequence filename):

    # Score definition line; i.e. in score definition file 
    tm_util,-con,1e-7,-sal,0.2,-tmpey,-the

    # Actual command line; i.e. issued by script
    tm_util -con 1e-7 -sal 0.2 -tmpey -the rand_seqs.dna

The command line options -con and -sal set concentration and salt (to 1e-7 
and 0.2 M, respectively). The -tmpey and -the options specify the Peyret 
thermodynamics algorithm and to output thermodynamic values, respectively.

There are four features indicated in the score definition line; From col 2
we will get sequence melting temperature, Tm (named as 'tmPey0_f'), and from
columns 3,4,5 we will get free energy ('dGPey0_f'), enthalpy ('dHPey0_f'), 
and entropy (dSPey0_f).

**NOTE1**: The output of called programs must have one line per input 
sequence. Blank lines and lines starting with "#" are ignored. Otherwise,
each input sequence should have a corresponding output line with values to
be extracted and compiled into score tables. 

**NOTE2**: *tm_util* as well as other programs listed in the example score 
definition file (*dna_util*, *alphcont*, *venpipe*) are all part of the 
vertools collection; Source code is available here:

    https://github.com/ryantkoehler/vertools


----------------------------------------------------------------------------
Usage

The script requires a score definition file and a sequence file.

Calling the script with --help will list options and (currently minimal!)
usage instructions.

The following command line generates a table of features for the given 
sequences; The output table has 32 features for 1000 sequences.

    ./seqs2ftab.py -s rand_seqs.dna -d exam_score_defs.txt -o rand_seqs.sco

