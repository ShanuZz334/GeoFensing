setlocal
set PYTHONPATH=%PYTHONPATH%;.;../../../python
set PATH=%PATH%;%~dp0;../../../../../ultimateDeepLearning/third_parties/onnxruntime-1.20.0-for-win7-donot-distribute/lib/windows-x64-cpu
python ../../../samples/python/liveness/liveness.py --image "../../../assets/images/genuine.jpg" --assets ../../../assets
endlocal