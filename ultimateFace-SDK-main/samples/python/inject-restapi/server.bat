setlocal
set PYTHONPATH=%PYTHONPATH%;.;../../../python;../../../binaries/windows/x86_64
set PATH=%PATH%;%~dp0;../../../binaries/windows/x86_64;../../../../../ultimateDeepLearning/third_parties/onnxruntime-1.20.0-for-win7-donot-distribute/lib/windows-x64-cpu
python -m flask --app server run --host=0.0.0.0 --port=9100
endlocal