import { useState } from "react";
import { Button } from "@/components/ui/button";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ImageTestPage = () => {
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const testImageGeneration = async () => {
    try {
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

  return (
    <div className="min-h-screen p-8 bg-gray-100">
      <div className="max-w-4xl mx-auto bg-white p-8 rounded-lg shadow">
        <h1 className="text-2xl font-bold mb-4">Image Generation Test</h1>
        
        <Button 
          onClick={testImageGeneration}
          disabled={loading}
          className="mb-4"
        >
          {loading ? "Generating..." : "Test Image Generation"}
        </Button>

        {error && (
          <div className="p-4 bg-red-100 text-red-700 rounded mb-4">
            Error: {error}
          </div>
        )}

        {image && (
          <div className="border p-4 rounded">
            <p className="text-sm mb-2">Image received ({image.length} chars)</p>
            <img 
              src={`data:image/png;base64,${image}`}
              alt="Generated"
              className="max-w-full rounded"
              onLoad={() => console.log("Image loaded!")}
              onError={(e) => console.error("Image load error:", e)}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default ImageTestPage;
