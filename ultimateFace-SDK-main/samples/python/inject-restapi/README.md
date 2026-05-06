- [Dependencies](#dependencies)
  - [Debugging missing dependencies](#dependencies-debugging)
- [GPGPU acceleration](#gpu-acceleration)
- [Prerequisite](#prerequisite)
- [Run](#run)
- [Know issues](#testing-know-issues)

This application is a reference implementation for developers to show how to use the Python API and could
be used to easily test [Stream injection (Virtual Camera) detection module](https://www.doubango.org/SDKs/face-liveness/docs/Stream_injection_detection.html). The Python API is a wrapper around the C++ API defined at [https://www.doubango.org/SDKs/face-liveness/docs/cpp-api.html](https://www.doubango.org/SDKs/face-liveness/docs/cpp-api.html).

If you don't want to build this sample and is looking for a quick way to check the accuracy, then try
our online webapp demo at https://www.doubango.org/webapps/face-liveness.

This sample is open source and doesn't require registration or license key.

<a name="dependencies"></a>
# Dependencies #
**The SDK is developed in C++11** and you'll need **glibc 2.27+** on *Linux* and **[Microsoft Visual C++ 2015 Redistributable(x64) - 14.0.24123](https://www.microsoft.com/en-us/download/details.aspx?id=52685)** (any later version is ok) on *Windows*.  **You most likely already have these dependencies on your machine** as almost every program requires it.

<a name="dependencies-debugging"></a>
## Debugging missing dependencies ##
To check if all dependencies are present:
- **Windows x86_64:** Use [Dependency Walker](https://www.dependencywalker.com/) on [binaries/windows/x86_64/ultimateFaceSDK.dll](../../../binaries/windows/x86_64/ultimateFaceSDK.dll) and [binaries/windows/x86_64/plugin_dl_onnx.dll](../../../binaries/windows/x86_64/plugin_dl_onnx.dll).
- **Linux x86_64:** Use `ldd <your-shared-lib>` on [binaries/linux/x86_64/libultimateFaceSDK.so](../../../binaries/linux/x86_64/libultimateFaceSDK.so) and [binaries/linux/x86_64/libplugin_onnx.so](../../../binaries/linux/x86_64/libplugin_dl_onnx.so).

<a name="gpu-acceleration"></a>
# GPGPU acceleration #
- On x86-64, GPGPU acceleration is disabled by default. Check [here](../../../GPGPU.md) for more information on how to enable it.

<a name="prerequisite"></a>
# Prerequisite #

 - [**You must build the Python extension**](../../../python/README.md) before trying to run this sample. More information on how to build the extension could be found [here](../../../python/README.md)
 - The client (html page) must be hosted on a web server. if you don't have one, then use https://www.doubango.org/SDKs/face-liveness/inject-sample.
 - If the server runs on your local machine, then you have to tell Chrome to trust `localhost:9001` as explained [here](https://medium.com/@Carmichaelize/enabling-the-microphone-camera-in-chrome-for-local-unsecure-origins-9c90c3149339).

<a name="run"></a>
# Run #

## Server run

On Windows:
```
setlocal
set PYTHONPATH=%PYTHONPATH%;.;../../../python;../../../binaries/windows/x86_64
set PATH=%PATH%;%~dp0;../../../binaries/windows/x86_64
python -m flask --app server run --host=0.0.0.0 --port=9100
endlocal
```
or execute [run.bat](run.bat) to make your lifer easier.

On Linux:
```
PYTHONPATH=$PYTHONPATH:.:../../../python:../../../binaries/linux/x86_64 \
LD_LIBRARY_PATH=.:$LD_LIBRARY_PATH:../../../binaries/linux/x86_64 \
python -m flask --app server run --host=0.0.0.0 --port=9100
```

## Client

You can either host the [source](client) on your own web server or use https://www.doubango.org/SDKs/face-liveness/inject-sample

<a name="testing-know-issues"></a>
# Know issues #
If you get `undefined symbol: PyUnicode_FromFormat` error message, then make sure you're using Python 3 and same version as the one used to buid the extension. We tested the code on version **3.6.9** (Windows 8), **3.6.8** (Ubuntu 18) and **3.7.3** (Raspbian Buster). Run `python --version` to print your Python version. You may use `python3` instead of `python` to make sure you're using version 3.


