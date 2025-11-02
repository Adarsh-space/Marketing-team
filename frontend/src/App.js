import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import HomePage from "@/pages/HomePage";
import CampaignPage from "@/pages/CampaignPage";
import DashboardPage from "@/pages/DashboardPage";
import VoiceAssistant from "@/pages/VoiceAssistant";
import VoiceAssistantWithAgents from "@/pages/VoiceAssistantWithAgents";
import UnifiedAgentChat from "@/pages/UnifiedAgentChat";
import SettingsPage from "@/pages/SettingsPage";
import AgentChatPage from "@/pages/AgentChatPage";
import ImageTestPage from "@/pages/ImageTestPage";
import TaskManagementPage from "@/pages/TaskManagementPage";
import ZohoConnectionsPage from "@/pages/ZohoConnectionsPage";
import SocialMediaCredentialsPage from "@/pages/SocialMediaCredentialsPage";
import CampaignDashboard from "@/pages/CampaignDashboard";
import EmailDashboard from "@/pages/EmailDashboard";
import SocialMediaDashboard from "@/pages/SocialMediaDashboard";
import AnalyticsDashboard from "@/pages/AnalyticsDashboard";
// New Pages
import LoginPage from "@/pages/LoginPage";
import SignupPage from "@/pages/SignupPage";
import CreditsDashboard from "@/pages/CreditsDashboard";
import PaymentPage from "@/pages/PaymentPage";
import ScrapingDashboard from "@/pages/ScrapingDashboard";
import "@/App.css";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          {/* Authentication */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />

          {/* Main Pages */}
          <Route path="/" element={<HomePage />} />
          <Route path="/voice" element={<VoiceAssistantWithAgents />} />
          <Route path="/voice-simple" element={<VoiceAssistant />} />
          <Route path="/agent-chat" element={<UnifiedAgentChat />} />
          <Route path="/agents" element={<AgentChatPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/campaign/:campaignId" element={<CampaignPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/test-image" element={<ImageTestPage />} />
          <Route path="/task-management" element={<TaskManagementPage />} />
          <Route path="/zoho-connections" element={<ZohoConnectionsPage />} />
          <Route path="/social-media-credentials" element={<SocialMediaCredentialsPage />} />
          <Route path="/campaigns" element={<CampaignDashboard />} />
          <Route path="/email" element={<EmailDashboard />} />
          <Route path="/social-media" element={<SocialMediaDashboard />} />
          <Route path="/analytics" element={<AnalyticsDashboard />} />

          {/* New Features */}
          <Route path="/credits" element={<CreditsDashboard />} />
          <Route path="/payment" element={<PaymentPage />} />
          <Route path="/scraping" element={<ScrapingDashboard />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
