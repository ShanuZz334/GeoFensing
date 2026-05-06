The deep learning models used in this SDK were developped using [Pytorch](https://pytorch.org/) and [Tensorflow](https://www.tensorflow.org/). All models were exported to [ONNX](https://onnx.ai/) for inferencing. 
We use [ONNX Runtime 1.21.0](https://github.com/microsoft/onnxruntime/releases/tag/v1.21.0) a.k.a **ONNX RT** as inference engine. The SDK should work with any later version but we'll only provide support if you're using 1.21.0.

This short guide explain how to enable GPGPU acceleration for NVIDIA GPUs. We'll focus on **Ubuntu 20.04** but it's easy to adapt the guide for Windows.

The SDK is shipped with the CPU version of [ONNX RT 1.21.0](https://github.com/microsoft/onnxruntime/releases/tag/v1.21.0) in the [binaries folder](binaries). The GPU versions are too large to be pushed on Github. 
You'll have to pull the GPU version of ONNX RT to replace the CPU version.
```
cd binaries/linux/x86_64
wget https://github.com/microsoft/onnxruntime/releases/download/v1.21.0/onnxruntime-linux-x64-gpu-1.21.0.tgz
tar -xf onnxruntime-linux-x64-gpu-1.21.0.tgz
cp -rf onnxruntime-linux-x64-gpu-1.21.0/lib/* .
```

[ONNX Runtime 1.21.0](https://github.com/microsoft/onnxruntime/releases/tag/v1.21.0) requires **CUDA 12.x** and **cuDNN 9.x** according to https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html.
We tested both cuDNN 9.8 and 9.11 and had `segmentation fault` with the later. So, we highly recommend using cuDNN 9.8 and making sure no other version is installed on your machine.

Using Anaconda on **Ubuntu 20.04**:
```
conda create -n test_env_onnx python=3.10
conda activate test_env_onnx

wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run
sudo sh cuda_12.1.0_530.30.02_linux.run

wget https://developer.download.nvidia.com/compute/cudnn/9.8.0/local_installers/cudnn-local-repo-ubuntu2004-9.8.0_1.0-1_amd64.deb
sudo dpkg -i cudnn-local-repo-ubuntu2004-9.8.0_1.0-1_amd64.deb
sudo cp /var/cudnn-local-repo-ubuntu2004-9.8.0/cudnn-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cudnn
```
