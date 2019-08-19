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
    wavFile = './Visualize_evaluate/soundfile/sound.wav'
    model_name = './model/classifier_rf'
    model_type = './model/randomforest'
    ARC_evaluate(wavFile, model_name, model_type)