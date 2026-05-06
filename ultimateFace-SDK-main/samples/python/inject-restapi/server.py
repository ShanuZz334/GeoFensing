from flask import Flask, request
from flask_cors import CORS, cross_origin
import base64, io, numpy as np, json, signal
from PIL import Image
import ultimateFaceSDK as UltFaceSdk

## App ##
app = Flask(__name__)
cors = CORS(app)

## ulimateFace SDK ##

# Defines the default JSON configuration. More information at https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html
ULTFACE_CONFIG = {
    "assets_folder": "../../../assets",
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
    
    "license_token_file": "",
    "license_token_data": ""
}

def ultFaceCheckResult(operation :str, result :UltFaceSdk.UltFaceSdkResult):
    if not result.isOK():
        raise Exception("{} failed -> {}".format(operation, result.phrase()))
    else:
        print("{} : OK -> {}".format(operation,  result.json()))
        
def ultFaceDeInit(sign_num, frame):
    ultFaceCheckResult("DeInit({})".format(sign_num), 
                UltFaceSdk.UltFaceSdkEngine.deInit()
               )

# Initialize the engine (called once)
ultFaceCheckResult("Init", 
            UltFaceSdk.UltFaceSdkEngine.init(json.dumps(ULTFACE_CONFIG))
            )

# Register kill signal
signal.signal(signal.SIGTERM, ultFaceDeInit)

## POST ##
@app.route('/', methods = ['POST'])
@cross_origin()
def virtual_cam_buster():
    assert(request.method == 'POST')
    
    # Get Base64 images
    base64_main = base64.b64decode(request.json['main'])
    base64_aux = base64.b64decode(request.json['aux'])

    # Decode images and convert to RGB24
    image_main = np.array(Image.open(io.BytesIO(base64_main)).convert('RGB'))
    image_aux = np.array(Image.open(io.BytesIO(base64_aux)).convert('RGB'))
    
    # perform injection detection
    # notice the chroma is 'BGR24' instead of 'RGB24' because of OpenCV.
    bytes_main = image_main.tobytes(order='C') # keep a ref using local var and don't let it die
    bytes_aux = image_aux.tobytes(order='C') # keep a ref using local var and don't let it die
    aggressive_mode = 'off' # should be 'off' when the image is from Android/iOS/web, otherwise 'on'. More at https://www.doubango.org/SDKs/face-liveness/docs/Stream_injection_detection.html#aggressive-mode
    result = UltFaceSdk.UltFaceSdkEngine.process_inject(
                UltFaceSdk.UltFaceImageInfoRgbFamily(UltFaceSdk.ULTFACE_SDK_IMAGE_TYPE_RGB24, bytes_main, image_main.shape[1], image_main.shape[0]),
                UltFaceSdk.UltFaceImageInfoRgbFamily(UltFaceSdk.ULTFACE_SDK_IMAGE_TYPE_RGB24, bytes_aux, image_aux.shape[1], image_aux.shape[0]),
                aggressive_mode
            )
    ultFaceCheckResult("Process", result)
    
    return result.json()
    
    
    
    