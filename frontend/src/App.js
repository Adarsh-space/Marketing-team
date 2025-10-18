import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import HomePage from "@/pages/HomePage";
import CampaignPage from "@/pages/CampaignPage";
import DashboardPage from "@/pages/DashboardPage";
import VoiceAssistant from "@/pages/VoiceAssistant";
import "@/App.css";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/voice" element={<VoiceAssistant />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/campaign/:campaignId" element={<CampaignPage />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
