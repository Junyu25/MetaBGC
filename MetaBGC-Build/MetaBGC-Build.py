import os, re, time, sys, string, math
import argparse
import ntpath
import re
from Bio import AlignIO
from Utils.Utils import runHMMSearch
from Utils.Utils import runMakeBLASTDB
from Utils.Utils import runBLASTN
from Utils.Utils import parseHMM
from Utils.Utils import createPandaDF
from CreateSpHMMs import GenerateSpHMM
from rpy2.robjects.packages import STAP
from shutil import copyfile

CPU_THREADS = 1

def RunHMMDirectory(inputDir, hmmModel, sampleType, protType, window, interval, ouputDir):
    for subdir, dirs, files in os.walk(inputDir):
        sampleStr = ntpath.basename(subdir)
        for file in files:
            filePath = os.path.join(subdir, file)
            if re.match(r".*-translated.fasta$", file) and os.path.getsize(filePath) > 0:
                hmmTblFileName = file.split(".")[0] +"_"+interval+".tbl"
                hmmTblFilePath = os.path.join(ouputDir, hmmTblFileName)
                runHMMSearch(filePath, hmmModel,hmmTblFilePath,CPU_THREADS)
                result_dict = parseHMM(hmmTblFilePath, sampleType, sampleStr, protType, window, interval)
                hmmSearchFileName = file.split(".")[0] +"_"+interval+".txt"
                hmmSearchFilePath = os.path.join(ouputDir, hmmSearchFileName)
                createPandaDF(result_dict, hmmSearchFilePath)

def RunBLASTNDirectory(inputDir, blastDB, ouputDir):
    for subdir, dirs, files in os.walk(inputDir):
        sampleStr = ntpath.basename(subdir)
        for file in files:
            filePath = os.path.join(subdir, file)
            if re.match(r".*.fasta$", file) and not re.match(r".*-translated.fasta$", file) and os.path.getsize(filePath) > 0:
                outputFileName = file.split(".")[0]+".txt"
                outputFilePath = os.path.join(ouputDir, outputFileName)
                runBLASTN(filePath, blastDB, outputFilePath,CPU_THREADS)


if __name__ == '__main__':
    startTime = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('--prot_alignment', required=True, help="Alignment of the protein homologs in FASTA format.")
    parser.add_argument('--prot_family_name', required=True, help="Name of the protein family.")
    parser.add_argument('--cohort_name', required=True, help="Name of the sample/cohort name.")
    parser.add_argument('--nucl_seq_directory', required=True, help="Directory with nuleotide fasta files.")
    parser.add_argument('--prot_seq_directory', required=True, help="Directory with protein translated fasta files.")
    parser.add_argument('--tp_genes', required=True, help="Multi-FASTA with True Positive genes.")
    parser.add_argument('--gene_pos', required=True, help="Genes positions.")
    parser.add_argument('--F1_Thresh', required=True, help="F1 score threshold.")
    parser.add_argument('--output_directory', required=True, help="Directory to save results.")
    parser.add_argument('--cpu', required=False, help="Number of threads. Def.: 4")
    args = parser.parse_args()

    global CPU_THREADS
    if args.cpu is not None:
        CPU_THREADS = args.cpu

    hmm_directory = os.path.join(args.output_directory, 'spHMMs')
    os.makedirs(hmm_directory,0o777,True)
    copyfile(args.prot_alignment, hmm_directory+os.sep+ntpath.basename(args.prot_alignment))
    prot_aln_file = os.path.join(hmm_directory,ntpath.basename(args.prot_alignment))
    alignment = AlignIO.read(args.prot_alignment, "fasta")
    hmmDict = GenerateSpHMM(prot_aln_file, 10, 30, hmm_directory, args.prot_family_name, 1, alignment.get_alignment_length()+1)

    hmm_search_directory = os.path.join(args.output_directory, 'hmm_result')
    os.makedirs(hmm_search_directory,0o777,True)

    for hmmInterval, hmmFile in hmmDict.items():
        RunHMMDirectory(args.prot_seq_directory,hmmFile, args.cohort_name, args.prot_family_name, "30_10", hmmInterval, hmm_search_directory)

    allHMMResult = hmm_search_directory + os.sep + "CombinedHmmSearch.txt"
    with open(allHMMResult, 'w') as outfile:
        for subdir, dirs, files in os.walk(hmm_search_directory):
            for file in files:
                filePath = os.path.join(subdir, file)
                if re.match(r".*txt$", file) and os.path.getsize(filePath) > 0:
                    with open(filePath) as infile:
                        for line in infile:
                            outfile.write(line)

    blastn_search_directory = os.path.join(args.output_directory, 'blastn_result')
    os.makedirs(blastn_search_directory,0o777,True)

    tp_file = ntpath.basename(args.tp_genes)
    copyfile(args.tp_genes, blastn_search_directory + os.sep + tp_file)
    fastaFile = os.path.join(blastn_search_directory,tp_file)
    runMakeBLASTDB(fastaFile, tp_file, 'nucl')
    RunBLASTNDirectory(args.nucl_seq_directory, fastaFile, blastn_search_directory)

    allBLASTResult = blastn_search_directory + os.sep + "CombinedBLASTSearch.txt"
    with open(allBLASTResult, 'w') as outfile:
        for subdir, dirs, files in os.walk(blastn_search_directory):
            for file in files:
                filePath = os.path.join(subdir, file)
                if re.match(r".*txt$", file) and os.path.getsize(filePath) > 0:
                    with open(filePath) as infile:
                        for line in infile:
                            outfile.write(line)


    hp_hmm_directory = os.path.join(args.output_directory, 'HiPer_spHMMs')
    os.makedirs(hp_hmm_directory,0o777,True)
    with open('EvaluateSpHMM.R', 'r') as f:
        rStr = f.read()
    myfunc = STAP(rStr, "EvaluateSpHMM")
    myfunc.EvaluateSpHMM(allHMMResult,allBLASTResult,args.gene_pos,args.prot_family_name,float(args.F1_Thresh),hmm_search_directory,hp_hmm_directory)

    timeTaken = time.time() - startTime
    mins = int(timeTaken / 60)
    secs = int(timeTaken) % 60
    print("\nTotal time taken : " + str(mins) + " mins " + str(secs) + " seconds")
