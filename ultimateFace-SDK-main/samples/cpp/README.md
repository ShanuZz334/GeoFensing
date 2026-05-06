 - [benchmark](benchmark) -> to measure the application performance (speed, memory usage...) on your CPU/GPU.
 - [liveness](liveness) -> [avant-garde](https://www.doubango.org/SDKs/face-liveness/docs/Avant_garde.html#avant-garde), [3d face liveness](https://www.doubango.org/SDKs/face-liveness/docs/3D_passive_liveness.html#d-passive-liveness), [deepfake detection](https://www.doubango.org/SDKs/face-liveness/docs/Deepfake_detection.html#deepfake-detection) and [identity concealment check](https://www.doubango.org/SDKs/face-liveness/docs/Identity_concealment.html#identity-concealment).
 - [recognition](recognition) -> [face recognition check](https://www.doubango.org/SDKs/face-liveness/docs/Face_recognition.html#face-recognition).

<a name="known-issues"></a>
# Known issues #
- On Linux you may get `[CompVSharedLib] Failed to load library with path=<...>libplugin_dl_onnx.so, Error: 0xffffffff`. Make sure to set `LD_LIBRARY_PATH` to add binaries folder to help the loader find all dependencies. You can also run `ldd libplugin_dl_onnx.so` to see which libraries are missing.
- On Linux you may get `'GLIBC_2.27' not found (required by <...>)`. This message means you're using an old glibc version. Update glibc or your OS to Ubuntu 18, Debian Buster... You can check your actual version by running `ldd --version`. 
