import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import HomePage from "@/pages/HomePage";
import CampaignPage from "@/pages/CampaignPage";
import DashboardPage from "@/pages/DashboardPage";
import VoiceAssistant from "@/pages/VoiceAssistant";
import VoiceAssistantWithAgents from "@/pages/VoiceAssistantWithAgents";
import SettingsPage from "@/pages/SettingsPage";
import AgentChatPage from "@/pages/AgentChatPage";
import "@/App.css";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/voice" element={<VoiceAssistantWithAgents />} />
          <Route path="/voice-simple" element={<VoiceAssistant />} />
          <Route path="/agents" element={<AgentChatPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/campaign/:campaignId" element={<CampaignPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
