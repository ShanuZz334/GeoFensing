- [Dependencies](#dependencies)
  - [Debugging missing dependencies](#dependencies-debugging)
- [GPGPU acceleration](#gpu-acceleration)
- [Pre-built binaries](#prebuilt)
- [Building](#building)
- [Usage](#testing-usage)
- [Examples](#testing-examples)

This application is a reference implementation for developers to show how to use the [C++ API](https://www.doubango.org/SDKs/face-liveness/docs/cpp-api.html) and could
be used to easily test the [3D liveness detection module](https://www.doubango.org/SDKs/face-liveness/docs/3D_passive_liveness.html). 
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

You'll need [CMake](https://cmake.org/) to build this sample.

- Create build folder and move into it: `mkdir build && cd build`

To generate the build files:
- Windows (Visual Studio files): `cmake .. -DCMAKE_BUILD_TYPE=Release`
- Linux (Makefile): `cmake .. -G"Unix Makefiles" -DCMAKE_BUILD_TYPE=Release`

To build the project:
- Windows: Open the VS solution and build the projet
- Linux: Run `make` to build the project 

<a name="testing-usage"></a>
# Usage #

```
liveness \
      --assets <path-to-assets-folder> \
      --image <path-to-image-to-process> \
      [--parallel <whether-to-enable-parallel-mode:true/false>] \
      [--cuda_activation <cuda-activation:auto/on/off>] \
      [--tokenfile <path-to-license-token-file>] \
      [--tokendata <base64-license-token-data>]
```
Options surrounded with **[]** are optional.
- `--assets` Path to the [assets](../../../assets) folder containing the configuration files and models. More information at https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html#assets-folder.
- `--image` Path to the image (JPEG/PNG/BMP...) to process.
- `--parallel` Whether to enabled the parallel mode. More info at https://www.doubango.org/SDKs/face-liveness/docs/Parallel_processing.html. **Default: true**.
- `--cuda_activation` CUDA activation mode. More info at https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html#cuda-activation. **Default: "auto"**.
- `--tokenfile` Path to the file containing the base64 license token if you have one. If not provided, then the application will act like a trial version. Default: *null*. More information at https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html#license-token-file.
- `--tokendata` Base64 license token if you have one. If not provided, then the application will act like a trial version. Default: *null*. More information at https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html#license-token-data.
- 
<a name="testing-examples"></a>
# Examples #

- On **Linux x86_64**, you may use the next command:
```
LD_LIBRARY_PATH=../../../binaries/linux/x86_64:$LD_LIBRARY_PATH ./liveness \
    --image "../../../assets/images/genuine.jpg" \
    --assets ../../../assets \
    --cuda_activation "auto" \
    --parallel false
```

- On **Windows x86_64**, you may use the next command:
```
liveness.exe ^
    --image "../../../assets/images/genuine.jpg" ^
    --assets ../../../assets ^
    --cuda_activation "auto" ^
    --parallel false
```
you can also use [binaries/windows/x86_64/liveness.bat](../../../binaries/windows/x86_64/liveness.bat) to make your life easier.

