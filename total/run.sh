echo "***************************Start detecting and evaluating*******************"
echo "Here is total folder. "
echo "It will start to run collect.py first and then run ARC_evaluate.py. "
echo "****************************************************************************"
echo 1234 | sudo -S python ./Visualize_evaluate/collect.py & gnome-terminal -x bash -c "python ./model/ARC_evaluate.py"
