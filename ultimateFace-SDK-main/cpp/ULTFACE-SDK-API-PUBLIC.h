/* Copyright (C) 2011-2025 Doubango Telecom <https://www.doubango.org>
* File author: Mamadou DIOP (Doubango Telecom, France).
* License: For non commercial use only.
* Source code: https://github.com/DoubangoTelecom/ultimateFace-SDK
* WebSite: https://www.doubango.org/webapps/face-liveness
*/
/**
\file ULTFACE-SDK-API-PUBLIC.h
UltimateFace-SDK public header
*/
#ifndef _ULTFACE_SDK_API_PUBLIC_H_
#define _ULTFACE_SDK_API_PUBLIC_H_

#include <string>
#include <assert.h>

/// \def ULTFACE_SDK_VERSION_MAJOR
/// Major version
///
/// \def ULTFACE_SDK_VERSION_MINOR
/// Minor version
///
/// \def ULTFACE_SDK_VERSION_MICRO
/// Micro version
#define ULTFACE_SDK_VERSION_MAJOR		0
#define ULTFACE_SDK_VERSION_MINOR		0
#define ULTFACE_SDK_VERSION_MICRO		2

// Windows's symbols export
#if defined(SWIG)
# 	define ULTFACE_SDK_PUBLIC_API
#else
#	if (defined(WIN32) || defined(_WIN32) || defined(_WIN32_WCE) || defined(_WIN16) || defined(_WIN64) || defined(__WIN32__) || defined(__TOS_WIN__) || defined(__WINDOWS__)) && !defined(ULTFACE_SDK_STATIC)
#		if defined (ULTFACE_SDK_EXPORTS)
# 			define ULTFACE_SDK_PUBLIC_API		__declspec(dllexport)
#		else
# 			define ULTFACE_SDK_PUBLIC_API		__declspec(dllimport)
#		endif
#	else
# 		define ULTFACE_SDK_PUBLIC_API			__attribute__((visibility("default")))
#	endif /* WIN32 */
#endif /* SWIG */

// Android OS detection
#if (defined(__ANDROID__) || defined(ANDROID)) && !defined(SWIG)
#	define ULTFACE_SDK_OS_ANDROID	1
#endif /* ULTFACE_SDK_OS_ANDROID */

// Macros to print logs to the console
#if ULTFACE_SDK_OS_ANDROID
#	if !defined(SWIG)
#		include <android/log.h>
#		include <android/asset_manager.h>
#		include <jni.h>
#	endif
#	define ULTFACE_SDK_PRINT_VERBOSE(FMT, ...) __android_log_print(ANDROID_LOG_VERBOSE, "org.doubango.ultFace.Sdk", "*[ULTFACE_SDK VERBOSE]: " FMT "\n", ##__VA_ARGS__)
#	define ULTFACE_SDK_PRINT_INFO(FMT, ...) __android_log_print(ANDROID_LOG_INFO, "org.doubango.ultFace.Sdk", "*[ULTFACE_SDK INFO]: " FMT "\n", ##__VA_ARGS__)
#	define ULTFACE_SDK_PRINT_WARN(FMT, ...) __android_log_print(ANDROID_LOG_WARN, "org.doubango.ultFace.Sdk", "**[ULTFACE_SDK WARN]: function: \"%s()\" \nfile: \"%s\" \nline: \"%u\" \nmessage: " FMT "\n", __FUNCTION__,  __FILE__, __LINE__, ##__VA_ARGS__)
#	define ULTFACE_SDK_PRINT_ERROR(FMT, ...) __android_log_print(ANDROID_LOG_ERROR, "org.doubango.ultFace.Sdk", "***[ULTFACE_SDK ERROR]: function: \"%s()\" \nfile: \"%s\" \nline: \"%u\" \nmessage: " FMT "\n", __FUNCTION__,  __FILE__, __LINE__, ##__VA_ARGS__)
#	define ULTFACE_SDK_PRINT_FATAL(FMT, ...) __android_log_print(ANDROID_LOG_FATAL, "org.doubango.ultFace.Sdk", "****[ULTFACE_SDK FATAL]: function: \"%s()\" \nfile: \"%s\" \nline: \"%u\" \nmessage: " FMT "\n", __FUNCTION__,  __FILE__, __LINE__, ##__VA_ARGS__)
#else
#	define ULTFACE_SDK_PRINT_VERBOSE(FMT, ...) fprintf(stderr, "*[ULTFACE_SDK VERBOSE]: " FMT "\n", ##__VA_ARGS__)
#	define ULTFACE_SDK_PRINT_INFO(FMT, ...) fprintf(stderr, "*[ULTFACE_SDK INFO]: " FMT "\n", ##__VA_ARGS__)
#	define ULTFACE_SDK_PRINT_WARN(FMT, ...) fprintf(stderr, "**[ULTFACE_SDK WARN]: function: \"%s()\" \nfile: \"%s\" \nline: \"%u\" \nmessage: " FMT "\n", __FUNCTION__,  __FILE__, __LINE__, ##__VA_ARGS__)
#	define ULTFACE_SDK_PRINT_ERROR(FMT, ...) fprintf(stderr, "***[ULTFACE_SDK ERROR]: function: \"%s()\" \nfile: \"%s\" \nline: \"%u\" \nmessage: " FMT "\n", __FUNCTION__,  __FILE__, __LINE__, ##__VA_ARGS__)
#	define ULTFACE_SDK_PRINT_FATAL(FMT, ...) fprintf(stderr, "****[ULTFACE_SDK FATAL]: function: \"%s()\" \nfile: \"%s\" \nline: \"%u\" \nmessage: " FMT "\n", __FUNCTION__,  __FILE__, __LINE__, ##__VA_ARGS__)
#endif /* !ULTFACE_SDK_OS_ANDROID */

// Assertion function
#if defined(NDEBUG)
#	define ULTFACE_SDK_ASSERT(x) do { bool __ULTFACE_SDK_b_ret = (x); if (!__ULTFACE_SDK_b_ret) { ULTFACE_SDK_PRINT_FATAL("Assertion failed!"); abort(); } } while(0)
#else
#	define ULTFACE_SDK_ASSERT(x) do { bool __ULTFACE_SDK_b_ret = (x); assert(__ULTFACE_SDK_b_ret); } while(0)
#endif /* !NDEBUG */

namespace UltFace
{
	/*! Defines the image types.
	*/
	enum ULTFACE_SDK_IMAGE_TYPE {
		/*! Each pixel is stored on 3 bytes. Each channel (R, G, B) is stored with 8 bits of precision (256 possible values).
		* Here is how the pixels are packed:
		* \code{.cpp}
		* const int pixel = (B & 0xff) << 16 | (G & 0xff) << 8 | (R & 0xff);
		* \endcode
		*/
		ULTFACE_SDK_IMAGE_TYPE_RGB24,

		/*! Each pixel is stored on 4 bytes. Each channel (R, G, B, A) is stored with 8 bits (1 byte) of precision (256 possible values).
		* The R channel is stored at the lowest memory address followed by G, B then A channels. If you're using Android then,
		* this is the same as <a href="https://developer.android.com/reference/android/graphics/Bitmap.Config#ARGB_8888">ARGB_8888</a>.
		* Here is how the pixels are packed:
		* \code{.cpp}
		* const int pixel = (A & 0xff) << 24 | (B & 0xff) << 16 | (G & 0xff) << 8 | (R & 0xff);
		* \endcode
		*/
		ULTFACE_SDK_IMAGE_TYPE_RGBA32,

		/*! Each pixel is stored on 4 bytes. Each channel (B, G, R, A) is stored with 8 bits (1 byte) of precision (256 possible values).
		* The B channel is stored at the lowest memory address followed by G, R then A channels. If you're using iOS then,
		* this is the same as <a href="https://developer.apple.com/documentation/corevideo/1563591-pixel_format_identifiers/kcvpixelformattype_32bgra?language=objc">kCVPixelFormatType_32BGRA</a>.
		* Here is how the pixels are packed:
		* \code{.cpp}
		* const int pixel = (A & 0xff) << 24 | (R & 0xff) << 16 | (G & 0xff) << 8 | (B & 0xff);
		* \endcode
		*/
		ULTFACE_SDK_IMAGE_TYPE_BGRA32,

		/*! Each pixel is stored on 3 bytes. Each channel (B, G, R) is stored with 8 bits (1 byte) of precision (256 possible values).
		* The B channel is stored at the lowest memory address followed by G then R channels. If you're using C# then,
		* this is the same as <b>PixelFormat.Format24bppRgb</b>.
		* Here is how the pixels are packed:
		* \code{.cpp}
		* const int pixel = (R & 0xff) << 16 | (G & 0xff) << 8 | (B & 0xff);
		* \endcode
		*/
		ULTFACE_SDK_IMAGE_TYPE_BGR24,

		/*! YUV 4:2:0 image with a plane of 8 bit Y samples followed by an interleaved U/V plane containing 8 bit 2x2 subsampled colour difference samples.
		*	More information at https://www.fourcc.org/pixel-format/yuv-nv12/
		*/
		ULTFACE_SDK_IMAGE_TYPE_NV12,

		/*! YUV 4:2:0 image with a plane of 8 bit Y samples followed by an interleaved V/U plane containing 8 bit 2x2 subsampled chroma samples.
		* The same as \ref ULTFACE_SDK_IMAGE_TYPE_NV12 except the interleave order of U and V is reversed.
		*	More information at https://www.fourcc.org/pixel-format/yuv-nv21/
		*/
		ULTFACE_SDK_IMAGE_TYPE_NV21,

		/*! These formats are identical to YV12 except that the U and V plane order is reversed.
		* They comprise an NxM Y plane followed by (N/2)x(M/2) U and V planes.
		* This is the format of choice for many software MPEG codecs.
		* More information at https://www.fourcc.org/pixel-format/yuv-i420/
		*/
		ULTFACE_SDK_IMAGE_TYPE_YUV420P,

		/*! Same as \ref ULTFACE_SDK_IMAGE_TYPE_YUV420P except the order of U and V is reversed.
		* More information at https://www.fourcc.org/pixel-format/yuv-yv12/
		*/
		ULTFACE_SDK_IMAGE_TYPE_YVU420P,

		/*! YUV 4:2:2 image with an NxM Y plane followed by (N/2)x(M) V and U planes.
		*/
		ULTFACE_SDK_IMAGE_TYPE_YUV422P,

		/*! YUV 4:4:4 image with an NxM Y plane followed by NxM V and U planes.
		*/
		ULTFACE_SDK_IMAGE_TYPE_YUV444P,

		/*! Grayscale image with single channel (luminance only). Each pixel is stored in single byte (8 bit Y samples).
		*/
		ULTFACE_SDK_IMAGE_TYPE_Y,
	};

	/*! Abstract class representing image information.
	*/
	struct ULTFACE_SDK_PUBLIC_API UltFaceImageInfo {
		/*! Image type */
		enum Type {
			Compressed,
			Uncompressed
		};
	protected:
#if !defined(SWIG) // %nodefaultctor
		UltFaceImageInfo() = delete;
#endif
		/*! Constructs image information.
		\param type image type (compressed or uncompressed).
		*/
		UltFaceImageInfo(const Type& type)
			: type_(type)
		{
		}
#if !defined(SWIG)
	private:
		Type type_;

	public:
		virtual bool isValid() const = 0; ///< checks whether the image info is valid or not.
		bool isCompressed() const { return type_ == Type::Compressed; } ///< checks whether the image info represents compressed data or not.
		Type type() const { return type_; } ///< the type of the image info.
#endif
	};

	/*! Class representing compressed (png, jpeg...) image information.
	 \see \ref UltFaceImageInfoUncompressed
	*/
	struct ULTFACE_SDK_PUBLIC_API UltFaceImageInfoCompressed : public UltFaceImageInfo {
	public:
#if !defined(SWIG) // %nodefaultctor
		UltFaceImageInfoCompressed() = delete;
#endif
		/*! Constructs compressed (jpeg, png...) image information.
		\param data_ptr pointer to the compressed data.
		\param data_size size of the compressed data in bytes.
		*/
		UltFaceImageInfoCompressed(const void* data_ptr, const size_t& data_size)
			: UltFaceImageInfo(UltFaceImageInfo::Type::Compressed)
			, data_ptr_(data_ptr)
			, data_size_(data_size)
		{
		}
#if !defined(SWIG)
	private:
		const void* data_ptr_ = nullptr;
		size_t data_size_ = 0;

	public:
		const void* data_ptr() const { return data_ptr_; } ///< pointer to the compressed data.
		size_t data_size() const { return data_size_; } ///< size of the compressed data in bytes.
		virtual bool isValid() const override { return data_ptr_ && data_size_; } ///< checks whether the image info is valid or not.
#endif
	};

	/*! Abstract class representing uncompressed image information.
	* An uncompressed image could be of RGB (\ref UltFaceImageInfoRgbFamily) or YUV (\ref UltFaceImageInfoYuvFamily) family.
	* For compressed image (jpeg, png...), use \ref UltFaceImageInfoCompressed
	*
	* \see \ref UltFaceImageInfoUncompressed
	*/
	struct ULTFACE_SDK_PUBLIC_API UltFaceImageInfoUncompressed : public UltFaceImageInfo {
	protected:
#if !defined(SWIG) // %nodefaultctor
		UltFaceImageInfoUncompressed() = delete;
#endif
		/*! Constructs uncompressed (rgb, bgr, yuv...) image information.
		\param chroma image chroma.
		\param widthInSamples image width in samples.
		\param heightInSamples image height in samples.
		\param exifOrientation jpeg exif orientation (within [1,7]). The engine will rotate the image based on the orientation info. More info at https://jdhao.github.io/2019/07/31/image_rotation_exif_info.
		*/
		UltFaceImageInfoUncompressed(
			const ULTFACE_SDK_IMAGE_TYPE& chroma, 
			const size_t& widthInSamples, 
			const size_t& heightInSamples, 
			const int& exifOrientation = 1
		)
			: UltFaceImageInfo(UltFaceImageInfo::Type::Uncompressed)
			, chroma_(chroma)
			, widthInSamples_(widthInSamples)
			, heightInSamples_(heightInSamples)
			, exifOrientation_(exifOrientation)
		{
		}
#if !defined(SWIG)
	private:
		ULTFACE_SDK_IMAGE_TYPE chroma_;
		size_t widthInSamples_ = 0;
		size_t heightInSamples_ = 0;
		int exifOrientation_ = 1;

	public:
		ULTFACE_SDK_IMAGE_TYPE chroma() const { return chroma_; } ///< image chroma
		size_t widthInSamples() const { return widthInSamples_; } ///< image width in samples
		size_t heightInSamples() const { return heightInSamples_; } ///< image height in samples
		int exifOrientation() const { return exifOrientation_; } ///< jpeg exif orientation (within [1,7])
		virtual bool isValid() const override {
			return widthInSamples_ && heightInSamples_ && (exifOrientation_ >= 0 && exifOrientation_ <= 8);
		} ///< checks whether the image info is valid or not.
		bool isRgbFamilyType() const {
			return chroma_ == ULTFACE_SDK_IMAGE_TYPE_RGB24 ||
				chroma_ == ULTFACE_SDK_IMAGE_TYPE_RGBA32 ||
				chroma_ == ULTFACE_SDK_IMAGE_TYPE_BGRA32 ||
				chroma_ == ULTFACE_SDK_IMAGE_TYPE_BGR24;
		} ///< checks whether the image info represents RGB data or not.
#endif
	};

	/*! Class representing RGB-family (rgb, rgba, bgr...) image information
	* \see \ref UltFaceImageInfoYuvFamily
	*/
	struct ULTFACE_SDK_PUBLIC_API UltFaceImageInfoRgbFamily : public UltFaceImageInfoUncompressed {
	public:
#if !defined(SWIG) // %nodefaultctor
		UltFaceImageInfoRgbFamily() = delete;
#endif
		/*! Constructs RGB (rgb, bgr, rgba...) image information.
		\param chroma image chroma.
		\param rgbPtr image data pointer.
		\param widthInSamples image width in samples.
		\param heightInSamples image height in samples.
		\param strideInSamples image stride in samples. Should be zero unless your the data is strided.
		\param exifOrientation jpeg exif orientation (within [1,7]). The engine will rotate the image based on the orientation info. More info at https://jdhao.github.io/2019/07/31/image_rotation_exif_info.
		*/
		UltFaceImageInfoRgbFamily(
			const ULTFACE_SDK_IMAGE_TYPE& chroma,
			const void* rgbPtr, 
			const size_t& widthInSamples, 
			const size_t& heightInSamples, 
			const size_t& strideInSamples = 0, 
			const int& exifOrientation = 1
		)
			: UltFaceImageInfoUncompressed(chroma, widthInSamples, heightInSamples, exifOrientation)
			, rgbPtr_(rgbPtr)
			, strideInSamples_(strideInSamples)
		{
		}
#if !defined(SWIG)
		size_t strideInSamples() const { return strideInSamples_; } ///< image stride in samples
		const void* rgbPtr() const { return rgbPtr_; } ///< image data pointer
		virtual bool isValid() const override {
			return isRgbFamilyType() && UltFaceImageInfoUncompressed::isValid() && (rgbPtr() && (widthInSamples() <= strideInSamples() || !strideInSamples()));
		} ///< checks whether the image info is valid or not.
	private:
		const void* rgbPtr_ = nullptr;
		size_t strideInSamples_ = 0;
#endif
	};

	/*! Class representing YUV-family (yuv420, nv12, nv21, y...) image information
	* \see \ref UltFaceImageInfoRgbFamily
	*/
	struct ULTFACE_SDK_PUBLIC_API UltFaceImageInfoYuvFamily : public UltFaceImageInfoUncompressed {
#if !defined(SWIG) // %nodefaultctor
		UltFaceImageInfoYuvFamily() = delete;
#endif
		/*! Constructs YUV (yuv420, nv12, nv21, y...) image information.
		\param chroma image chroma.
		\param yPtr pointer to the start of the Y (luma) samples.
		\param uPtr pointer to the start of the U (chroma) samples.
		\param vPtr pointer to the start of the V (chroma) samples.
		\param widthInSamples image width in samples.
		\param heightInSamples image height in samples.
		\param yStrideInBytes image stride in bytes for the Y (luma) samples.
		\param uStrideInBytes image stride in bytes for the U (chroma) samples.
		\param vStrideInBytes image stride in bytes for the V (chroma) samples.
		\param uvPixelStrideInBytes image pixel stride in bytes for the UV (chroma) samples. Should be 1 for planar and 2 for semi-planar formats. Set to 0 for auto-detect.
		\param exifOrientation jpeg exif orientation (within [1,7]). The engine will rotate the image based on the orientation info. More info at https://jdhao.github.io/2019/07/31/image_rotation_exif_info.
		*/
		UltFaceImageInfoYuvFamily(
			const ULTFACE_SDK_IMAGE_TYPE& chroma,
			const void* yPtr,
			const void* uPtr,
			const void* vPtr,
			const size_t& widthInSamples,
			const size_t& heightInSamples,
			const size_t& yStrideInBytes,
			const size_t& uStrideInBytes,
			const size_t& vStrideInBytes,
			const size_t& uvPixelStrideInBytes = 0,
			const int& exifOrientation = 1
		)
			: UltFaceImageInfoUncompressed(chroma, widthInSamples, heightInSamples, exifOrientation)
			, yPtr_(yPtr)
			, uPtr_(uPtr)
			, vPtr_(vPtr)
			, yStrideInBytes_(yStrideInBytes)
			, uStrideInBytes_(uStrideInBytes)
			, vStrideInBytes_(vStrideInBytes)
			, uvPixelStrideInBytes_(uvPixelStrideInBytes)
		{}
#if !defined(SWIG)
		const void* yPtr() const { return yPtr_; } ///< pointer to the start of the Y (luma) samples
		const void* uPtr() const { return uPtr_; } ///< pointer to the start of the U (chroma) samples
		const void* vPtr() const { return vPtr_; } ///< pointer to the start of the V (chroma) samples
		size_t yStrideInBytes() const { return yStrideInBytes_; } ///< image stride in bytes for the Y (luma) samples
		size_t uStrideInBytes() const { return uStrideInBytes_; } ///< image stride in bytes for the U (chroma) samples
		size_t vStrideInBytes() const { return vStrideInBytes_; } ///< image stride in bytes for the V (chroma) samples
		size_t uvPixelStrideInBytes() const { return uvPixelStrideInBytes_; } ///< image pixel stride in bytes for the UV (chroma) samples

		virtual bool isValid() const override {
			return !isRgbFamilyType() && UltFaceImageInfoUncompressed::isValid() && yPtr() && uPtr() && vPtr() && yStrideInBytes() && uStrideInBytes() && vStrideInBytes() && yStrideInBytes() >= widthInSamples()
				&& (uvPixelStrideInBytes() >=0 && uvPixelStrideInBytes() <= 2);
		} ///< checks whether the image info is valid or not.
	private:
		const void* yPtr_ = nullptr;
		const void* uPtr_ = nullptr;
		const void* vPtr_ = nullptr;
		const size_t yStrideInBytes_ = 0;
		const size_t uStrideInBytes_ = 0;
		const size_t vStrideInBytes_ = 0;
		const size_t uvPixelStrideInBytes_ = 0;
#endif
	};

	/*! Result returned by the \ref UltFaceSdkEngine "engine" at initialization, deInitialization and processing stages.
	*/
	class ULTFACE_SDK_PUBLIC_API UltFaceSdkResult {
	public:
		UltFaceSdkResult();
		UltFaceSdkResult(const int code, const char* phrase, const char* json, const size_t numFaces = 0);
		UltFaceSdkResult(const UltFaceSdkResult& other);
		virtual ~UltFaceSdkResult();
#if !defined(SWIG)
		UltFaceSdkResult& operator=(const UltFaceSdkResult& other) { return operatorAssign(other); }
#endif
		inline int code()const { return code_; } ///< The result code. >=0 if success, <0 otherwise.
		inline const char* phrase()const { return phrase_; } ///< Short description for the \ref code.
		inline const char* json()const { return json_; } ///< The result as JSON string. May be null or empty if no face found.
		inline const size_t numFaces()const { return numFaces_; } ///< Number of faces in \ref json string. This is a helper function to quickly check whether the result contains faces without parsing the \ref json string.
		inline bool isOK()const { return (code_ == 0); } ///< Whether the result is success. true if success, false otherwise.
#if !defined(SWIG)
		static UltFaceSdkResult bodyless(const int code, const char* phrase) { return UltFaceSdkResult(code, phrase, ""); }
		static UltFaceSdkResult bodylessOK() { return UltFaceSdkResult(0, "OK", ""); }
#endif /* SWIG */

	private:
		void ctor(const int code, const char* phrase, const char* json, const size_t numFaces);
#if !defined(SWIG)
		UltFaceSdkResult& operatorAssign(const UltFaceSdkResult& other);
#endif /* SWIG */

	private:
		int code_;
		char* phrase_;
		char* json_;
		size_t numFaces_;
	};

	/*! Abstract class to be used to get asynchronous notifications.
	*/
	struct UltFaceSdkParallelDeliveryCallback
	{
	protected:
		UltFaceSdkParallelDeliveryCallback() { }
	public:
		virtual ~UltFaceSdkParallelDeliveryCallback() {  }
		/*! Notification function to override in order to receive the results. */
		virtual void onNewResult(const UltFaceSdkResult* newResult) const = 0;
	};

	/*! The Face SDK engine.
	*/
	class ULTFACE_SDK_PUBLIC_API UltFaceSdkEngine
	{
#if !defined(SWIG) // %nodefaultctor
	protected:
		UltFaceSdkEngine() = delete;
#endif /* SWIG */
	public:

#if ULTFACE_SDK_OS_ANDROID
		/*! Initializes the engine. This function must be the first one to call.
		This function is only available on Android.
		\param assetManager AssetManager to use to read the content of the "assets" folder containing the models and configuration files.
		\param jsonConfig JSON string containing configuration entries. May be null. More info at https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html
		\param parallelDeliveryCallback Callback function to enable parallel mode. Use null value to use sequential instead of parallel mode. More info at https://www.doubango.org/SDKs/face-liveness/docs/Parallel_versus_sequential_processing.html.
		\returns a result
		*/
		static UltFaceSdkResult init(jobject assetManager, const char* jsonConfig, const UltFaceSdkParallelDeliveryCallback* parallelDeliveryCallback = nullptr);
#else
		/*! Initializes the engine. This function must be the first one to call.
			\param jsonConfig JSON string containing configuration entries. May be null. More info at https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html
			\param parallelDeliveryCallback \ref UltFaceSdkParallelDeliveryCallback "callback" function to enable inter parallel mode. Use nullptr value to use sequential instead of parallel mode. More info at https://www.doubango.org/SDKs/face-liveness/docs/Parallel_processing.html#inter-processing.
			\returns a \ref UltFaceSdkResult "result"
		*/
		static UltFaceSdkResult init(const char* jsonConfig, const UltFaceSdkParallelDeliveryCallback* parallelDeliveryCallback = nullptr);
#endif /* ULTFACE_SDK_OS_ANDROID */

		/*! DeInitializes the engine. This function must be the last one to be call.
			Deallocates all the resources allocated using \ref init function.
			\returns a \ref UltFaceSdkResult "result"
		*/
		static UltFaceSdkResult deInit();
		
		/*! Performs face liveness detection. The full liveness pipeline includes avant-garde, deepfake detection and identity concealment detection.

			Sample code: 
				- cpp: <a href="https://github.com/DoubangoTelecom/ultimateFace-SDK/tree/main/samples/cpp/liveness/liveness.cxx">liveness.cxx</a>
				- python: <a href="https://github.com/DoubangoTelecom/ultimateFace-SDK/tree/main/samples/python/liveness/liveness.py">liveness.py</a>
				- csharp: <a href="https://github.com/DoubangoTelecom/ultimateFace-SDK/tree/main/samples/csharp/liveness/Program.cs">Program.cs</a>
				- java: <a href="https://github.com/DoubangoTelecom/ultimateFace-SDK/tree/main/samples/java/liveness/Liveness.java">Liveness.java</a>

			\param image The image to process. Use \ref UltFaceImageInfoRgbFamily or \ref UltFaceImageInfoYuvFamily to build the image.
			\returns a \ref UltFaceSdkResult "result
		*/
		static UltFaceSdkResult process_liveness(const UltFaceImageInfo* image);

		/*! Performs stream inject check (a.k.a virtual camera detection).
			Requires a stereo image (main and auxiliary) with some requirements.

			Sample code: 
				- python: <a href="https://github.com/DoubangoTelecom/ultimateFace-SDK/tree/main/samples/python/inject/inject.py">inject.py</a>

			\param stereo_main First part of the stereo image. Should have 720p ("1280 x 720" or "720 x 1280") size. Use \ref UltFaceImageInfoRgbFamily or \ref UltFaceImageInfoYuvFamily to build the image.
			\param stereo_aux Second part of the stereo image. Should have VGA ("640 x 480" or "480 x 640") size. Use \ref UltFaceImageInfoRgbFamily or \ref UltFaceImageInfoYuvFamily to build the image.
			\param aggressive_mode Possible values: "auto", "on" or "off". More info at https://www.doubango.org/SDKs/face-liveness/docs/Stream_injection_detection.html#aggressive-mode.
			\returns a \ref UltFaceSdkResult "result
		*/
		static UltFaceSdkResult process_inject(const UltFaceImageInfo* stereo_main, const UltFaceImageInfo* stereo_aux, const char* aggressive_mode = "auto");

		/*! Performs face recognition.

		Sample code: 
			- cpp: <a href="https://github.com/DoubangoTelecom/ultimateFace-SDK/tree/main/samples/cpp/recognition/recognition.cxx">recognition.cxx</a>
			- python: <a href="https://github.com/DoubangoTelecom/ultimateFace-SDK/tree/main/samples/python/recognition/recognition.py">recognition.py</a>
			- csharp: <a href="https://github.com/DoubangoTelecom/ultimateFace-SDK/tree/main/samples/csharp/recognition/Program.cs">Program.cs</a>
			- java: <a href="https://github.com/DoubangoTelecom/ultimateFace-SDK/tree/main/samples/java/recognition/Recognition.java">Recognition.java</a>

		\param image The image to process. Use \ref UltFaceImageInfoRgbFamily or \ref UltFaceImageInfoYuvFamily to build the image.
		\returns a \ref UltFaceSdkResult "result
		*/
		static UltFaceSdkResult process_recognition(const UltFaceImageInfo* image);

		/*! Retrieve EXIF orientation value from JPEG meta-data.
			\param jpegMetaDataPtr Pointer to the meta-data.
			\param jpegMetaDataSize Size of the meta-data.
			\returns Image's EXIF/JPEG orientation. Must be within [1, 7]. More information at https://jdhao.github.io/2019/07/31/image_rotation_exif_info.
		*/
		static int exifOrientation(const void* jpegMetaDataPtr, const size_t jpegMetaDataSize);

		/*! Build a unique runtime license key associated to this device.
			You must \ref init "initialize" the engine before calling this function.
			This function doesn't require internet connection.
			The runtime key must be activated to obtain a token. The activation procedure is explained at https://www.doubango.org/SDKs/LicenseManager/docs/Activation_use_cases.html.
			\param rawInsteadOfJSON Whether to output the runtime key as raw string intead of JSON entry. Requesting raw
			string instead of JSON could be helpful for applications without JSON parser to extract the key.
			\returns a \ref UltFaceSdkResult "result"
		*/
		static UltFaceSdkResult requestRuntimeLicenseKey(const bool& rawInsteadOfJSON = false);

#if !defined(SWIG)
		static UltFaceSdkResult optimizeTRT(const char* models_folder);
#endif /* !defined(SWIG) */

#if ULTFACE_SDK_OS_ANDROID && !defined(SWIG)
		static void setAssetManager(AAssetManager* assetManager);
		static void setJavaVM(JavaVM* vm);

	private:
		static bool s_bOweAAssetManager;
#endif /* ULTFACE_SDK_OS_ANDROID */
	};

} // namespace UltFace 

#endif // _ULTFACE_SDK_API_PUBLIC_H_
