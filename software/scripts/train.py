import audioTrainTest as aT
aT.featureAndTrain(["../stop breath","../normal data"], 0.025, 0.025, aT.shortTermWindow, aT.shortTermStep, "randomforest", "classifier_rf", True)
