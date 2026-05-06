- [Dependencies](#dependencies)
  - [Debugging missing dependencies](#dependencies-debugging)
- [GPGPU acceleration](#gpu-acceleration)
- [Pre-built binaries](#prebuilt)
- [Building](#building)
- [Usage](#testing-usage)
- [Examples](#testing-examples)
- [Know issues](#testing-know-issues)

This application is a reference implementation for developers to show how to use the Java API and could
be used to easily test the [3D liveness detection module](https://www.doubango.org/SDKs/face-liveness/docs/3D_passive_liveness.html). The Java API is a wrapper around the C++ API defined at [https://www.doubango.org/SDKs/face-liveness/docs/cpp-api.html](https://www.doubango.org/SDKs/face-liveness/docs/cpp-api.html).

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

<a name="prebuilt"></a>
# Pre-built binaries #
If you don't want to build this sample by yourself, then use the pre-built C++ versions:
 - Windows x86_64: [liveness.exe](../../../binaries/windows/x86_64/liveness.exe) under [binaries/windows/x86_64](../../../binaries/windows/x86_64)
 - Linux x86_64: [liveness](../../../binaries/linux/x86_64/liveness) under [binaries/linux/x86_64](../../../binaries/linux/x86_64).

<a name="building"></a>
# Building #

This sample contains [a single Java source file](Liveness.java).

You have to navigate to the current folder (`ultimateFace-SDK/samples/java/liveness`) before trying the next commands:
```
cd ultimateFace-SDK/samples/java/liveness
```

Here is how to build the file using `javac`:
```
javac @sources.txt -d .
```

<a name="testing-usage"></a>
# Usage #

`Liveness` is a command line application with the following usage:
```
Liveness \
      --assets <path-to-assets-folder> \
      --image <path-to-image-to-process> \
      [--tokenfile <path-to-license-token-file>] \
      [--tokendata <base64-license-token-data>]
```
Options surrounded with **[]** are optional.
- `--assets` Path to the [assets](../../../assets) folder containing the configuration files and models. More information at https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html#assets-folder.
- `--image` Path to the image (JPEG/PNG/BMP...) to process.
- `--tokenfile` Path to the file containing the base64 license token if you have one. If not provided, then the application will act like a trial version. Default: *null*. More information at https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html#license-token-file.
- `--tokendata` Base64 license token if you have one. If not provided, then the application will act like a trial version. Default: *null*. More information at https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html#license-token-data.

<a name="testing-examples"></a>
## Examples ##
You'll need to build the sample as explained [above](#building).

You have to navigate to the current folder (`ultimateFace-SDK/samples/java/liveness`) before trying the next commands:
```
cd ultimateFace-SDK/samples/java/liveness
```

- On **Linux x86_64**, you may use the next command:
```
LD_LIBRARY_PATH=../../../binaries/linux/x86_64:$LD_LIBRARY_PATH \
java Liveness --image "../../../assets/images/genuine.jpg" --assets ../../../assets
```

- On **Windows x86_64**, you may use the next command:
```
setlocal
set PATH=%PATH%;../../../binaries/windows/x86_64
java Liveness --image "../../../assets/images/genuine.jpg" --assets ../../../assets
endlocal
```
To make your life easier, run [run.bat](run.bat) to test on Windows. You can edit the file using Notepad to change the parameters.

