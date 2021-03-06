from metabgc.src.producer_consumer import *
import os
import re
import csv
import logging

"""
Function to run make BLAST db and search FASTA files. 
"""
def BLASTN(blastdb, searchFileList,
                  blastCmdString, blastParamStr, outFileList, ncpus):
    blastCmdList = []
    for i, queryFile in enumerate(searchFileList):
        outFile = outFileList[i]
        cmd = blastCmdString + " -num_threads 1 -query " + queryFile + " -db " + blastdb + " " + blastParamStr + " -out " + outFile
        blastCmdList.append(cmd)
        logging.info(cmd)

    invoke_producer_consumer(blastCmdList, ncpus - 2)
    logging.info("Done running BLAST searches.")


"""
Function to run make BLAST db and search FASTA files. 
"""
def MakeDB_BLASTN(dbFileList, existing_map_dict, dbOpPath, searchFileList, blastCmdString, blastParamStr, outFileList, ncpus):
    dbOutDict = {}
    makeDBCmdList=[]
    blastCmdList = []
    for dbInputFile in dbFileList:
        sample_basename = os.path.basename(dbInputFile)
        dbOut = ""
        if sample_basename in existing_map_dict:
            dbOut = existing_map_dict[sample_basename]
            dbOutDict[dbInputFile] = dbOut
            logging.info("Found existing database path:" + dbOut)

        if not os.path.isfile(dbOut):
            logging.info("Constructing BLAST DB for:" + dbInputFile)
            dbOpPath = dbOpPath + os.sep + sample_basename
            os.makedirs(dbOpPath, 0o777, True)
            dbName = os.path.splitext(sample_basename)[0]
            dbOut = dbOpPath + os.sep + dbName
            cmd = "makeblastdb -in " + dbInputFile + " -title " + dbName + " -dbtype nucl -out " + dbOut
            dbOutDict[dbInputFile] = dbOut
            makeDBCmdList.append(cmd)
            logging.info(cmd)

    invoke_producer_consumer(makeDBCmdList, ncpus - 2)
    logging.info("Done creating BLAST databases if any were needed.")

    for i, dbInputFile in enumerate(dbFileList):
        fastaFile = searchFileList[i]
        dbOut = dbOutDict[dbInputFile]
        outFile = outFileList[i]
        cmd = blastCmdString + " -num_threads 1 " + \
                  " -query " + fastaFile + " -db " + dbOut + " " + blastParamStr + " -out " + outFile
        blastCmdList.append(cmd)
        logging.info(cmd)

    invoke_producer_consumer(blastCmdList, ncpus - 2)
    logging.info("Done running BLAST searches.")

"""
Function to create blast databases from the fasta files in dbDir and running a query against the directory. 
"""
def RunPCMakeDBandBlastN(dbDir, existingDbDirMapFile, queryFile, blastCmdString, blastParamStr, ouputDir, ncpus=4):
    existing_map_dict = {}
    if existingDbDirMapFile:
        logging.info("Existing database path map provided:" + existingDbDirMapFile)
        existing_map_dict = {}
        map_file = os.path.join(existingDbDirMapFile)
        with open(map_file) as f:
            reader = csv.reader(f, skipinitialspace=True)
            existing_map_dict = dict(reader)

    dbFileList = []
    searchFileList = []
    outFileList = []

    for subdir, dirs, files in os.walk(dbDir):
        for file in files:
            filePath = os.path.join(subdir, file)
            if re.match(r".*\.fasta$", file) and os.path.getsize(filePath) > 0:
                sampleStr = os.path.splitext(file)[0]
                outputFileName = sampleStr + ".txt"
                outputFilePath = os.path.join(ouputDir, outputFileName)
                dbFileList.append(filePath)
                searchFileList.append(queryFile)
                outFileList.append(outputFilePath)

    MakeDB_BLASTN(dbFileList,existing_map_dict,
                  ouputDir, searchFileList, blastCmdString, blastParamStr, outFileList,ncpus)

"""
Function to search a bunch of blast queries against the database provided. 
"""
def RunPCBlastSearch(blastdb, queryFileList, blastCmdString, blastParamStr, ouputDir, ncpus=4):
    searchFileList = []
    outFileList = []
    for file in queryFileList:
        if os.path.exists(file):
            searchFileList.append(file)
            rootFileName = os.path.splitext(os.path.basename(file))[0]
            outFileName = os.path.join(ouputDir,rootFileName + ".txt")
            outFileList.append(outFileName)
    BLASTN(blastdb, searchFileList,
                  blastCmdString, blastParamStr, outFileList)


