import audioTrainTest as aT
aT.featureAndTrain(["../COPD","../normal"], 0.025, 0.025, aT.shortTermWindow, aT.shortTermStep, "randomforest", "classifier_rf", True)
