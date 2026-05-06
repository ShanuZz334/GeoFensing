/* Copyright (C) 2011-2025 Doubango Telecom <https://www.doubango.org>
   File author: Mamadou DIOP (Doubango Telecom, France).
   License: For non commercial use only.
   Source code: https://github.com/DoubangoTelecom/ultimateFace-SDK
   WebSite: https://www.doubango.org/webapps/face-liveness
*/

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.util.Hashtable;
import java.util.IllegalFormatException;
import java.util.List;
import java.util.Arrays;
import java.util.stream.Collectors;
import java.lang.IllegalArgumentException;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;

import org.doubango.UltFace.Sdk.UltFaceSdkEngine;
import org.doubango.UltFace.Sdk.UltFaceSdkResult;
import org.doubango.UltFace.Sdk.UltFaceImageInfoCompressed;

public class Recognition {

   public static void main(String[] args) throws IllegalArgumentException, FileNotFoundException, IOException {
      // Parse arguments
      final Hashtable<String, String> parameters = ParseArgs(args);

      // Make sur the image is provided using args
      if (!parameters.containsKey("--image0") || !parameters.containsKey("--image1"))
      {
         System.err.println("--image0 and --image0 are required");
         throw new IllegalArgumentException("--image0 and --image1 required");
      }
      // Extract assets folder
      // https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html#assets-folder
      final String assetsFolder = parameters.containsKey("--assets")
          ? parameters.get("--assets") : "";

      // License data - Optional
      // https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html#license-token-data
      final String tokenDataBase64 = parameters.containsKey("--tokendata")
          ? parameters.get("--tokendata") : "";

      // Similarity threshold
      final double threshold = parameters.containsKey("--threshold")
          ? Double.parseDouble(parameters.get("--threshold")) : 0.35;

      // Load the native library
      System.loadLibrary("ultimateFaceSDK");

      // Initialize the engine
      UltFaceSdkResult result = CheckResult("Init", UltFaceSdkEngine.init(BuildJSON(assetsFolder, tokenDataBase64)));

      // Decode the JPEG/PNG/BMP file
      final File files[] = { 
         new File(parameters.get("--image0")),
         new File(parameters.get("--image1"))
      };
      for (int i = 0; i < files.length; ++i) {
         if (!files[i].exists()) {
            throw new FileNotFoundException("File not found: " + files[i].getAbsolutePath());
         }
      }

      // Reading The data
      ByteBuffer nativeBuffers[] = { null, null };
      for (int i = 0; i < files.length; ++i) {
         try(RandomAccessFile inFile = new RandomAccessFile(files[i], "r")) {
            final FileChannel inChannel = inFile.getChannel();
            nativeBuffers[i] = ByteBuffer.allocateDirect((int)inChannel.size());
            inChannel.read(nativeBuffers[i]);
            nativeBuffers[i].flip();         
         } catch (IOException e) {
            e.printStackTrace();
            throw e;
         }
      }
      
      // Processing
      // First inference is expected to be slow because models will be loaded and initialized.
      // Please do not report about inference being slow.
      float embeddings[][] = new float[files.length][];
      for (int i = 0; i < files.length; ++i) {
         result = CheckResult("Process", UltFaceSdkEngine.process_recognition(
               new UltFaceImageInfoCompressed(nativeBuffers[i], nativeBuffers[i].remaining())
            ));
         embeddings[i] = extractEmbeddingsForTheLargestFace(result);
      }
      
      // Computing similarity. It's DOT product between the vectors.
      // The returned vectors are already L2-normed which means their
      // dot product value is within [-1,1].
      // On python you'd call "emb0.dot(emb1.T)"
      assert embeddings[0].length == embeddings[1].length;
      double similarity = 0;
      final float[] emb0 = embeddings[0];
      final float[] emb1 = embeddings[1];
      for (int i = 0; i < emb0.length; ++i) {
         similarity += emb0[i] * emb1[i];
      }
      System.out.println(String.format("Size: %d. Similarity: %f. Matched: %s", emb0.length, similarity, (similarity >= threshold) ? "yes" : "no"));

      // Wait until user press a key
      System.out.println("Press any key to terminate !!" + System.lineSeparator());
      final java.util.Scanner scanner = new java.util.Scanner(System.in);
      if (scanner != null) {
         scanner.nextLine();
         scanner.close();
      }

      // Now that you're done, deInit the engine before exiting
      CheckResult("DeInit", UltFaceSdkEngine.deInit());
   }

   static Hashtable<String, String> ParseArgs(String[] args) throws IllegalArgumentException
   {
      System.out.println("Args: " + String.join(" ", args) + System.lineSeparator());

      if ((args.length & 1) != 0)
      {
            String errMessage = String.format("Number of args must be even: %d", args.length);
            System.err.println(errMessage);
            throw new IllegalArgumentException(errMessage);
      }

      // Parsing
      Hashtable<String, String> values = new Hashtable<String, String>();
      for (int index = 0; index < args.length; index += 2)
      {
            String key = args[index];
            if (!key.startsWith("--"))
            {
               String errMessage = String.format("Invalid key: %s", key);
               System.err.println(errMessage);
               throw new IllegalArgumentException(errMessage);
            }
            values.put(key, args[index + 1].replace("$(ProjectDir)", System.getProperty("user.dir").trim()));
      }
      return values;
   }

   static UltFaceSdkResult CheckResult(String functionName, UltFaceSdkResult result) throws IOException
   {
      if (!result.isOK())
      {
            String errMessage = String.format("%s: Execution failed: %s, %s", functionName, result.phrase(), result.json());
            System.err.println(errMessage);
            throw new IOException(errMessage);
      }
      return result;
   }

   static float[] extractEmbeddingsForTheLargestFace(UltFaceSdkResult result) throws IOException
   {
      // we're using regular expressions to extract the embeddings to avoid adding
      // a json parser to the dependencies. you *must* not do it in your app.
      Pattern pattern = Pattern.compile("\\[{2}([^\\]]+)", Pattern.CASE_INSENSITIVE);
      Matcher matcher = pattern.matcher(result.json());
      boolean found = matcher.find();
      if (!found) {
         throw new IOException("Failed to find an embedding in the json result");
      }

      // Splitting the array
      String embeddings_str = matcher.group(1);
      Pattern p = Pattern.compile(",");
      String[] elements = p.split(embeddings_str);
      float embeddings_float[] = new float[elements.length];
      for (int  i = 0; i < elements.length; ++i) {
         embeddings_float[i] = Float.parseFloat(elements[i]);
      }

      return embeddings_float;
   }

   // https://www.doubango.org/SDKs/face-liveness/docs/Configuration_options.html
   static String BuildJSON(String assetsFolder, String tokenDataBase64)
   {
      return String.format(
         "{" +
         "\"debug_level\": \"info\"," +
         "\"debug_write_input_image_enabled\": false," +
         "\"debug_internal_data_path\": \".\"," +
         "" +
         "\"gpu_ctrl_memory_enabled\": true," +
         "\"num_threads\": -1," +
         "\"max_latency\": -1," +
         "\"max_batchsize\": -1," +
         "\"asm_enabled\": true," +
         "\"intrin_enabled\": true," +
         "\"cuda_activation\": \"auto\"," +
         "\"backend\": \"onnx\"," +
         "" +
         "\"detect_target_size\": 640," +
         "\"detect_size_threshold\": 16," +
         "\"detect_score_threshold\": 0.5," +
         "\"detect_iou_threshold\": 0.4," +
         "\"detect_topk\": 1," +
         "" +
         "\"avantgarde_score_threshold\": 0.5," +
         "" +
         "\"liveness_genuine_threshold\": 0.5," +
         "\"liveness_disputed_threshold\": 0.4," +
         "" +
         "\"deepfake_genuine_threshold\": 0.5," +
         "" +
         "\"disguise_genuine_threshold\": 0.5," +
         "" +
         "\"inject_similarity_threshold\": 0.35," +
         "\"inject_genuine_threshold\": 0.90," +
         "\"inject_smartpass_enabled\": true," +
         "" +
         "\"assets_folder\": \"%s\"," +
         "\"license_token_data\": \"%s\"" +
         "}"
         , 
         // Value added using command line args
         assetsFolder,
         tokenDataBase64
      );
   }
}