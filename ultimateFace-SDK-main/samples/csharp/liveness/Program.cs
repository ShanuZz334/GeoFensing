/* Copyright (C) 2011-2025 Doubango Telecom <https://www.doubango.org>
* File author: Mamadou DIOP (Doubango Telecom, France).
* License: For non commercial use only.
* Source code: https://github.com/DoubangoTelecom/ultimateFace-SDK
* WebSite: https://www.doubango.org/webapps/face-liveness
*/
using System;
using System.Collections.Generic;
using System.Web.Script.Serialization;
using System.Runtime.InteropServices;
using org.doubango.UltFace.Sdk;

namespace liveness
{
    class Program
    {
        static void Main(String[] args)
        {
            // Parse arguments
            IDictionary<String, String> parameters = ParseArgs(args);

            // Make sur the image is provided using args
            if (!parameters.ContainsKey("--image"))
            {
                Console.Error.WriteLine("--image required");
                throw new Exception("--image required");
            }
            // Make sure the image exists
            String file = parameters["--image"];
            if (!System.IO.File.Exists(file))
            {
                throw new System.IO.FileNotFoundException("File not found:" + file);
            }

            // Extract assets folder
            // https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html#assets-folder
            String assetsFolder = parameters.ContainsKey("--assets")
                ? parameters["--assets"] : String.Empty;

            // License data - Optional
            // https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html#license-token-data
            String tokenDataBase64 = parameters.ContainsKey("--tokendata")
                ? parameters["--tokendata"] : String.Empty;

            // Initialize the engine: Load deep learning models and init GPU shaders
            // Make sure de disable VS hosting process to see logs from native code: https://social.msdn.microsoft.com/Forums/en-US/5da6cdb2-bc2b-4fff-8adf-752b32143dae/printf-from-dll-in-console-app-in-visual-studio-c-2010-express-does-not-output-to-console-window?forum=Vsexpressvcs
            // This function should be called once.
            UltFaceSdkResult result = CheckResult("Init", UltFaceSdkEngine.init(BuildJSON(assetsFolder, tokenDataBase64)));

            // Read file bytes (encoded JPEG or PNG)
            byte[] bytes = System.IO.File.ReadAllBytes(file);

            // Processing
            // Please note that the first inference is very slow because we'll load the models and
            // perform some initialization.
            GCHandle pinnedBuffer = GCHandle.Alloc(bytes, GCHandleType.Pinned);
            result = CheckResult("Process", UltFaceSdkEngine.process_liveness(
                new UltFaceImageInfoCompressed(pinnedBuffer.AddrOfPinnedObject(), (uint)bytes.Length)
                ));
            pinnedBuffer.Free();
            // Print result to console
            Console.WriteLine("Result: {0}", result.json());

            // Wait until user press a key
            Console.WriteLine("Press any key to terminate !!");
            Console.Read();

            // Now that you're done, deInit the engine before exiting
            CheckResult("DeInit", UltFaceSdkEngine.deInit());
        }

        static IDictionary<String, String> ParseArgs(String[] args)
        {
            Console.WriteLine("Args: {0}", string.Join(" ", args));

            if ((args.Length & 1) != 0)
            {
                String errMessage = String.Format("Number of args must be even: {0}", args.Length);
                Console.Error.WriteLine(errMessage);
                throw new Exception(errMessage);
            }

            // Parsing
            Dictionary<String, String> values = new Dictionary<String, String>();
            for (int index = 0; index < args.Length; index += 2)
            {
                String key = args[index];
                if (key.Length < 2 || key[0] != '-' || key[1] != '-')
                {
                    String errMessage = String.Format("Invalid key: {0}", key);
                    Console.Error.WriteLine(errMessage);
                    throw new Exception(errMessage);
                }
                values[key] = args[index + 1];
            }
            return values;
        }

        static UltFaceSdkResult CheckResult(String functionName, UltFaceSdkResult result)
        {
            if (!result.isOK())
            {
                String errMessage = String.Format("{0}: Execution failed: {1} -> {2}", new String[] { functionName, result.phrase(), result.json() });
                Console.Error.WriteLine(errMessage);
                throw new Exception(errMessage);
            }
            return result;
        }

        // https://www.doubango.org/SDKs/mrz/docs/Configuration_options.html
        static String BuildJSON(String assetsFolder = "", String tokenDataBase64 = "")
        {
            return new JavaScriptSerializer().Serialize(new
            {
                debug_level = "info",
                debug_write_input_image_enabled = false,
                debug_internal_data_path = ".",

                gpu_ctrl_memory_enabled = true,
                num_threads = -1,
                max_latency = -1,
                max_batchsize = -1,
                asm_enabled = true,
                intrin_enabled = true,
                cuda_activation = "auto",
                backend = "onnx",

                detect_target_size = 640,
                detect_size_threshold = 16,
                detect_score_threshold = 0.5,
                detect_iou_threshold = 0.4,
                detect_topk = 1000,

                avantgarde_score_threshold = 0.5,

                liveness_genuine_threshold = 0.5,
                liveness_disputed_threshold = 0.4,

                deepfake_genuine_threshold = 0.5,

                disguise_genuine_threshold = 0.5,

                inject_similarity_threshold = 0.35,
                inject_genuine_threshold = 0.90,
                inject_smartpass_enabled = true,

                inject_channel1_threshold = 0.70,
                inject_channel2_threshold = 0.80,

                // Value added using command line args
                assets_folder = assetsFolder,
                license_token_data = tokenDataBase64,
            });
        }
    }
}
