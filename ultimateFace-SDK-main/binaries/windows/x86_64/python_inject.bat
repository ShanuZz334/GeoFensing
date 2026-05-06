setlocal
set PYTHONPATH=%PYTHONPATH%;.;../../../python
set PATH=%PATH%;%~dp0;../../../../../ultimateDeepLearning/third_parties/onnxruntime-1.20.0-for-win7-donot-distribute/lib/windows-x64-cpu
python ../../../samples/python/inject/inject.py --camera 0 --assets ../../../assets
endlocal