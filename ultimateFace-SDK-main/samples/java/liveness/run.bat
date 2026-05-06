setlocal
set PATH=%PATH%;../../../binaries/windows/x86_64;../../../../../ultimateDeepLearning/third_parties/onnxruntime-1.20.0-for-win7-donot-distribute/lib/windows-x64-cpu
java -Djava.library.path=../../../binaries/windows/x86_64 Liveness --image "../../../assets/images/genuine.jpg" --assets ../../../assets
endlocal