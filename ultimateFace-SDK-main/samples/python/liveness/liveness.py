'''
    Copyright (C) 2011-2025 Doubango Telecom <https://www.doubango.org>
    File author: Mamadou DIOP (Doubango Telecom, France).
    License: For non commercial use only.
    Source code: https://github.com/DoubangoTelecom/ultimateFace-SDK
    WebSite: https://www.doubango.org/webapps/face-liveness

    https://github.com/DoubangoTelecom/ultimateFace-SDK/blob/master/samples/python/liveness/README.md
	Usage: 
		liveness.py \
			--image <path-to-image-to-process> \
			--assets <path-to-assets-folder>\
            [--tokenfile <path-to-license-token-file>] \
			[--tokendata <base64-license-token-data>]
	Example:
		python ../../../samples/python/liveness/liveness.py --image "../../../assets/images/genuine.jpg" --assets ../../../assets
'''

import ultimateFaceSDK as UltFaceSdk
import os, argparse, json

# Defines the default JSON configuration. More information at https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html
JSON_CONFIG = {    
    "debug_level": "info",
    "debug_write_input_image_enabled": False,
    "debug_internal_data_path": ".",
    
    "gpu_ctrl_memory_enabled": True,
    "num_threads": -1,
    "max_latency": -1,
    "max_batchsize": -1,
    "asm_enabled": True,
    "intrin_enabled": True,
    "cuda_activation": "auto",
    "backend": "onnx",
    
    "detect_target_size": 640,
    "detect_size_threshold": 16,
    "detect_score_threshold": 0.5,
    "detect_iou_threshold": 0.4,
    "detect_topk": 1000,
    
    "avantgarde_score_threshold": 0.5,
    
    "liveness_genuine_threshold": 0.5,
    "liveness_disputed_threshold": 0.4,
    
    "deepfake_genuine_threshold": 0.5,
    
    "disguise_genuine_threshold": 0.5,
    
    "inject_similarity_threshold": 0.35,
    "inject_genuine_threshold": 0.90,
    "inject_smartpass_enabled": True,
}

# Check result
def checkResult(operation, result):
    if not result.isOK():
        raise Exception("{} failed -> {}".format(operation, result.phrase()))
    else:
        print("{} : OK -> {}".format(operation,  result.json()))

# Entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
    This is the liveness sample using python language
    """)

    parser.add_argument("--image", required=True, type=str, help="Path to the image to process")
    parser.add_argument("--assets", required=False, type=str, default="../../../assets", help="Path to the assets folder")
    parser.add_argument("--tokenfile", required=False, type=str, default="", help="Path to license token file")
    parser.add_argument("--tokendata", required=False, type=str, default="", help="Base64 license token data")

    args = parser.parse_args()

    # Check if image exist
    if not os.path.isfile(args.image):
        raise Exception("File doesn't exist: {}".format(args.image))

    # Update JSON options using values from the command args
    JSON_CONFIG["assets_folder"] = args.assets
    JSON_CONFIG["license_token_file"] = args.tokenfile
    JSON_CONFIG["license_token_data"] = args.tokendata

    # Initialize the engine (called once)
    checkResult("Init", 
                UltFaceSdk.UltFaceSdkEngine.init(json.dumps(JSON_CONFIG))
               )

    # Process (called as many times as needed)
    # Please note that the first time you call this function all deep learning models will be loaded 
    # and initialized which means it will be slow. In your application you've to initialize the engine
    # once and do all the processing you need, then deinitialize it.
    with open(args.image, 'rb') as file:
        checkResult("Process",
                    UltFaceSdk.UltFaceSdkEngine.process_liveness(
                        UltFaceSdk.UltFaceImageInfoCompressed(file.read(), os.fstat(file.fileno()).st_size)
                    )
            )

    # Press any key to exit
    input("\nPress Enter to exit...\n") 

    # DeInit the engine (called once)
    checkResult("DeInit", 
                UltFaceSdk.UltFaceSdkEngine.deInit()
               )
    
    