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
        public class JsonResult
        {
            public List<List<double> > faces { get; set; }
        }

        static void Main(String[] args)
        {
            // Parse arguments
            IDictionary<String, String> parameters = ParseArgs(args);

            // Make sur the image is provided using args
            foreach (string arg in new String[]{ "--image0", "--image1"})
            {
                if (!parameters.ContainsKey(arg))
                {
                    throw new Exception(String.Format("{0} required", arg));
                }
                if (!System.IO.File.Exists(parameters[arg]))
                {
                    throw new System.IO.FileNotFoundException(String.Format("File not found: {0}", arg));
                }
            }

            // Threshold - optional
            double threshold = parameters.ContainsKey("--threshold")
                ? double.Parse(parameters["--threshold"]) : 0.35;

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

            // Extract embeddings
            byte[] bytes0 = System.IO.File.ReadAllBytes(parameters["--image0"]);
            byte[] bytes1 = System.IO.File.ReadAllBytes(parameters["--image1"]);
            GCHandle pinnedBuffer0 = GCHandle.Alloc(bytes0, GCHandleType.Pinned);
            GCHandle pinnedBuffer1 = GCHandle.Alloc(bytes1, GCHandleType.Pinned);
            UltFaceSdkResult result0 = CheckResult("Process", UltFaceSdkEngine.process_recognition(
                new UltFaceImageInfoCompressed(pinnedBuffer0.AddrOfPinnedObject(), (uint)bytes0.Length)
                ));
            UltFaceSdkResult result1 = CheckResult("Process", UltFaceSdkEngine.process_recognition(
                new UltFaceImageInfoCompressed(pinnedBuffer1.AddrOfPinnedObject(), (uint)bytes1.Length)
                ));
            pinnedBuffer0.Free();
            pinnedBuffer1.Free();

            // Extract faces' embeddings
            JavaScriptSerializer json_ser = new JavaScriptSerializer();
            JsonResult j0 = json_ser.Deserialize<JsonResult>(result0.json());
            JsonResult j1 = json_ser.Deserialize<JsonResult>(result1.json());
            if (j0.faces.Count == 0)
            {
                throw new Exception("No face in image0");
            }
            if (j1.faces.Count == 0)
            {
                throw new Exception("No face in image1");
            }
            
            // Compute Cosine Similarity on the first face (the largest one on each image)
            System.Diagnostics.Debug.Assert(j0.faces[0].Count == j1.faces[0].Count);
            double similarity = 0;
            for (int i = 0; i < j0.faces[0].Count; ++i)
            {
                similarity += j0.faces[0][i] * j1.faces[0][i];
            }

            // Print result to console
            Console.WriteLine(String.Format("Similarity: {0}, VecSize: {1}, Same: {2}", similarity, j0.faces[0].Count, (similarity >= threshold)));

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
                detect_topk = 1,

                avantgarde_score_threshold = 0.5,

                liveness_genuine_threshold = 0.5,
                liveness_disputed_threshold = 0.4,

                deepfake_genuine_threshold = 0.5,

                disguise_genuine_threshold = 0.5,

                inject_similarity_threshold = 0.35,
                inject_genuine_threshold = 0.90,
                inject_smartpass_enabled = true,

                // Value added using command line args
                assets_folder = assetsFolder,
                license_token_data = tokenDataBase64,
            });
        }
    }
}
