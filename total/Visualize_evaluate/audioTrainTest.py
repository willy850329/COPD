from __future__ import print_function
import sys
import numpy
import os
import glob
import pickle as cPickle
import signal
import csv
import ntpath
import audioFeatureExtraction as aF
import audioBasicIO
from scipy import linalg as la
from scipy.spatial import distance
import sklearn.svm
import sklearn.decomposition
import sklearn.ensemble

def signal_handler(signal, frame):
    print('You pressed Ctrl+C! - EXIT')
    os.system("stty -cbreak echo")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

shortTermWindow = 0.050
shortTermStep = 0.050
eps = 0.00000001



def classifierWrapper(classifier, classifier_type, test_sample):
    '''
    This function is used as a wrapper to pattern classification.
    ARGUMENTS:
        - classifier:        a classifier object of type sklearn.svm.SVC or kNN (defined in this library) or sklearn.ensemble.RandomForestClassifier or sklearn.ensemble.GradientBoostingClassifier  or sklearn.ensemble.ExtraTreesClassifier
        - classifier_type:    "svm" or "knn" or "randomforests" or "gradientboosting" or "extratrees"
        - test_sample:        a feature vector (numpy array)
    RETURNS:
        - R:            class ID
        - P:            probability estimate

    EXAMPLE (for some audio signal stored in array x):
        import audioFeatureExtraction as aF
        import audioTrainTest as aT
        # load the classifier (here SVM, for kNN use load_model_knn instead):
        [classifier, MEAN, STD, classNames, mt_win, mt_step, st_win, st_step] = aT.load_model(model_name)
        # mid-term feature extraction:
        [mt_features, _, _] = aF.mtFeatureExtraction(x, Fs, mt_win * Fs, mt_step * Fs, round(Fs*st_win), round(Fs*st_step));
        # feature normalization:
        curFV = (mt_features[:, i] - MEAN) / STD;
        # classification
        [Result, P] = classifierWrapper(classifier, model_type, curFV)
    '''
    R = -1
    P = -1
    if classifier_type == "knn":
        [R, P] = classifier.classify(test_sample)
    elif classifier_type == "svm" or \
                    classifier_type == "randomforest" or \
                    classifier_type == "gradientboosting" or \
                    classifier_type == "extratrees" or \
                    classifier_type == "svm_rbf":
        R = classifier.predict(test_sample.reshape(1,-1))[0]
        P = classifier.predict_proba(test_sample.reshape(1,-1))[0]
    return [R, P]





def randSplitFeatures(features, per_train):
    '''
    def randSplitFeatures(features):

    This function splits a feature set for training and testing.

    ARGUMENTS:
        - features:         a list ([numOfClasses x 1]) whose elements 
                            containt numpy matrices of features.
                            each matrix features[i] of class i is 
                            [n_samples x numOfDimensions]
        - per_train:        percentage
    RETURNS:
        - featuresTrains:   a list of training data for each class
        - f_test:           a list of testing data for each class
    '''

    f_train = []
    f_test = []
    for i, f in enumerate(features):
        [n_samples, numOfDims] = f.shape
        randperm = numpy.random.permutation(range(n_samples))
        n_train = int(round(per_train * n_samples))
        f_train.append(f[randperm[0:n_train]])
        f_test.append(f[randperm[n_train::]])
    return f_train, f_test

def load_model(model_name, is_regression=False):
    '''
    This function loads an SVM model either for classification or training.
    ARGMUMENTS:
        - SVMmodel_name:     the path of the model to be loaded
        - is_regression:     a flag indigating whereas this model is regression or not
    '''
    try:
        fo = open(model_name + "MEANS", "rb")
    except IOError:
            print("Load SVM model: Didn't find file")
            return
    try:
        MEAN = cPickle.load(fo)
        STD = cPickle.load(fo)
        if not is_regression:
            classNames = cPickle.load(fo)
        mt_win = cPickle.load(fo)
        mt_step = cPickle.load(fo)
        st_win = cPickle.load(fo)
        st_step = cPickle.load(fo)
        compute_beat = cPickle.load(fo)

    except:
        fo.close()
    fo.close()

    MEAN = numpy.array(MEAN)
    STD = numpy.array(STD)

    with open(model_name, 'rb') as fid:
        SVM = cPickle.load(fid)    

    if is_regression:
        return(SVM, MEAN, STD, mt_win, mt_step, st_win, st_step, compute_beat)
    else:
        return(SVM, MEAN, STD, classNames, mt_win, mt_step, st_win, st_step, compute_beat)



def trainRandomForest(features, n_estimators):
    '''
    Train a multi-class decision tree classifier.
    Note:     This function is simply a wrapper to the sklearn functionality for SVM training
              See function trainSVM_feature() to use a wrapper on both the feature extraction and the SVM training (and parameter tuning) processes.
    ARGUMENTS:
        - features:         a list ([numOfClasses x 1]) whose elements containt numpy matrices of features
                            each matrix features[i] of class i is [n_samples x numOfDimensions]
        - n_estimators:     number of trees in the forest
    RETURNS:
        - svm:              the trained SVM variable

    NOTE:
        This function trains a linear-kernel SVM for a given C value. For a different kernel, other types of parameters should be provided.
    '''

    [X, Y] = listOfFeatures2Matrix(features)
    rf = sklearn.ensemble.RandomForestClassifier(n_estimators = n_estimators)
    rf.fit(X,Y)

    return rf



def featureAndTrain(list_of_dirs, mt_win, mt_step, st_win, st_step, 
                    classifier_type, model_name, 
                    compute_beat=False, perTrain=0.90):
    '''
    This function is used as a wrapper to segment-based audio feature extraction and classifier training.
    ARGUMENTS:
        list_of_dirs:        list of paths of directories. Each directory contains a signle audio class whose samples are stored in seperate WAV files.
        mt_win, mt_step:        mid-term window length and step
        st_win, st_step:        short-term window and step
        classifier_type:        "svm" or "knn" or "randomforest" or "gradientboosting" or "extratrees"
        model_name:        name of the model to be saved
    RETURNS:
        None. Resulting classifier along with the respective model parameters are saved on files.
    '''

    # STEP A: Feature Extraction:
    [features, classNames, _] = aF.dirsWavFeatureExtraction(list_of_dirs, 
                                                            mt_win, 
                                                            mt_step, 
                                                            st_win, 
                                                            st_step, 
                                                            compute_beat=compute_beat)

    if len(features) == 0:
        print("trainSVM_feature ERROR: No data found in any input folder!")
        return

    n_feats = features[0].shape[1]
    feature_names = ["features" + str(d + 1) for d in range(n_feats)]

    writeTrainDataToARFF(model_name, features, classNames, feature_names)

    for i, f in enumerate(features):
        if len(f) == 0:
            print("trainSVM_feature ERROR: " + list_of_dirs[i] + " folder is empty or non-existing!")
            return

    # STEP B: classifier Evaluation and Parameter Selection:
    if classifier_type == "svm" or classifier_type == "svm_rbf":
        classifier_par = numpy.array([0.001, 0.01,  0.5, 1.0, 5.0, 10.0, 20.0])
    elif classifier_type == "randomforest":
        classifier_par = numpy.array([10, 25, 50, 100,200,500])      

    # get optimal classifeir parameter:
    features2 = []
    for f in features:        
        fTemp = []
        for i in range(f.shape[0]):
            temp = f[i,:]
            if (not numpy.isnan(temp).any()) and (not numpy.isinf(temp).any()) :
                fTemp.append(temp.tolist())
            else:
                print("NaN Found! Feature vector not used for training")
        features2.append(numpy.array(fTemp))
    features = features2

    bestParam = evaluateclassifier(features, classNames, 100, classifier_type, classifier_par, 0, perTrain)

    print("Selected params: {0:.5f}".format(bestParam))

    C = len(classNames)
    [features_norm, MEAN, STD] = normalizeFeatures(features)        # normalize features
    MEAN = MEAN.tolist()
    STD = STD.tolist()
    featuresNew = features_norm

    # STEP C: Save the classifier to file
    if classifier_type == "svm":
        classifier = trainSVM(featuresNew, bestParam)        
    elif classifier_type == "svm_rbf":
        classifier = trainSVM_RBF(featuresNew, bestParam)
    elif classifier_type == "randomforest":
        classifier = trainRandomForest(featuresNew, bestParam)
    elif classifier_type == "gradientboosting":
        classifier = trainGradientBoosting(featuresNew, bestParam)
    elif classifier_type == "extratrees":
        classifier = trainExtraTrees(featuresNew, bestParam)

    if classifier_type == "knn":
        [X, Y] = listOfFeatures2Matrix(featuresNew)
        X = X.tolist()
        Y = Y.tolist()
        fo = open(model_name, "wb")
        cPickle.dump(X, fo, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(Y,  fo, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(MEAN, fo, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(STD,  fo, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(classNames,  fo, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(bestParam,  fo, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(mt_win, fo, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(mt_step, fo, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(st_win, fo, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(st_step, fo, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(compute_beat, fo, protocol=cPickle.HIGHEST_PROTOCOL)
        fo.close()
    elif classifier_type == "svm" or classifier_type == "svm_rbf" or \
                    classifier_type == "randomforest" or \
                    classifier_type == "gradientboosting" or \
                    classifier_type == "extratrees":
        with open(model_name, 'wb') as fid:
            cPickle.dump(classifier, fid)            
        fo = open(model_name + "MEANS", "wb")
        cPickle.dump(MEAN, fo, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(STD, fo, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(classNames, fo, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(mt_win, fo, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(mt_step, fo, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(st_win, fo, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(st_step, fo, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(compute_beat, fo, protocol=cPickle.HIGHEST_PROTOCOL)
        fo.close()        




def evaluateclassifier(features, class_names, n_exp, classifier_name, Params, parameterMode, perTrain=0.90):
    '''
    ARGUMENTS:
        features:     a list ([numOfClasses x 1]) whose elements containt numpy matrices of features.
                each matrix features[i] of class i is [n_samples x numOfDimensions]
        class_names:    list of class names (strings)
        n_exp:        number of cross-validation experiments
        classifier_name: svm or knn or randomforest
        Params:        list of classifier parameters (for parameter tuning during cross-validation)
        parameterMode:    0: choose parameters that lead to maximum overall classification ACCURACY
                1: choose parameters that lead to maximum overall f1 MEASURE
    RETURNS:
         bestParam:    the value of the input parameter that optimizes the selected performance measure
    '''

    # feature normalization:
    (features_norm, MEAN, STD) = normalizeFeatures(features)
    #features_norm = features;
    n_classes = len(features)
    ac_all = []
    f1_all = []
    precision_classes_all = []
    recall_classes_all = []
    f1_classes_all = []
    cms_all = []

    # compute total number of samples:
    n_samples_total = 0
    for f in features:
        n_samples_total += f.shape[0]
    if n_samples_total > 1000 and n_exp > 50:
        n_exp = 50
        print("Number of training experiments changed to 50 due to high number of samples")
    if n_samples_total > 2000 and n_exp > 10:
        n_exp = 10
        print("Number of training experiments changed to 10 due to high number of samples")

    for Ci, C in enumerate(Params):
        # for each param value
        cm = numpy.zeros((n_classes, n_classes))
        for e in range(n_exp):
            # for each cross-validation iteration:
            print("Param = {0:.5f} - classifier Evaluation "
                  "Experiment {1:d} of {2:d}".format(C, e+1, n_exp))
            # split features:
            f_train, f_test = randSplitFeatures(features_norm, perTrain)
            # train multi-class svms:
            if classifier_name == "svm":
                classifier = trainSVM(f_train, C)
            elif classifier_name == "svm_rbf":
                classifier = trainSVM_RBF(f_train, C)
            elif classifier_name == "knn":
                classifier = trainKNN(f_train, C)
            elif classifier_name == "randomforest":
                classifier = trainRandomForest(f_train, C)
            elif classifier_name == "gradientboosting":
                classifier = trainGradientBoosting(f_train, C)
            elif classifier_name == "extratrees":
                classifier = trainExtraTrees(f_train, C)

            cmt = numpy.zeros((n_classes, n_classes))
            for c1 in range(n_classes):
                n_test_samples = len(f_test[c1])
                res = numpy.zeros((n_test_samples, 1))
                for ss in range(n_test_samples):
                    [res[ss], _] = classifierWrapper(classifier,
                                                     classifier_name,
                                                     f_test[c1][ss])
                for c2 in range(n_classes):
                    cmt[c1][c2] = float(len(numpy.nonzero(res == c2)[0]))
            cm = cm + cmt
        cm = cm + 0.0000000010
        rec = numpy.zeros((cm.shape[0], ))
        pre = numpy.zeros((cm.shape[0], ))

        for ci in range(cm.shape[0]):
            rec[ci] = cm[ci, ci] / numpy.sum(cm[ci, :])
            pre[ci] = cm[ci, ci] / numpy.sum(cm[:, ci])
        precision_classes_all.append(pre)
        recall_classes_all.append(rec)
        f1 = 2 * rec * pre / (rec + pre)
        f1_classes_all.append(f1)
        ac_all.append(numpy.sum(numpy.diagonal(cm)) / numpy.sum(cm))

        cms_all.append(cm)
        f1_all.append(numpy.mean(f1))

    print("\t\t, end=""")
    for i, c in enumerate(class_names):
        if i == len(class_names)-1:
            print("{0:s}\t\t".format(c), end="")
        else:
            print("{0:s}\t\t\t".format(c), end="")
    print("OVERALL")
    print("\tC", end="")
    for c in class_names:
        print("\tPRE\tREC\tf1", end="")
    print("\t{0:s}\t{1:s}".format("ACC", "f1"))
    best_ac_ind = numpy.argmax(ac_all)
    best_f1_ind = numpy.argmax(f1_all)
    for i in range(len(precision_classes_all)):
        print("\t{0:.3f}".format(Params[i]), end="")
        for c in range(len(precision_classes_all[i])):
            print("\t{0:.1f}\t{1:.1f}\t{2:.1f}".format(100.0 * precision_classes_all[i][c],
                                                       100.0 * recall_classes_all[i][c],
                                                       100.0 * f1_classes_all[i][c]), end="")
        print("\t{0:.1f}\t{1:.1f}".format(100.0 * ac_all[i], 100.0 * f1_all[i]), end="")
        if i == best_f1_ind:
            print("\t best f1", end="")
        if i == best_ac_ind:
            print("\t best Acc", end="")
        print("")

    if parameterMode == 0:    # keep parameters that maximize overall classification accuracy:
        print("Confusion Matrix:")
        printConfusionMatrix(cms_all[best_ac_ind], class_names)
        return Params[best_ac_ind]
    elif parameterMode == 1:  # keep parameters that maximize overall f1 measure:
        print("Confusion Matrix:")
        printConfusionMatrix(cms_all[best_f1_ind], class_names)
        return Params[best_f1_ind]



def printConfusionMatrix(cm, class_names):
    '''
    This function prints a confusion matrix for a particular classification task.
    ARGUMENTS:
        cm:            a 2-D numpy array of the confusion matrix
                       (cm[i,j] is the number of times a sample from class i was classified in class j)
        class_names:    a list that contains the names of the classes
    '''

    if cm.shape[0] != len(class_names):
        print("printConfusionMatrix: Wrong argument sizes\n")
        return

    for c in class_names:
        if len(c) > 4:
            c = c[0:3]
        print("\t{0:s}".format(c), end="")
    print("")

    for i, c in enumerate(class_names):
        if len(c) > 4:
            c = c[0:3]
        print("{0:s}".format(c), end="")
        for j in range(len(class_names)):
            print("\t{0:.2f}".format(100.0 * cm[i][j] / numpy.sum(cm)), end="")
        print("")


def normalizeFeatures(features):
    '''
    This function normalizes a feature set to 0-mean and 1-std.
    Used in most classifier trainning cases.

    ARGUMENTS:
        - features:    list of feature matrices (each one of them is a numpy matrix)
    RETURNS:
        - features_norm:    list of NORMALIZED feature matrices
        - MEAN:        mean vector
        - STD:        std vector
    '''
    X = numpy.array([])

    for count, f in enumerate(features):
        if f.shape[0] > 0:
            if count == 0:
                X = f
            else:
                X = numpy.vstack((X, f))
            count += 1

    MEAN = numpy.mean(X, axis=0) + 0.00000000000001;
    STD = numpy.std(X, axis=0) + 0.00000000000001;

    features_norm = []
    for f in features:
        ft = f.copy()
        for n_samples in range(f.shape[0]):
            ft[n_samples, :] = (ft[n_samples, :] - MEAN) / STD
        features_norm.append(ft)
    return (features_norm, MEAN, STD)


def listOfFeatures2Matrix(features):
    '''
    listOfFeatures2Matrix(features)

    This function takes a list of feature matrices as argument and returns a single concatenated feature matrix and the respective class labels.

    ARGUMENTS:
        - features:        a list of feature matrices

    RETURNS:
        - X:            a concatenated matrix of features
        - Y:            a vector of class indeces
    '''

    X = numpy.array([])
    Y = numpy.array([])
    for i, f in enumerate(features):
        if i == 0:
            X = f
            Y = i * numpy.ones((len(f), 1))
        else:
            X = numpy.vstack((X, f))
            Y = numpy.append(Y, i * numpy.ones((len(f), 1)))
    return (X, Y)



def fileClassification(inputFile, model_name, model_type):
    # Load classifier:

    if not os.path.isfile(model_name):
        print("fileClassification: input model_name not found!")
        return (-1, -1, -1)

    if not os.path.isfile(inputFile):
        print("fileClassification: wav file not found!")
        return (-1, -1, -1)

    if model_type == 'knn':
        [classifier, MEAN, STD, classNames, mt_win, mt_step, st_win, st_step,
         compute_beat] = load_model_knn(model_name)
    else:
        [classifier, MEAN, STD, classNames, mt_win, mt_step, st_win, st_step,
         compute_beat] = load_model(model_name)

    [Fs, x] = audioBasicIO.readAudioFile(inputFile)        # read audio file and convert to mono
    x = audioBasicIO.stereo2mono(x)

    if isinstance(x, int):                                 # audio file IO problem
        return (-1, -1, -1)
    if x.shape[0] / float(Fs) <= mt_win:
        return (-1, -1, -1)

    # feature extraction:
    [mt_features, s, _] = aF.mtFeatureExtraction(x, Fs, mt_win * Fs, mt_step * Fs, round(Fs * st_win), round(Fs * st_step))
    mt_features = mt_features.mean(axis=1)        # long term averaging of mid-term statistics
    if compute_beat:
        [beat, beatConf] = aF.beatExtraction(s, st_step)
        mt_features = numpy.append(mt_features, beat)
        mt_features = numpy.append(mt_features, beatConf)
    curFV = (mt_features - MEAN) / STD                # normalization

    [Result, P] = classifierWrapper(classifier, model_type, curFV)    # classification        
    return Result, P, classNames

def writeTrainDataToARFF(model_name, features, classNames, feature_names):
    f = open(model_name + ".arff", 'w')
    f.write('@RELATION ' + model_name + '\n')
    for fn in feature_names:
        f.write('@ATTRIBUTE ' + fn + ' NUMERIC\n')
    f.write('@ATTRIBUTE class {')
    for c in range(len(classNames)-1):
        f.write(classNames[c] + ',')
    f.write(classNames[-1] + '}\n\n')
    f.write('@DATA\n')
    for c, fe in enumerate(features):
        for i in range(fe.shape[0]):
            for j in range(fe.shape[1]):
                f.write("{0:f},".format(fe[i, j]))
            f.write(classNames[c]+"\n")
    f.close()



def main(argv):
    return 0

if __name__ == '__main__':
    main(sys.argv)
