import { useState } from "react";
import { Button } from "@/components/ui/button";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ImageTestPage = () => {
  const [image, setImage] = useState(null);
  const [video, setVideo] = useState(null);
  const [videoConcept, setVideoConcept] = useState(null);
  const [loading, setLoading] = useState(false);
  const [videoLoading, setVideoLoading] = useState(false);
  const [error, setError] = useState(null);

  const testImageGeneration = async () => {
    try:
      setLoading(true);
      setError(null);
      console.log("Requesting image...");
      
      const response = await axios.post(`${API}/chat`, {
        message: "Generate an image of a sunset",
        user_id: "test_user"
      }, {
        timeout: 60000
      });

      console.log("Response received:", response.data);
      
      if (response.data.image_base64) {
        console.log("Image data length:", response.data.image_base64.length);
        setImage(response.data.image_base64);
      } else {
        setError("No image in response");
      }
    } catch (err) {
      console.error("Error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const testVideoGeneration = async () => {
    try {
      setVideoLoading(true);
      setError(null);
      console.log("Requesting video...");
      
      const response = await axios.post(`${API}/generate-video`, {
        content: "Dynamic marketing video for a tech startup showcasing innovation",
        duration: 10,
        resolution: "1080p"
      }, {
        timeout: 120000 // 2 minutes for video
      });

      console.log("Video response received:", response.data);
      
      if (response.data.status === "success" && response.data.video_base64) {
        console.log("Video data length:", response.data.video_base64.length);
        setVideo(response.data.video_base64);
      } else if (response.data.status === "concept_only") {
        console.log("Sora not available, showing concept");
        setVideoConcept(response.data.video_concept);
      } else {
        setError("No video in response");
      }
    } catch (err) {
      console.error("Error:", err);
      setError(err.message);
    } finally {
      setVideoLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-8 bg-gray-100">
      <div className="max-w-4xl mx-auto bg-white p-8 rounded-lg shadow">
        <h1 className="text-2xl font-bold mb-6">Image & Video Generation Test</h1>
        
        {/* Image Test Section */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-3">Image Generation (DALL-E)</h2>
          <Button 
            onClick={testImageGeneration}
            disabled={loading}
            className="mb-4"
          >
            {loading ? "Generating Image..." : "Test Image Generation"}
          </Button>

          {image && (
            <div className="border p-4 rounded">
              <p className="text-sm mb-2 text-green-600">✅ Image received ({image.length} chars) - HD Quality</p>
              <img 
                src={`data:image/png;base64,${image}`}
                alt="Generated"
                className="max-w-full rounded shadow-lg"
                onLoad={() => console.log("Image loaded!")}
                onError={(e) => console.error("Image load error:", e)}
              />
            </div>
          )}
        </div>

        {/* Video Test Section */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-3">Video Generation (Sora)</h2>
          <Button 
            onClick={testVideoGeneration}
            disabled={videoLoading}
            className="mb-4 bg-purple-600 hover:bg-purple-700"
          >
            {videoLoading ? "Generating Video..." : "Test Video Generation"}
          </Button>

          {video && (
            <div className="border p-4 rounded">
              <p className="text-sm mb-2 text-green-600">✅ Video received ({video.length} chars) - 1080p</p>
              <video 
                src={`data:video/mp4;base64,${video}`}
                controls
                className="max-w-full rounded shadow-lg"
                onLoadedData={() => console.log("Video loaded!")}
                onError={(e) => console.error("Video load error:", e)}
              />
            </div>
          )}

          {videoConcept && (
            <div className="border p-4 rounded bg-yellow-50">
              <p className="text-sm mb-2 text-yellow-700">ℹ️ Sora API not available yet - Video Concept Generated:</p>
              <div className="whitespace-pre-wrap text-sm">{videoConcept}</div>
            </div>
          )}
        </div>

        {error && (
          <div className="p-4 bg-red-100 text-red-700 rounded mb-4">
            Error: {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default ImageTestPage;
