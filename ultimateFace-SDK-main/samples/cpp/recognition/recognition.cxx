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
#include <regex>

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

static void printUsage(const std::string& message = "");
static bool parseArgs(int argc, char *argv[], std::map<std::string, std::string >& values);
static bool readFile(const std::string& path, FileInfo& file);
static bool checkResult(const UltFaceSdkResult& result);
static std::vector<float> extractEmbeddingsForTheLargestFace(const UltFaceSdkResult& result);

// Similarity values are within [-1, 1].
// Faces will be considered the same if the similarity is
// greater or equal to the threshold.
static const double kSimilarityThreshold = 0.35;

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
"\"detect_topk\": 1"
""
;

int main(int argc, char *argv[])
{
	// local variables
	UltFaceSdkResult result;
	std::string assetsFolder, licenseTokenData, licenseTokenFile;
	std::string cudaActivation = "auto";
	bool isParallelDeliveryEnabled = true;
	std::string imagePaths[2];
	double threshold = kSimilarityThreshold;

	// Parsing args
	std::map<std::string, std::string > args;
	if (!parseArgs(argc, argv, args)) {
		printUsage();
		return -1;
	}
	if (args.find("--image0") == args.end()) {
		printUsage("--image0 required");
		return -1;
	}
	if (args.find("--image1") == args.end()) {
		printUsage("--image1 required");
		return -1;
	}
	if (args.find("--assets") == args.end()) {
		printUsage("--assets required");
		return -1;
	}
	imagePaths[0] = args["--image0"];
	imagePaths[1] = args["--image1"];

	if (args.find("--assets") != args.end()) {
		assetsFolder = args["--assets"];
#if defined(_WIN32)
		std::replace(assetsFolder.begin(), assetsFolder.end(), '\\', '/');
#endif
	}
	if (args.find("--cuda_activation") != args.end()) {
		cudaActivation = args["--cuda_activation"];
	}
	if (args.find("--threshold") != args.end()) {
		threshold = std::atof(args["--threshold"].c_str());
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

	// Read input files
	FileInfo files[2];
	for (size_t i = 0; i < sizeof(imagePaths) / sizeof(imagePaths[0]); ++i) {
		if (!readFile(imagePaths[i], files[i]) || !files[i].isValid()) {
			ULTFACE_SDK_PRINT_FATAL("Can't read %s", imagePaths[i].c_str());
			return -1;
		}
	}

	// Init the engine
	ULTFACE_SDK_PRINT_INFO("Starting recognition sample...");
	ULTFACE_SDK_ASSERT(checkResult(UltFaceSdkEngine::init(
		ASSET_MGR_PARAM()
		jsonConfig.c_str()
	)));

	// Processing
	// Please note that the first inference is very slow because we'll load the models and
	// perform some initialization.
	std::vector<float> embeddings[sizeof(files) / sizeof(files[0])];
	for (size_t i = 0; i < sizeof(files) / sizeof(files[0]); ++i) {
		// Extract face embeddings (512-float vectors)
		const auto imageInfo = UltFaceImageInfoCompressed(files[i].compressedDataPtr, files[i].compressedDataSize);
		ULTFACE_SDK_ASSERT(checkResult(result = UltFaceSdkEngine::process_recognition(
			&imageInfo
		)));
		embeddings[i] = extractEmbeddingsForTheLargestFace(result);
		if (embeddings[i].empty()) {
			ULTFACE_SDK_PRINT_ERROR("No face in image #%zu or failed to extract embeddings", i);
			return -1;
		}
	}

	// Computing similarity. It's DOT product between the vectors.
	// The returned vectors are already L2-normed which means their
	// dot product value is within [-1,1].
	// On python you'd call "emb0.dot(emb1.T)"
	ULTFACE_SDK_ASSERT(embeddings[0].size() == embeddings[1].size());
	double similarity = 0;
	const auto& emb0 = embeddings[0];
	const auto& emb1 = embeddings[1];
	for (size_t i = 0; i < emb0.size(); ++i) {
		similarity += emb0[i] * emb1[i];
	}
	ULTFACE_SDK_PRINT_INFO("Size: %zu. Similarity: %lf. Matched: %s", emb0.size(), similarity, (similarity >= threshold) ? "yes" : "no");

	// Done, press any key to terminate
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
		"--parallel: Whether to enabled the parallel mode. More info about the parallel mode at https ://www.doubango.org/SDKs/kyc-documents-verif/docs/Parallel_versus_sequential_processing.html. Default: true.\n\n"
		"--cuda_activation: CUDA activation type. Default: \"auto\". \n\n"
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
		ULTFACE_SDK_PRINT_ERROR("Can't open %s", path.c_str());
		return false;
	}

	// Retrieve file size
	struct stat st_;
	if (stat(path.c_str(), &st_) != 0) {
		ULTFACE_SDK_PRINT_ERROR("File is empty %s", path.c_str());
	}
	file.compressedDataSize = static_cast<size_t>(st_.st_size);

	// Alloc memory and read data
	file.compressedDataPtr = ::malloc(file.compressedDataSize);
	if (!file.compressedDataPtr) {
		ULTFACE_SDK_PRINT_ERROR("Failed to alloc mem with size = %zu", file.compressedDataSize);
		return false;
	}
	size_t read_;
	if (file.compressedDataSize != (read_ = fread(file.compressedDataPtr, 1, file.compressedDataSize, file.filePtr))) {
		ULTFACE_SDK_PRINT_ERROR("fread(%s) returned %zu instead of %zu", path.c_str(), read_, file.compressedDataSize);
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

static std::vector<float> extractEmbeddingsForTheLargestFace(const UltFaceSdkResult& result)
{
	std::vector<float> embeddings;
	// we're using regular expressions to extract the embeddings to avoid adding
	// a json parser to the dependencies. you *must* not do it in your app.
	std::cmatch sm;
	if (!std::regex_search(result.json(), sm, std::regex("\\[{2}([^\\]]+)")) || sm.size() != 2) {
		ULTFACE_SDK_PRINT_ERROR("Failed to find an embedding in the json result. [%zu]", sm.size());
		return embeddings;
	}

	// Splitting the array
	embeddings.reserve(512);
	const std::regex rgx(",");
	const std::string emb_str = sm.str(1);
	std::sregex_token_iterator iter(emb_str.cbegin(), emb_str.cend(), rgx, -1);
	std::sregex_token_iterator end{};
	for (; iter != end; ++iter) {
		embeddings.push_back(std::stof(iter->str()));
	}

	return embeddings;
}