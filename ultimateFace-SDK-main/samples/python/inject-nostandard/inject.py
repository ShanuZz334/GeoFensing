'''
    Copyright (C) 2011-2025 Doubango Telecom <https://www.doubango.org>
    File author: Mamadou DIOP (Doubango Telecom, France).
    License: For non commercial use only.
    Source code: https://github.com/DoubangoTelecom/ultimateFace-SDK
    WebSite: https://www.doubango.org/webapps/face-liveness

    https://github.com/DoubangoTelecom/ultimateFace-SDK/blob/master/samples/python/liveness/README.md
	Usage: 
		inject.py \
			--assets <path-to-assets-folder>\
            [--camera <camera-index>]
            [--tokenfile <path-to-license-token-file>] \
			[--tokendata <base64-license-token-data>]
	Example:
		python ../../../samples/python/inject/inject.py --assets ../../../assets --camera 0
'''

import ultimateFaceSDK as UltFaceSdk
import argparse, json, cv2, numpy as np

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
    
    "inject_similarity_threshold": 0.35,
    "inject_genuine_threshold": 0.90,
    "inject_smartpass_enabled": True,
}

WINDOW_TITLE = "Stream inject (virtual camera) detection"

STEREO_SIZES = {
    'main': { 'width': 1280, 'height': 720 },
    'aux': { 'width': 640, 'height': 480 },
}

def checkResult(operation :str, result :UltFaceSdk.UltFaceSdkResult):
    if not result.isOK():
        raise Exception("{} failed -> {}".format(operation, result.phrase()))
    else:
        print("{} : OK -> {}".format(operation,  result.json()))
        
def draw(
        main :np.ndarray, 
        text :str, 
        aux :np.ndarray = None,
        font=cv2.FONT_HERSHEY_PLAIN,
        pos=(0, 0),
        font_scale=2,
        font_thickness=2,
        text_color=(0, 0, 0),
        text_color_bg=(0, 255, 255)
    ) -> np.ndarray:
    
    x, y = pos
    text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
    text_w, text_h = text_size
    image = np.copy(main) # must not alter 'main'
    image = cv2.rectangle(image, pos, (x + text_w, y + text_h), text_color_bg, -1)
    image = cv2.putText(image, text, (x, y + text_h + font_scale - 1), font, font_scale, text_color, font_thickness)
    if not aux is None:
        scale = (main.shape[1] * 0.1) / aux.shape[1]
        img = cv2.resize(aux, None, fx=scale, fy=scale)
        image[
              image.shape[0]-img.shape[0]:, 0:img.shape[1],...
        ] = img
        
    return image
        
def openCamera(target :str, camera :int=0) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(camera, cv2.CAP_ANY)
    cap.set(cv2.CAP_PROP_FORMAT, -1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, STEREO_SIZES[target]['width'])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, STEREO_SIZES[target]['height'])
    if not cap.isOpened():
        raise Exception('Failed to open camera at index {}'.format(camera))
    return cap
        
def takeAuxImage(camera :int=0) -> np.ndarray:
    cap = openCamera('aux', camera)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise Exception('Failed to read from camera at index {}'.format(camera))
    return frame
        
# Entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
    This is the liveness sample using python language
    """)

    parser.add_argument("--assets", required=False, type=str, default="../../../assets", help="Path to the assets folder")
    parser.add_argument("--camera", required=False, type=int, default=0, help="Camera index")
    parser.add_argument("--tokenfile", required=False, type=str, default="", help="Path to license token file")
    parser.add_argument("--tokendata", required=False, type=str, default="", help="Base64 license token data")

    args = parser.parse_args()

    # Update JSON options using values from the command args
    JSON_CONFIG["assets_folder"] = args.assets
    JSON_CONFIG["license_token_file"] = args.tokenfile
    JSON_CONFIG["license_token_data"] = args.tokendata

    # Initialize the engine (called once)
    checkResult("Init", 
                UltFaceSdk.UltFaceSdkEngine.init(json.dumps(JSON_CONFIG))
               )

    # "main" loop
    cap = openCamera('main', args.camera)
    while(cap.isOpened()):
        ret, main = cap.read()
        if not ret:
            raise Exception('Failed to read from camera at index {}'.format(args.camera))
        
        # display main image
        cv2.imshow(WINDOW_TITLE, draw(main, 'Press any key to process a frame. Or \'q\' to exit'))
        # wait for any key
        k = cv2.waitKey(1)
        if k != -1:
            cv2.imshow(WINDOW_TITLE, draw(main, 'Processing...'))
            cv2.waitKey(1)
            if k & 0xFF == ord('q'): break
            # close the camera
            cap.release()
            # take aux image
            aux = takeAuxImage(args.camera)
            
            # perform injection detection
            # notice the chroma is 'BGR24' instead of 'RGB24' because of OpenCV.
            bytes_main = main.tobytes(order='C') # keep a ref using local var and don't let it die
            bytes_aux = aux.tobytes(order='C') # keep a ref using local var and don't let it die
            aggressive_mode = 'on' # should be 'off' when the image is from Android/iOS/web, otherwise 'on'. More at https://www.doubango.org/SDKs/face-liveness/docs/Stream_injection_detection.html#aggressive-mode
            result = UltFaceSdk.UltFaceSdkEngine.process_inject(
                        UltFaceSdk.UltFaceImageInfoRgbFamily(UltFaceSdk.ULTFACE_SDK_IMAGE_TYPE_BGR24, bytes_main, main.shape[1], main.shape[0]),
                        UltFaceSdk.UltFaceImageInfoRgbFamily(UltFaceSdk.ULTFACE_SDK_IMAGE_TYPE_BGR24, bytes_aux, aux.shape[1], aux.shape[0]),
                        aggressive_mode
                    )
            checkResult("Process", result)
            # display result
            cv2.imshow(WINDOW_TITLE, draw(main, 'Result: {}. Press any key to resume. Or \'q\' to exit'.format(json.loads(result.json())['inject_code'].split('_')[1]), aux))
            
            # wait for any key before resuming
            if cv2.waitKey(0) & 0xFF != ord('q'):
                # resume capture
                cap = openCamera('main', args.camera)
            else:
                break

    cap.release()
        
    cv2.destroyAllWindows()

    # DeInit the engine (called once)
    checkResult("DeInit", 
                UltFaceSdk.UltFaceSdkEngine.deInit()
               )
    
    