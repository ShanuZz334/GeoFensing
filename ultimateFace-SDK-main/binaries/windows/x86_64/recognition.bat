setlocal
set PATH=%PATH%;%~dp0;../../../../../ultimateDeepLearning/third_parties/onnxruntime-1.20.0-for-win7-donot-distribute/lib/windows-x64-cpu
recognition.exe ^
    --assets ../../../assets ^
    --image0 "../../../assets/images/macron-0.jpg" ^
    --image1 "../../../assets/images/macron-1.jpg" ^
    --cuda_activation "auto"
endlocal