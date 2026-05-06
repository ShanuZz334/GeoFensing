setlocal
set PATH=%PATH%;%~dp0;../../../../../ultimateDeepLearning/third_parties/onnxruntime-1.20.0-for-win7-donot-distribute/lib/windows-x64-cpu
benchmark.exe ^
    --assets ../../../assets ^
    --image "../../../assets/images/genuine.jpg" ^
    --loops 20 ^
    --cuda_activation "auto" ^
    --parallel true
endlocal