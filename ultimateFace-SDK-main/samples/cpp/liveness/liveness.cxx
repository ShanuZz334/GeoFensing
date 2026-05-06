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

using namespace UltFace;

struct FileInfo {
	void* compressedDataPtr = nullptr;
	size_t compressedDataSize = 0;
	FILE* filePtr = nullptr;
	virtual ~FileInfo() {
		if (compressedDataPtr) free(compressedDataPtr), compressedDataPtr = nullptr;
		if (filePtr) fclose(filePtr), filePtr = nullptr;
	}
	bool isValid() const {
		return compressedDataPtr && compressedDataSize > 0;
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

	// Init
	ULTFACE_SDK_PRINT_INFO("Starting liveness sample...");
	ULTFACE_SDK_ASSERT(checkResult(UltFaceSdkEngine::init(
		ASSET_MGR_PARAM()
		jsonConfig.c_str(),
		isParallelDeliveryEnabled ? &parallelDeliveryCallbackCallback : nullptr
	)));

	// Processing
	// Please note that the first inference is very slow because we'll load the models and
	// perform some initialization.
	const auto imageInfo = UltFaceImageInfoCompressed(file.compressedDataPtr, file.compressedDataSize);
	ULTFACE_SDK_ASSERT(checkResult(result = UltFaceSdkEngine::process_liveness(
		&imageInfo
	)));

	// Printing to the console is very slow and use a low priority thread.
	// Wait until all results are displayed.
	if (isParallelDeliveryEnabled) {
		static std::mutex parallelNotifMutex;
		std::unique_lock<std::mutex > lk(parallelNotifMutex);
		parallelNotifCondVar.wait_for(lk,
			std::chrono::milliseconds(1500), // maximum number of millis to wait for before giving up, must never wait this long
			[] { return (parallelNotifCount == 1); }
		);
	}

	// Print latest result
	const std::string& json_ = result.json();
	if (!json_.empty()) {
		ULTFACE_SDK_PRINT_INFO("result: %s", json_.c_str());
	}

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
		"\t[--parallel <whether-to-enable-parallel-mode:true/false>] \n"
		"\t[--cuda_activation <cuda-activation:auto/on/off>] \n"
		"\t[--tokenfile <path-to-license-token-file>] \n"
		"\t[--tokendata <base64-license-token-data>] \n"
		"\n"
		"Options surrounded with [] are optional.\n"
		"\n"
		"--image: Path to an image(JPEG/PNG/BMP) to evaluate. \n\n"
		"--assets: Path to the assets folder containing the configuration files and models.\n\n"
		"--parallel: Whether to enabled the parallel mode. More info at https://www.doubango.org/SDKs/face-liveness/docs/Parallel_processing.html. Default: true.\n\n"
		"--cuda_activation: CUDA activation mode. More info at https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html#cuda-activation. Default: \"auto\". \n\n"
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

static bool readFile(const std::string& path, FileInfo& file)
{
	// Open the file
	if ((file.filePtr = fopen(path.c_str(), "rb")) == nullptr) {
		ULTFACE_SDK_PRINT_INFO("Can't open %s", path.c_str());
		return false;
	}

	// Retrieve file size
	struct stat st_;
	if (stat(path.c_str(), &st_) != 0) {
		ULTFACE_SDK_PRINT_INFO("File is empty %s", path.c_str());
	}
	file.compressedDataSize = static_cast<size_t>(st_.st_size);

	// Alloc memory and read data
	file.compressedDataPtr = ::malloc(file.compressedDataSize);
	if (!file.compressedDataPtr) {
		ULTFACE_SDK_PRINT_INFO("Failed to alloc mem with size = %zu", file.compressedDataSize);
		return false;
	}
	size_t read_;
	if (file.compressedDataSize != (read_ = fread(file.compressedDataPtr, 1, file.compressedDataSize, file.filePtr))) {
		ULTFACE_SDK_PRINT_INFO("fread(%s) returned %zu instead of %zu", path.c_str(), read_, file.compressedDataSize);
		return false;
	}

	return file.isValid();
}

static bool checkResult(const UltFaceSdkResult& result)
{
	if (!result.isOK()) {
		ULTFACE_SDK_PRINT_ERROR("Failed: phrase: %s, json: %s", result.phrase(), result.json());
		return false;
	}
	return true;
}