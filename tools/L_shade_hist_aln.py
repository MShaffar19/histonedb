# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 13:09:07 2013

@author: alexeyshaytan
Let's visualize  histones

"""
#Standard librairies
import os
import re
import sys
from subprocess import Popen, PIPE, STDOUT
import argparse
import glob
import uuid

#Required libraires
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import AlignIO
from Bio import SeqIO
from Bio.Align import MultipleSeqAlignment
from Bio import AlignIO

#Custom libraries
from hist_ss import get_features_in_aln

DEVNULL = open(os.devnull, 'wb')

def write_texshade(file_handle,aln_fname,res_per_line,features=None,shading_modes=['similar'],logo=True,hideseqs=False):
    """
    """
    for shading in map(str, shading_modes):
        print >> file_handle, "    \\begin{{texshade}}{{{}}}".format(aln_fname)
        #print >> file_handle, "        \\residuesperline*{{{}}}".format(res_per_line)
        print >> file_handle, "        \\seqtype{P}"
        print >> file_handle, "        \\defconsensus{{}}{*}{upper}"

        if shading in ["similar","0"]:
            print >> file_handle, "        \\shadingmode{similar}"
            print >> file_handle, "        \\threshold[80]{50}"
            if logo:
                print >> file_handle, "        \\showsequencelogo{top} \\showlogoscale{leftright}"
                print >> file_handle, "        \\namesequencelogo{logo}"
        elif shading in ["hydropathy_functional", "1"]:
            print >> file_handle, "        \\shadingmode[hydropathy]{functional}"
            print >> file_handle, "        \\shadeallresidues"
            print >> file_handle, "        \\threshold[80]{50}"
            if logo:
                print >> file_handle, "        \\showsequencelogo[hydropathy]{top} \\showlogoscale{leftright}"
        elif shading in ["chemical_functional", "2"]:
            print >> file_handle, "        \\shadingmode[chemical]{functional}"
            print >> file_handle, "        \\shadeallresidues"
            if logo:
                print >> file_handle, "        \\showsequencelogo[chemical]{top} \\showlogoscale{leftright}"
        elif shading in ["structure_functional", "3"]:
            print >> file_handle, "        \\shadingmode[structure]{functional}"
            print >> file_handle, "        \\shadeallresidues"
        elif shading in ["charge_functional", "4"]:
            print >> file_handle, "        \\shadingmode[charge]{functional}"
            print >> file_handle, "        \\shadeallresidues"
        elif shading in ["diverse", "5"]:
            print >> file_handle, "        \\shadingmode{diverse}"

        if hideseqs:
            print >> file_handle, "        \\hideseqs"

        print >> file_handle, "        \\showconsensus[black]{bottom}"

        if features:
            print >> file_handle, "        {}".format(features)

        print >> file_handle, "        \showlegend"

        print >> file_handle, "    \end{texshade}"

def write_alignment(tex, align, title, shading_modes=["similar"], logo=False, hideseqs=False, splitN=20, secondary_structure=True, save_dir=""):
    """
    """
    ns='consensus'
    a_len=len(align)
    num=int(a_len/splitN)+1
    if((a_len-(num-1)*splitN)<2):
        splitN += 1
        num=int(a_len/splitN)+1
    if((a_len-(num-1)*splitN)<2):
        splitN=splitN+1
        num=int(a_len/splitN)+1
    if((a_len-(num-1)*splitN)<2):
        splitN=splitN+1
        num=int(a_len/splitN)+1
    name = os.path.splitext(title)[0].replace(" ", "")

    filename = tex.name[:-4]
    
    for i in xrange(num):
        t_aln=align[(i*splitN):((i+1)*splitN)]
        with open(os.path.join(save_dir, "{}_{}.fasta".format(filename, i)), "w") as aln_file:
            AlignIO.write(t_aln, aln_file, "fasta")
            print "wrote", aln_file.name
    
    res_per_line=len(align[0])
    
    #Let's make some drawing
    features = ""
    if secondary_structure:
        #prepare feature section
        for f in get_features_in_aln(align, filename, save_dir, save_gff=False):
            if(re.search('alpha',i)):
                features += "\\feature{tttop}{consensus}{%d..%d}{helix}{%s}"%(f.start+1,f.end+1,i)
            if(re.search('beta',i)):
                features += "\\feature{tttop}{consensus}{%d..%d}{-->}{%s}"%(f.start+1,f.end+1,i)
            if(re.search('loop',i)):
                features += "\\feature{ttttop}{consensus}{%d..%d}{loop}{%s}"%(f.start+1,f.end+1,i)
            if(re.search('domain',i)):
                features += "\\feature{ttttop}{consensus}{%d..%d}{loop}{%s}"%(f.start+1,f.end+1,i)
            if(re.search('tail',i)):
                features += "\\feature{ttttop}{consensus}{%d..%d}{loop}{%s}"%(f.start+1,f.end+1,i)
            if(re.search('mgarg',i)):
                features += "\\frameblock{consensus}{%d..%d}{Red[1.5pt]}"%(f.start+1,f.end+1)

    print >> tex, "    \\Huge{{{}}}".format(title.replace("_", "\_"))

    for i in xrange(num):
        write_texshade(
            tex, 
            os.path.join(save_dir, "{}_{}.fasta".format(filename, i)),
            res_per_line, 
            features,
            shading_modes=shading_modes, 
            logo=logo,
            hideseqs=hideseqs,
            )
        print >> tex, "    \\newpage"


def write_alignments(alignments, outfile=None, shading_modes=["similar"], logo=True, hideseqs=False, splitN=20, secondary_structure=True, save_dir=""):
    """
    """
    if outfile is None:
        n2=str(uuid.uuid4())
        outfile = "alignment_{}".format(n2)
    with open(os.path.join(save_dir, "{}.tex".format(outfile)), "w") as tex:
        print >> tex, "\\documentclass[11pt,landscape]{article}"
        print >> tex, "\\usepackage{hyperref}"
        print >> tex, "\\usepackage[paperwidth={}in, paperheight=18in]{{geometry}}".format(22/200.*200+2.5)
        print >> tex, "\\usepackage{texshade}\n"
        print >> tex, "\\begin{document}"
        for aln in alignments:
            if isinstance(aln, str):
                name = os.path.basename(aln)
                msa = MultipleSeqAlignment(list(SeqIO.parse(aln, "fasta")))
            elif isinstance(aln, MultipleSeqAlignment):
                msa = aln
                name = aln.annotations.get("name", "HistoneDB")
            else:
                raise RuntimeError("Invalid alignments: Must be a path to a FASTA format or a BioPython MultipleSequenceAlignment object.")
            
            write_alignment(
                tex, 
                msa, 
                name,
                shading_modes=shading_modes, 
                logo=logo, 
                hideseqs=hideseqs, 
                splitN=splitN,
                secondary_structure=secondary_structure,
                save_dir=save_dir
                )
        print >> tex, "\\end{document}"

    #Turn latex into pdf
    pdflatex = os.path.join(os.path.dirname(sys.executable), "pdflatex")
    # print pdflatex
    # print os.path.join(save_dir, "{}.tex".format(outfile))
    #assert 0, " ".join([pdflatex, "--file-line-error", "--synctex=1", "-output-directory={}".format(save_dir), "--save-size=10000", os.path.join(save_dir, "{}.tex".format(outfile))])
    process = Popen([pdflatex, "--file-line-error", "--synctex=1", "-output-directory={}".format(save_dir), "--save-size=10000", os.path.join(save_dir, "{}.tex".format(outfile))])
    process.communicate()

    #assert 0, 
    #assert os.path.exists(os.path.join(save_dir, "{}.pdf".format(outfile))),"Where are you?"

    os.remove(os.path.join(save_dir, "{}.tex".format(outfile)))
    os.remove(os.path.join(save_dir, "{}.aux".format(outfile)))
    os.remove(os.path.join(save_dir, "{}.log".format(outfile)))
    os.remove(os.path.join(save_dir, "{}.out".format(outfile)))

    for fasta_part in glob.glob(os.path.join(save_dir, "{}_*.fasta".format(name))):
        os.remove(fasta_part)

    return os.path.join(save_dir, "{}.pdf".format(outfile))

def parse_args():
    parser = argparse.ArgumentParser(description="")
     
    #Define Input
    parser.add_argument("alignments",
                        nargs="*",
                        help="Paths to multiple sequence alignment in fasta format, separated by whitespace")
    parser.add_argument("-o", "--outfile",
                        required=False,
                        default="alignment")
    parser.add_argument("-s", "--shading_modes",
                        required=False,
                        nargs="*",
                        default=["similar"],
                        help="Mode to shade alignments")
    parser.add_argument("--no_secondary_structure",
                        required=False,
                        action="store_true",
                        default=False,
                        help="Do not caluclate or display secondary strucutre")
    parser.add_argument("-l", "--logo",
                        required=False,
                        action="store_true",
                        default=False,
                        help="Display sequence logo")
    parser.add_argument("--hideseqs",
                        required=False,
                        action="store_true",
                        default=False,
                        help="Hide sequences from output")
    parser.add_argument("-n", "--splitN",
                        required=False,
                        type=int,
                        default=20,
                        help="Split MSA into separte pages with n seqs on each page")
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    write_alignments(
        args.alignments, 
        args.outfile, 
        shading_modes=args.shading_modes, 
        logo=args.logo, 
        hideseqs=args.hideseqs, 
        splitN=args.splitN,
        secondary_structure=not args.no_secondary_structure
        )


    
            