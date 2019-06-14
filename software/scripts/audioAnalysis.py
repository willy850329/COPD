from __future__ import print_function
import argparse
import os
import numpy
import glob
import matplotlib.pyplot as plt
import audioFeatureExtraction as aF
import audioTrainTest as aT
import audioBasicIO
import scipy.io.wavfile as wavfile
import matplotlib.patches



def featureExtractionFileWrapper(wav_file, out_file, mt_win, mt_step,
                                 st_win, st_step):
    if not os.path.isfile(wav_file):
        raise Exception("Input audio file not found!")

    aF.mtFeatureExtractionToFile(wav_file, mt_win, mt_step, st_win,
                                 st_step, out_file, True, True, True)


def featureExtractionDirWrapper(directory, mt_win, mt_step, st_win, st_step):
    if not os.path.isdir(directory):
        raise Exception("Input path not found!")
    aF.mtFeatureExtractionToFileDir(directory, mt_win, mt_step, st_win,
                                    st_step, True, True, True)


def trainClassifierWrapper(method, beat_feats, directories, model_name):
    if len(directories) < 2:
        raise Exception("At least 2 directories are needed")
    aT.featureAndTrain(directories, 1, 1, aT.shortTermWindow, aT.shortTermStep,
                       method.lower(), model_name, compute_beat=beat_feats)




def classifyFileWrapper(inputFile, model_type, model_name):
    if not os.path.isfile(model_name):
        raise Exception("Input model_name not found!")
    if not os.path.isfile(inputFile):
        raise Exception("Input audio file not found!")

    [Result, P, classNames] = aT.fileClassification(inputFile, model_name,
                                                    model_type)
    print("{0:s}\t{1:s}".format("Class", "Probability"))
    for i, c in enumerate(classNames):
        print("{0:s}\t{1:.2f}".format(c, P[i]))
    print("Winner class: " + classNames[int(Result)])


def classifyFolderWrapper(inputFolder, model_type, model_name,
                          outputMode=False):
    if not os.path.isfile(model_name):
        raise Exception("Input model_name not found!")
	print("START!!")
    types = ('*.wav', '*.aif',  '*.aiff', '*.mp3')
    wavFilesList = []
    for files in types:
        wavFilesList.extend(glob.glob((inputFolder + files)))
    wavFilesList = sorted(wavFilesList)
    if len(wavFilesList) == 0:
        print("No WAV files found!")
        return
    Results = []
    for wavFile in wavFilesList:
        [Result, P, classNames] = aT.fileClassification(wavFile, model_name,
                                                        model_type)
        Result = int(Result)
        Results.append(Result)
        if outputMode:
            print("{0:s}\t{1:s}".format(wavFile, classNames[Result]))
    Results = numpy.array(Results)

    # print distribution of classes:
    [Histogram, _] = numpy.histogram(Results,bins=numpy.arange(len(classNames) + 1))
    for i, h in enumerate(Histogram):
        print("{0:20s}\t\t{1:d}\t\t".format(classNames[i], h),float(h)/float(Histogram[0]+Histogram[1]))


def parse_arguments():
    parser = argparse.ArgumentParser(description="A demonstration script "
                                                 "for pyAudioAnalysis library")
    tasks = parser.add_subparsers(
        title="subcommands", description="available tasks",
        dest="task", metavar="")


    classFile = tasks.add_parser("classifyFile",
                                 help="Classify a file using an "
                                      "existing classifier")
    classFile.add_argument("-i", "--input", required=True,
                           help="Input audio file")
    classFile.add_argument("--model", choices=["svm", "svm_rbf", "knn",
                                               "randomforest",
                                               "gradientboosting",
                                               "extratrees"],
                           required=True, help="Classifier type (svm or knn or"
                                               " randomforest or "
                                               "gradientboosting or "
                                               "extratrees)")
    classFile.add_argument("--classifier", required=True,
                           help="Classifier to use (path)")
    classFolder = tasks.add_parser("classifyFolder")
    classFolder.add_argument("-i", "--input", required=True,
                             help="Input folder")
    classFolder.add_argument("--model", choices=["svm", "svm_rbf", "knn",
                                                 "randomforest",
                                                 "gradientboosting",
                                                 "extratrees"],
                             required=True, help="Classifier type")
    classFolder.add_argument("--classifier", required=True,
                             help="Classifier to use (filename)")
    classFolder.add_argument("--details", action="store_true",
                             help="Plot details (otherwise only "
                                  "counts per class are shown)")


    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    
    if args.task == "classifyFile":
        # Apply audio classifier on audio file
        classifyFileWrapper(args.input, args.model, args.classifier)
    
    elif args.task == "classifyFolder":
        # Classify every WAV file in a given path
        classifyFolderWrapper(args.input, args.model, args.classifier,
                              args.details)
    
