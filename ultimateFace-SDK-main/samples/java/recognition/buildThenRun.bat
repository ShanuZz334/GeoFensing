REM using Anaconda with 'tensorflow14' env

REM building
javac @sources.txt -d .

REM Update PATH
setlocal
set PATH=%PATH%;../../../binaries/windows/x86_64;../../../../../ultimateDeepLearning/third_parties/onnxruntime-1.20.0-for-win7-donot-distribute/lib/windows-x64-cpu

REM running
java -Djava.library.path=../../../binaries/windows/x86_64 Recognition --image0 "../../../assets/images/macron-0.jpg" --image1 "../../../assets/images/macron-1.jpg" --threshold 0.35 --assets ../../../assets

endlocal