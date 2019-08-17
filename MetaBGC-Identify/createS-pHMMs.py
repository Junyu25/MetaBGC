#!/usr/bin/python

"""
Created on Tues Oct 10 03:08:34 2017
Updated on Mon Feb 5 18:40:09 2018
@author: francinecamacho
"""
from __future__ import division
from Bio import AlignIO
import os 
import subprocess

"""
Script takes in an alignment file (fasta format), kmer len, and sliding window len. The script 
parses the alignment file with kmer len and sliding winder to create a new alignment file.
Furthermore, the script builds a HMM profile with parsed portion of the new alignment file.
"""

"""
Function builds HMM profile with the parsed portion of the alignment file. 
"""
def runHMMBuild(alnFile, modelName):

    print("Running HMM Build on:", alnFile)
    hmmFile = alnFile.split('.fas')[0] +".hmm"
    cmd = "hmmbuild -n " + modelName + " --amino "+ hmmFile + " "+ alnFile 
    print(cmd) 
    subprocess.call(cmd, shell=True)
    print("Done Running HMM Build on:",alnFile)

"""
Function parses alignment file into kmer parts of the alignment file,
with a sliding window method. 
"""
def getKmers(k, interval, outdir, msaFile, modelName, start, end):

    alignment = AlignIO.read(msaFile, "fasta")
    if (start != None) & (end !=None):
        alignment = alignment[:,start-1:end-1]
    print ("Number of domains: %i" % len(alignment))
    print ("Alignment length: %i" % alignment.get_alignment_length())

    counter = int(((alignment.get_alignment_length()- k) /interval)+1)

    j = 0 
    for i in range(counter):
        startPos = j 
        endPos = j+k 
        kmer = alignment[:,startPos:endPos] #[ rows (different domains),columns (Amino Acids)] 

        outputFile = msaFile.split('.fas')[0] + "__" + str(k)+ "_"+ str(interval) + "__"+ str(startPos)+ "_"+ str(endPos) + ".fas"
        os.chdir(outdir)
        AlignIO.write(kmer, outputFile, "fasta")
        runHMMBuild(outputFile, modelName)

        j = j+interval

def main(aln_file, window_len, kmer_len, outdir, hmmName, start, end ):

    getKmers(kmer_len, window_len, outdir, aln_file, hmmName, start, end)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--aln_file', type= str,required=True) 
    parser.add_argument('--window_len',type= int, required=False, default=10)
    parser.add_argument('--kmer_len', type= int, required=True ) 
    parser.add_argument('--outdir', type= str, required=True)
    parser.add_argument('--hmmName', type= str, required=True)
    parser.add_argument('--start', type = int, required=False)
    parser.add_argument('--end', type = int, required=False)        


    args = parser.parse_args()

    main(args.aln_file, args.window_len, args.kmer_len, args.outdir, args.hmmName, args.start, args.end )

