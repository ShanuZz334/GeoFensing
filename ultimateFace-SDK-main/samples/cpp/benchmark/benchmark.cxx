/* Copyright (C) 2011-2025 Doubango Telecom <https://www.doubango.org>
* File author: Mamadou DIOP (Doubango Telecom, France).
* License: For non commercial use only.
* Source code: https://github.com/DoubangoTelecom/ultimateFace-SDK
* WebSite: https://www.doubango.org/webapps/face-liveness
*/
#include <ULTFACE-SDK-API-PUBLIC.h>

#include <chrono>
#include <vector>
#include <algorithm>
#include <random>
#include <mutex>
#include <map>
#include <sys/stat.h>
#include <condition_variable>

// Not part of the SDK, used to decode images -> https://github.com/nothings/stb
#define STB_IMAGE_IMPLEMENTATION
#define STB_IMAGE_STATIC
#include "stb_image.h"

using namespace UltFace;

struct FileInfo {
	void* uncompressedData = nullptr;
	size_t width = 0;
	size_t height = 0;
	ULTFACE_SDK_IMAGE_TYPE type;
	virtual ~FileInfo() {
		release();
	}
	void release() {
		if (uncompressedData) {
			free(uncompressedData);
			uncompressedData = nullptr;
		}
	}
	inline bool isValid() const {
		return (uncompressedData != nullptr && width && height);
	}
};

/*
* Parallel callback function used for notification. Not mandatory.
* More info about parallel delivery: https://www.doubango.org/SDKs/kyc-documents-verif/docs/Parallel_versus_sequential_processing.html
*/
static size_t parallelNotifCount = 0;
static std::condition_variable parallelNotifCondVar;
class MyUltFaceSdkParallelDeliveryCallback : public UltFaceSdkParallelDeliveryCallback {
public:
	MyUltFaceSdkParallelDeliveryCallback(const void* userData) : m_pMyDummyData(userData) {}
	virtual void onNewResult(const UltFaceSdkResult* result) const override {
		// Use m_pMyDummyData here if you want
		ULTFACE_SDK_ASSERT(result != nullptr);
		const std::string& json = result->json();
		// Printing to the console could be very slow and delayed -> stop displaying the result as soon as all faces are processed
		ULTFACE_SDK_PRINT_INFO("MyUltFaceSdkParallelDeliveryCallback::onNewResult(%d, %s, %zu): %s",
			result->code(),
			result->phrase(),
			++parallelNotifCount,
			!json.empty() ? json.c_str() : "{}"
		);
		parallelNotifCondVar.notify_one();
	}
private:
	const void* m_pMyDummyData;
};

static void printUsage(const std::string& message = "");
static bool parseArgs(int argc, char *argv[], std::map<std::string, std::string >& values);
static bool readFile(const std::string& path, FileInfo& file);
static bool checkResult(const UltFaceSdkResult& result);

// Asset manager used on Android to files in "assets" folder
#if ULTFACE_SDK_OS_ANDROID 
#	define ASSET_MGR_PARAM() __sdk_android_assetmgr, 
#else
#	define ASSET_MGR_PARAM() 
#endif /* ULTFACE_SDK_OS_ANDROID */

// Configuration for the deep learning engine
static const char* __jsonConfig =
"{"
"\"debug_level\": \"info\","
"\"debug_write_input_image_enabled\": false,"
"\"debug_internal_data_path\": \".\","
""
"\"gpu_ctrl_memory_enabled\": true,"
"\"num_threads\": -1,"
"\"max_latency\": -1,"
"\"max_batchsize\": -1,"
"\"asm_enabled\": true,"
"\"intrin_enabled\": true,"
"\"cuda_activation\": \"auto\","
"\"backend\": \"onnx\","
""
"\"detect_target_size\": 640,"
"\"detect_size_threshold\": 16,"
"\"detect_score_threshold\": 0.5,"
"\"detect_iou_threshold\": 0.4,"
"\"detect_topk\": 1000,"
""
"\"avantgarde_score_threshold\": 0.5,"
""
"\"liveness_genuine_threshold\": 0.5,"
"\"liveness_disputed_threshold\": 0.4,"
""
"\"deepfake_genuine_threshold\": 0.5,"
""
"\"disguise_genuine_threshold\": 0.5,"
""
"\"inject_similarity_threshold\": 0.35,"
"\"inject_genuine_threshold\": 0.90,"
"\"inject_smartpass_enabled\": true"
;

int main(int argc, char *argv[])
{
	// local variables
	UltFaceSdkResult result;
	MyUltFaceSdkParallelDeliveryCallback parallelDeliveryCallbackCallback(nullptr);
	std::string assetsFolder, licenseTokenData, licenseTokenFile;
	std::string cudaActivation = "auto";
	bool isParallelDeliveryEnabled = true;
	std::string imagePath;
	size_t loopsCount = 20;

	// Parsing args
	std::map<std::string, std::string > args;
	if (!parseArgs(argc, argv, args)) {
		printUsage();
		return -1;
	}
	if (args.find("--image") == args.end()) {
		printUsage("--image required");
		return -1;
	}
	if (args.find("--assets") == args.end()) {
		printUsage("--assets required");
		return -1;
	}
	imagePath = args["--image"];

	if (args.find("--loops") != args.end()) {
		const int loops = std::atoi(args["--loops"].c_str());
		if (loops < 1) {
			printUsage("--loops must be within [1, inf]");
			return -1;
		}
		loopsCount = static_cast<size_t>(loops);
	}

	if (args.find("--parallel") != args.end()) {
		isParallelDeliveryEnabled = (args["--parallel"].compare("true") == 0);
	}
	if (args.find("--assets") != args.end()) {
		assetsFolder = args["--assets"];
#if defined(_WIN32)
		std::replace(assetsFolder.begin(), assetsFolder.end(), '\\', '/');
#endif
	}
	if (args.find("--cuda_activation") != args.end()) {
		cudaActivation = args["--cuda_activation"];
	}

	if (args.find("--tokenfile") != args.end()) {
		licenseTokenFile = args["--tokenfile"];
#if defined(_WIN32)
		std::replace(licenseTokenFile.begin(), licenseTokenFile.end(), '\\', '/');
#endif
	}
	if (args.find("--tokendata") != args.end()) {
		licenseTokenData = args["--tokendata"];
	}


	// Update JSON config
	std::string jsonConfig = __jsonConfig;
	if (!assetsFolder.empty()) {
		jsonConfig += std::string(",\"assets_folder\": \"") + assetsFolder + std::string("\"");
	}
	if (!cudaActivation.empty()) {
		jsonConfig += std::string(",\"cuda_activation\": \"") + cudaActivation + std::string("\"");
	}
	if (!licenseTokenFile.empty()) {
		jsonConfig += std::string(",\"license_token_file\": \"") + licenseTokenFile + std::string("\"");
	}
	if (!licenseTokenData.empty()) {
		jsonConfig += std::string(",\"license_token_data\": \"") + licenseTokenData + std::string("\"");
	}

	jsonConfig += "}"; // end-of-config

	// Read input file
	FileInfo file;
	if (!readFile(imagePath, file) || !file.isValid()) {
		ULTFACE_SDK_PRINT_FATAL("Can't read %s", imagePath.c_str());
		return -1;
	}

	// Function to wait until parallel callback is called
	auto funcWaitPtr = [&](const size_t& count) -> void {
		if (isParallelDeliveryEnabled) {
			static std::mutex parallelNotifMutex;
			std::unique_lock<std::mutex > lk(parallelNotifMutex);
			parallelNotifCondVar.wait_for(lk,
				std::chrono::milliseconds(3 * 60 * 1000), // maximum number of millis to wait for before giving up, must never wait this long
				[&count] { return (parallelNotifCount == count); }
			);
		}
		else {
			parallelNotifCount = count;
		}
	};

	// Init
	ULTFACE_SDK_PRINT_INFO("Starting liveness sample...");
	ULTFACE_SDK_ASSERT(checkResult(UltFaceSdkEngine::init(
		ASSET_MGR_PARAM()
		jsonConfig.c_str(),
		isParallelDeliveryEnabled ? &parallelDeliveryCallbackCallback : nullptr
	)));

	// WarmUp
	// We load the models into the memory the first time the inference is called which
	// means it'll be very slow.
	ULTFACE_SDK_PRINT_INFO("Starting warmup...");
	auto imageInfo = UltFaceImageInfoRgbFamily(file.type, file.uncompressedData, file.width, file.height);
	ULTFACE_SDK_ASSERT(checkResult(result = UltFaceSdkEngine::process_liveness(
		&imageInfo
	)));
	funcWaitPtr(1);
	ULTFACE_SDK_PRINT_INFO("Warmup done.");

	// Processing
	ULTFACE_SDK_PRINT_INFO("Starting processing...");
	const std::chrono::high_resolution_clock::time_point timeStart = std::chrono::high_resolution_clock::now();
	for (size_t i = 0; i < loopsCount; ++i) {
		imageInfo = UltFaceImageInfoRgbFamily(file.type, file.uncompressedData, file.width, file.height);
		ULTFACE_SDK_ASSERT(checkResult(result = UltFaceSdkEngine::process_liveness(
			&imageInfo
		)));
	}
	funcWaitPtr(1 + loopsCount);

	// Compute the estimated frame rate.
	// At this step all frames are already processed but the result could be still on the delivery
	// queue due to the console display latency. You can move here the code used to wait until all
	// messages are displayed to include the delivery latency.
	const std::chrono::high_resolution_clock::time_point timeEnd = std::chrono::high_resolution_clock::now();
	const double elapsedTimeInMillis = std::chrono::duration_cast<std::chrono::duration<double >>(timeEnd - timeStart).count() * 1000.0;
	ULTFACE_SDK_PRINT_INFO("Elapsed time (Benchmark) = [[[ %lf millis ]]]", elapsedTimeInMillis);

	// Print latest result
	const std::string& json_ = result.json();
	if (!json_.empty()) {
		ULTFACE_SDK_PRINT_INFO("result: %s", json_.c_str());
	}

	// Print estimated frame rate
	const double estimatedFps = 1000.f / (elapsedTimeInMillis / static_cast<double>(parallelNotifCount));
	ULTFACE_SDK_PRINT_INFO("*** elapsedTimeInMillis: %lf, notified: %zu, estimatedFps: %lf ***", elapsedTimeInMillis, parallelNotifCount, estimatedFps);

	ULTFACE_SDK_PRINT_INFO("Press any key to terminate !!");
	getchar();

	// DeInit
	ULTFACE_SDK_PRINT_INFO("Ending liveness...");
	ULTFACE_SDK_ASSERT(checkResult(UltFaceSdkEngine::deInit()));

	return 0;
}

static void printUsage(const std::string& message /*= ""*/)
{
	if (!message.empty()) {
		ULTFACE_SDK_PRINT_INFO("%s", message.c_str());
	}

	ULTFACE_SDK_PRINT_INFO(
		"\n********************************************************************************\n"
		"benchmark\n"
		"\t--image <path-to-image-with-a-face-to-analyse> \n"
		"\t--assets <path-to-assets-folder> \n"
		"\t[--parallel <whether-to-enable-parallel-mode:true / false>] \n"
		"\t[--cuda_activation <cuda-activation>] \n"
		"\t[--tokenfile <path-to-license-token-file>] \n"
		"\t[--tokendata <base64-license-token-data>] \n"
		"\n"
		"Options surrounded with [] are optional.\n"
		"\n"
		"--image: Path to an image(JPEG/PNG/BMP) to evaluate. \n\n"
		"--assets: Path to the assets folder containing the configuration files and models.\n\n"
		"--parallel: Whether to enabled the parallel mode. More info at https://www.doubango.org/SDKs/face-liveness/docs/Parallel_processing.html. Default: true.\n\n"
		"--cuda_activation: CUDA activation mode. More info at https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html#cuda-activation. Default: \"auto\". \n\n"
		"--loops: Number of times to execute the liveness pipeline. Default: 20.\n\n"
		"--tokenfile: Path to the file containing the base64 license token if you have one. If not provided then, the application will act like a trial version. Default: null.\n\n"
		"--tokendata: Base64 license token if you have one. If not provided then, the application will act like a trial version. Default: null.\n\n"
		"********************************************************************************\n"
	);
}

static bool parseArgs(int argc, char *argv[], std::map<std::string, std::string >& values)
{
	ULTFACE_SDK_ASSERT(argc > 0 && argv != nullptr);

	values.clear();

	// Make sure the number of arguments is even
	if ((argc - 1) & 1) {
		ULTFACE_SDK_PRINT_INFO("Number of args must be even");
		return false;
	}

	// Parsing
	for (int index = 1; index < argc; index += 2) {
		std::string key = argv[index];
		if (key.size() < 2 || key[0] != '-' || key[1] != '-') {
			ULTFACE_SDK_PRINT_INFO("Invalid key: %s", key.c_str());
			return false;
		}
		values[key] = argv[index + 1];
	}

	return true;
}

static bool readFile(const std::string& path, FileInfo& fileInfo)
{
	if (path.empty()) {
		ULTFACE_SDK_PRINT_ERROR("Path is empty");
		return false;
	}

	// Open file
	FILE* file =
#	if ULTFACE_SDK_OS_ANDROID
		sdk_android_asset_fopen(path.c_str(), "rb");
#	else
		fopen(path.c_str(), "rb");
#	endif
	if (!file) {
		ULTFACE_SDK_PRINT_ERROR("Failed to open file at: %s", path.c_str());
		return false;
	}

	// Decode the file
	int width, height, channels;
	stbi_uc* uncompressedData = stbi_load_from_file(file, &width, &height, &channels, 0);
	fclose(file);
	if (!uncompressedData || width <= 0 || height <= 0 || (channels != 1 && channels != 3 && channels != 4)) {
		ULTFACE_SDK_PRINT_ERROR("Invalid file(%s, %d, %d, %d)", path.c_str(), width, height, channels);
		if (uncompressedData) {
			free(uncompressedData);
		}
		return false;
	}

	// We expect RGB-family data from the JPEG/PNG/BMP file
	// If you're using data from your camera then, it should be YUV-family and you don't need
	// to convert to RGB-family.
	// List of supported types: https://www.doubango.org/SDKs/anpr/docs/cpp-api.html#_CPPv4N15ultimateAlprSdk22ULTFACE_SDK_IMAGE_TYPEE
	fileInfo.type = (channels == 3) ? ULTFACE_SDK_IMAGE_TYPE_RGB24 : (channels == 1 ? ULTFACE_SDK_IMAGE_TYPE_Y : ULTFACE_SDK_IMAGE_TYPE_RGBA32);
	fileInfo.uncompressedData = uncompressedData;
	fileInfo.width = static_cast<size_t>(width);
	fileInfo.height = static_cast<size_t>(height);

	return fileInfo.isValid();
}

static bool checkResult(const UltFaceSdkResult& result)
{
	if (!result.isOK()) {
		ULTFACE_SDK_PRINT_ERROR("Failed: phrase: %s, json: %s", result.phrase(), result.json());
		return false;
	}
	return true;
}