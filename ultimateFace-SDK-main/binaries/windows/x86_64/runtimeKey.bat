setlocal
set PATH=%PATH%;%~dp0;../../../../../ultimateDeepLearning/third_parties/onnxruntime-1.20.0-for-win7-donot-distribute/lib/windows-x64-cpu
runtimeKey.exe ^
    --json true ^
    --assets ../../../assets
endlocal