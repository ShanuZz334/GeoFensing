setlocal
set PYTHONPATH=%PYTHONPATH%;.;../../../python
set PATH=%PATH%;%~dp0;../../../../../ultimateDeepLearning/third_parties/onnxruntime-1.20.0-for-win7-donot-distribute/lib/windows-x64-cpu
python ../../../samples/python/recognition/recognition.py --image0 "../../../assets/images/macron-0.jpg" --image1 "../../../assets/images/macron-1.jpg" --assets ../../../assets
endlocal