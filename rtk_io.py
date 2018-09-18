#   Misc IO functions
# 3/1/15 RTK; Merge from other places and update
# 7/28/15 RTK; Add dict_lines_from_table
# 10/20/17 RTK; Add call_exec*() functions
# 2/27/18 RTK; Add subdir functions
# 3/17/18 RTK; Add json

from __future__ import print_function

import re
import sys
import os
import glob
import subprocess
import json

BLANK_REGEX = re.compile('^\s*$')


# ----------------------------------------------------------------------------
#   General util
# ----------------------------------------------------------------------------
def string_or_none(st, default='None'):
    """Return string if not None, else default.

    This is useful to print possibly unset variables
    """
    if st is None:
        return default
    else:
        return st


# ----------------------------------------------------------------------------
#   General Inputs
# ----------------------------------------------------------------------------
def lines_from_fname(fname, com='#', blanks=False, verb=False):
    """Take filename, return list of lines
    """
    lines = []
    with open(fname, 'r') as infile:
        lines = lines_from_stream(infile, com=com, blanks=blanks)
    if verb:
        print("# Loaded", len(lines), "lines from", fname)
    return lines


def lines_from_stream(instr, com='#', blanks=False):
    """Take input stream, return list of lines

    Arguments:
    instr   Input stream
    com     Comment line start; These lines ignored
    """
    lines = []
    for line in instr:
        if com and line.startswith(com):
            continue
        if re.match(BLANK_REGEX,line) and not blanks:
            continue
        lines.append(line.rstrip('\n'))
    return lines


def table_from_fname(fname, mincol=1, maxcol=0, com='#', sep=None, verb=False):
    """Take filename, return table = list of lists (i.e. rows of tokens)

    Arguments:
    fname   File name
    mincol  Minimum number of columns (tokens) for row to be collected
    maxcol  Only collect up to this many tokens per row
    com     Comment line start; These lines ignored
    sep     Separator for tokens
    """
    table = []
    lines = lines_from_fname(fname, com)
    for line in lines:
        if sep:
            row = line.split(sep)
        else:
            row = line.split()
        if maxcol > 0 and len(row) > maxcol:
            row = row[0:maxcol]
        if len(row) >= mincol:
            table.append(row)
    if verb:
        print("# Loaded", len(table), "rows from", fname)
    return table


def list_from_fname(fname, com='#', sep=''):
    """Take filename, return list (of first token on each line)"""
    tab = table_from_fname(fname, com=com, sep=sep)
    lis = []
    for row in tab:
        lis.append(row[0])
    return lis


def dict_of_lists_from_fname_list(fnames, path=None, com='#', sep='', verb=True):
    """Take list of filenames, return dict of list of lists

    Arguments:
    fnames  List of file names (to be be opened)
    path    File path (prepended to file names)
    com     Comment line start; These lines ignored
    """
    ldic = {}
    for name in fnames:
        if path:
            name = path + '/' + name
        # TODO better error checking????
        lis = list_from_fname(name, com=com, sep=sep)
        if len(lis) > 0:
            ldic[name] = lis
    return ldic


def dict_lines_from_table(fname, kcol=0, com='#', sep=None, verb=False):
    """Takes a filename for a table and returns dict with table lines

    kcol = column to use as key; Should be unique (obviously)
    """
    tab = table_from_fname(fname, com=com, sep=sep, verb=verb)
    dic = {}
    for row in tab:
        key = row[kcol]
        dic[key] = row
    return dic


# ----------------------------------------------------------------------------
#   General Outputs
# ----------------------------------------------------------------------------
def check_nfile(fh, fname=None, pref=''):
    """ Close passed file handle if open
        Report this if given name
    """
    if fh and not fh.closed:
        if fname:
            if fh.mode[0] == 'w':
                print(pref + "New file:", fname)
            else:
                print(pref + "Closed file:", fname)
        fh.close()
        fh = None
    return fh


def dump_table_to_fname(table, fname, sep='\t', verb=True):
    """Dump table (list of lists) to filename """
    tlis = [sep.join([str(x) for x in row]) for row in table]
    dump_list_to_fname(tlis, fname, verb=verb)


def dump_list_to_fname(itemlist, fname, verb=True):
    """Dump list to filename, one item per line

    If fname is '-' then use stdout
    """
    if fname == '-':
        outfile = sys.stdout
    else:
        outfile = open(fname, 'w')
    if outfile != None:
        dump_list_to_stream(itemlist, outfile)
        if verb and outfile != sys.stdout:
            print("Output written to", fname)
    if fname != '-':
        outfile.close()


def dump_list_to_stream(itemlist, outstr):
    outstr.write('\n'.join(itemlist) + '\n')


# Report dictionary
def report_dict(dic, first=-1, last=-1, sort_key=False, sort_val=False, reverse=False,
        dump_key=True, dump_val=False, dump_func=None, ret_lis=False, ofile=sys.stdout):
    """Take dictionary and report (print) things from it

    Arguments:
    dic             Dictionary
    first/last      First / last values to dump (like slice; after sort)
    sort_key/val    Flag to sort by key / value
    revsere         Reverse sorting (if any)
    dump_key/val    Flag to dump key / value
    dump_func       Function to call for value dump
    ret_lis         Flag to return list of dumped keys
    ofile           Output file stream to print to
    """
    if sort_key:
        dits = sorted(dic.items(), key=lambda x: x[0], reverse=reverse)
    elif sort_val:
        dits = sorted(dic.items(), key=lambda x: x[1], reverse=reverse)
    else:
        dits = dic.items()
    first = first if first >= 0 else 0
    last = last if last >= 0 else len(dits)
    dits = dits[first:last]
    rkeys = []
    for k, v in dits:
        if dump_func:
            dump_func(k,v)
        elif dump_val:
            print(k,"\t", v, file=ofile)
        elif dump_key:
            print(k, file=ofile)
        rkeys.append(k)
    if ret_lis:
        return rkeys


# ----------------------------------------------------------------------------
#   json dict save load
# ----------------------------------------------------------------------------
def dict_from_json(fname, failok=False):
    try:
        with open(fname, 'r') as IFILE:
            dic = json.load(IFILE)
            return dic
    except Exception as e:
        if failok:
            return None
        else:
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
            raise


def dict_to_json(dic, fname, failok=False):
    try:
        with open(fname, 'w') as OFILE:
            json.dump(dic, OFILE)
            return True
    except Exception as e:
        if failok:
            return None
        else:
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
            raise


# ----------------------------------------------------------------------------
#   Filename collecting for (dir) path
# ----------------------------------------------------------------------------
def fnames_for_path(path='.', glob_pat=None, regex=None, start_with=None, ext=None, verb=False):
    """Take file path and qualifiers, return list of filenames

    Arguments:
    path        File path to look in
    glob_pat    Glob pattern for match
    regex       Regex for files to match
    start_with  Prefix for files to match
    ext         Extension for files to match
    """
    # Get all (possibly with extension) files in path
    #   glob returns *full path* so strip to just name
    if glob_pat:
        contents = [os.path.basename(x) for x in glob.glob(path + '/' + glob_pat)]
    elif ext:
        contents = [os.path.basename(x) for x in glob.glob(path + '/*.' + ext)]
    else:
        contents = os.listdir(path)
    # If subset qualifier get only these
    if regex:
        fnames = [f for f in contents if re.match(regex,f)]
    elif start_with:
        fnames = [f for f in contents if f.startswith(start_with)]
    else:
        fnames = contents
    if verb:
        print("# Found", len(fnames), "matching files in", path)
    return fnames


# Get qualified filenames in listed path
# Return dictionary with filenames as values and simplified name-derived keys
def fnames_dict_for_path(path, ext=None, regex=None, start_with=None,
        fton_fun=None, split='.', full_path=True, verb=False):
    """Take file path and qualifiers, return dict of names and filenames

    Arguments:
    path        File path to look in
    ext         Extension for qualifying files
    start_with  Files must start with this
    split       Character to split filenames on (and take first part as name)
    fton_fun    Function to convert filename to simplified name
    full_path   Flag to put full path as filenames
    """
    # Returned files are names only; no path
    fnames = fnames_for_path(path, ext=ext, regex=regex, start_with=start_with, verb=verb)
    # Extract key part from names
    snames = extrc_subs_from_string_list(fnames, fun=fton_fun, split=split)
    # If full path, add that up front
    if full_path:
        fnames = [path + '/' + s for s in fnames]
    fdic = dict(zip(snames, fnames))
    if verb:
        print("# Filenames yielded", len(fdic), "unique keys")
    return fdic


def get_fname_parts(fname):
    """Take file name and split into path + basename + extension

    """
    path = os.path.dirname(fname)
    bname, ext = os.path.splitext(os.path.basename(fname))
    ext = ext.replace('.', '')
    return path, bname, ext


# Based on code from https://stackoverflow.com/questions/28622452/list-files-in-a-subdirectory-in-python-mindepth-maxdepth
def subdirs(rootdir='.', maxdepth=float('inf')):
    """ Return subdirs under rootdir to given maxdepth; 

    Generator
    """
    root_depth = rootdir.rstrip(os.path.sep).count(os.path.sep) - 1
    for dirpath, dirs, files in os.walk(rootdir):
        depth = dirpath.count(os.path.sep) - root_depth
        if depth <= maxdepth:
            for dirname in dirs:
                yield os.path.join(dirpath, dirname)
        elif depth > maxdepth:
            del dirs[:] # too deep, don't recurse
            
            
def subdir_list(rootdir='.', maxdepth=float('inf')):
    """ Return subdirs under rootdir to given maxdepth

    Return list of subdirs
    """
    return [x for x in subdirs(rootdir, maxdepth)]


# TODO belongs somewhere else
# Take strings from list and extract shorter parts into new list
def extrc_subs_from_string_list(slis, fun=None, split='.'):
    nlis = []
    for s in slis:
        if fun:
            nlis.append(fun(s))
        else:
            nlis.append(s.split(split)[0])
    return nlis


# ----------------------------------------------------------------------------
#   Command line execution calls
# ----------------------------------------------------------------------------
def call_exec(com_args, shell=True, verb=False, vpref='# Call:', linelist=False):
    """
    Call executable via command line.
        com_args = command line given as string or list; If list join as strings
        shell = flag to call with shell (so env vars good, etc)
        verb = verbosity flag; If true, print before call
        vpref = prefix string for verbose prints; '' for none
        linelist = flag to split output into list of lines

    Returns output as given or split into list of lines
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

    if linelist:
        callout = callout.splitlines()

    return callout


def call_exec_lines(com_args, shell=True, verb=False, vpref='# Call:', strip_com=True, strip_blank=True):
    """
    Call executable via command line; wrapper for call_exec
        com_args = command line given as string or list; If list join as strings
        shell = flag to call with shell (so env vars good, etc)
        verb = verbosity flag; If true, print before call
        vpref = prefix string for verbose prints
        strip_com = flag to strip out comment lines (start with '#')
        strip_blank = flag to strip out blank lines

    Returns list of lines from command output
    """
    callout = call_exec(com_args, shell=shell, verb=verb, vpref=vpref, linelist=True)
    if callout and strip_com:
        callout = [x for x in callout if (x and not x.startswith('#'))]
    if callout and strip_blank:
        callout = [x for x in callout if (x and not x.isspace())]

    return callout


