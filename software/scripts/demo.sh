echo "***************************This is a demo shell*****************************"
echo "The test_COPD folder contains respiratory sound files of COPD patients."
echo "We will demostrate classifying these audio files by our model. "
echo "Our model is trained by random forest algorithm and the accuracy is roughly 90%."
echo "The demo will start in 5 seconds..."
echo "****************************************************************************"
sleep 5
python audioAnalysis.py classifyFolder -i ../COPD_test/  --model randomforest --classifier classifier_rf --details

