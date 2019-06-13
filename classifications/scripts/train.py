import audioTrainTest as aT
aT.featureAndTrain(["../demo/train_COPD","../demo/train_normal"], 0.025, 0.025, aT.shortTermWindow, aT.shortTermStep, "randomforest", "classifier_rf", True)
