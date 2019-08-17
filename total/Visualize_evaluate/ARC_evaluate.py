import audioTrainTest as aT
import time

def ARC_evaluate(wavFile, model_name, model_type):
    while(True):
        Result, P, classNames = aT.fileClassification(wavFile, model_name, model_type)
        Result = int(Result)
        print("{0:s}\t{1:s}".format(wavFile, classNames[Result]))
        time.sleep(5)
    return 0

if __name__ == '__main__':
    wavFile = '../model/soundfile/303_186_2b2_Pl_mc_AKGC417L.wav'
    #wavFile = '../model/soundfile/sound.wav'
    model_name = 'classifier_rf'
    model_type = 'randomforest'
    ARC_evaluate(wavFile, model_name, model_type)