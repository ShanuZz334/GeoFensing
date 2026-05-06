'''
    Copyright (C) 2011-2025 Doubango Telecom <https://www.doubango.org>
    File author: Mamadou DIOP (Doubango Telecom, France).
    License: For non commercial use only.
    Source code: https://github.com/DoubangoTelecom/ultimateFace-SDK
    WebSite: https://www.doubango.org/webapps/face-recognition

    https://github.com/DoubangoTelecom/ultimateFace-SDK/blob/master/samples/python/recognition/README.md
	Usage: 
		recognition.py \
			--image0 <path-to-first-image-to-process> \
            --image1 <path-to-second-image-to-process> \
			--assets <path-to-assets-folder>\
            [--tokenfile <path-to-license-token-file>] \
			[--tokendata <base64-license-token-data>]
	Example:
		python ../../../samples/python/recognition/recognition.py --image0 "../../../assets/images/macron-0.jpg" --image1 "../../../assets/images/macron-1.jpg" --assets ../../../assets
'''

import ultimateFaceSDK as UltFaceSdk
import os, argparse, json, numpy as np

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
    "detect_topk": 1,
}

# Check result
def checkResult(operation, result, quiet=False):
    if not result.isOK():
        raise Exception("{} failed -> {}".format(operation, result.phrase()))
    elif not quiet:
        print("{} : OK -> {}".format(operation,  result.json()))

# Entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
    This is the recognition sample using python language
    """)

    parser.add_argument("--image0", required=True, type=str, help="Path to the first image to process")
    parser.add_argument("--image1", required=True, type=str, help="Path to the second image to process")
    parser.add_argument("--assets", required=False, type=str, default="../../../assets", help="Path to the assets folder")
    parser.add_argument("--threshold", required=False, type=float, default=0.35, help="Similarity threshold")
    parser.add_argument("--tokenfile", required=False, type=str, default="", help="Path to license token file")
    parser.add_argument("--tokendata", required=False, type=str, default="", help="Base64 license token data")

    args = parser.parse_args()

    # Check if both images exist
    for image in [args.image0, args.image1]:
        if not os.path.isfile(image):
            raise Exception("File doesn't exist: {}".format(image))

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
    embeddings = []
    for i, image in enumerate([args.image0, args.image1]):
        result = None
        with open(image, 'rb') as file:
            # extract embeddings for all faces in the image
            result = UltFaceSdk.UltFaceSdkEngine.process_recognition(
                            UltFaceSdk.UltFaceImageInfoCompressed(file.read(), os.fstat(file.fileno()).st_size)
                        )
            checkResult("Process", result, quiet=True)
            # parse JSON result
            faces = json.loads(result.json())["faces"]
            # make sure at least 1 face is in the image
            if (len(faces) == 0):
                raise Exception('No face in image #{}'.format(i))
            # save the embeddings of the largest face only (ignore other faces)
            embeddings += [faces[0], ]

    # sanity check
    assert(len(embeddings) == 2 and len(embeddings[0]) == len(embeddings[1]))

    # Compute Similarity
    similarity = np.array(embeddings[0]).dot(np.array(embeddings[1]).T)
    print("Similarity: {:.2f}. Same person: {}".format(similarity, (similarity >= args.threshold)))

    # Press any key to exit
    input("\nPress Enter to exit...\n") 

    # DeInit the engine (called once)
    checkResult("DeInit", 
                UltFaceSdk.UltFaceSdkEngine.deInit()
               )
    
    