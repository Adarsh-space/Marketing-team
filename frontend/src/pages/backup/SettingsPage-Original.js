import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sparkles, ArrowLeft, Check, Facebook, Instagram, Linkedin, Twitter, Globe, Save } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SettingsPage = () => {
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [hubspotConnected, setHubspotConnected] = useState(false);
  const [credentials, setCredentials] = useState({
    facebook_page_id: '',
    facebook_access_token: '',
    instagram_account_id: '',
    instagram_access_token: '',
    linkedin_page_id: '',
    linkedin_access_token: '',
    twitter_api_key: '',
    twitter_api_secret: '',
    twitter_access_token: '',
    twitter_access_secret: '',
    google_analytics_id: '',
    website_url: ''
  });

  useEffect(() => {
    loadSettings();
    checkHubSpotStatus();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      if (response.data.credentials) {
        setCredentials(response.data.credentials);
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const checkHubSpotStatus = async () => {
    try {
      const response = await axios.get(`${API}/hubspot/status`);
      setHubspotConnected(response.data.connected);
    } catch (error) {
      console.error('Error checking HubSpot status:', error);
    }
  };

  const handleConnectHubSpot = async () => {
    try {
      const response = await axios.get(`${API}/oauth/hubspot/authorize`);
      window.location.href = response.data.authorization_url;
    } catch (error) {
      toast.error('Failed to connect HubSpot');
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await axios.post(`${API}/settings`, { credentials });
      toast.success('Settings saved successfully!');
    } catch (error) {
      console.error('Error saving settings:', error);
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field, value) => {
    setCredentials(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="min-h-screen pb-20">
      {/* Navigation */}
      <nav className="glass fixed top-0 left-0 right-0 z-50 border-b border-white/20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3" onClick={() => navigate('/')} style={{cursor: 'pointer'}}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-600 to-blue-600 bg-clip-text text-transparent">
              MarketAI
            </h1>
          </div>
          <Button 
            onClick={() => navigate('/')}
            variant="outline"
            className="border-cyan-200 hover:bg-cyan-50"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
        </div>
      </nav>

      {/* Content */}
      <div className="pt-24 px-6">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-3 text-slate-800">Integrations & Settings</h1>
            <p className="text-lg text-slate-600">Connect your social media accounts and marketing tools</p>
          </div>

          {/* HubSpot */}
          <Card className="p-6 glass border-white/30 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center">
                  <Globe className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-slate-800">HubSpot CRM</h3>
                  <p className="text-sm text-slate-600">Connect your HubSpot account for CRM integration</p>
                </div>
              </div>
              {hubspotConnected ? (
                <div className="flex items-center gap-2 text-green-700">
                  <Check className="w-5 h-5" />
                  <span className="font-medium">Connected</span>
                </div>
              ) : (
                <Button onClick={handleConnectHubSpot} className="bg-gradient-to-r from-orange-500 to-red-500 text-white">
                  Connect HubSpot
                </Button>
              )}
            </div>
          </Card>

          {/* Facebook */}
          <Card className="p-6 glass border-white/30 mb-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center">
                <Facebook className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-800">Facebook</h3>
                <p className="text-sm text-slate-600">Connect your Facebook Page for posting and analytics</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-700 mb-2">Page ID</Label>
                <Input 
                  value={credentials.facebook_page_id}
                  onChange={(e) => handleChange('facebook_page_id', e.target.value)}
                  placeholder="Your Facebook Page ID"
                  className="bg-white"
                />
              </div>
              <div>
                <Label className="text-slate-700 mb-2">Access Token</Label>
                <Input 
                  type="password"
                  value={credentials.facebook_access_token}
                  onChange={(e) => handleChange('facebook_access_token', e.target.value)}
                  placeholder="Facebook Access Token"
                  className="bg-white"
                />
              </div>
            </div>
          </Card>

          {/* Instagram */}
          <Card className="p-6 glass border-white/30 mb-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center">
                <Instagram className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-800">Instagram</h3>
                <p className="text-sm text-slate-600">Connect your Instagram Business Account</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-700 mb-2">Account ID</Label>
                <Input 
                  value={credentials.instagram_account_id}
                  onChange={(e) => handleChange('instagram_account_id', e.target.value)}
                  placeholder="Instagram Account ID"
                  className="bg-white"
                />
              </div>
              <div>
                <Label className="text-slate-700 mb-2">Access Token</Label>
                <Input 
                  type="password"
                  value={credentials.instagram_access_token}
                  onChange={(e) => handleChange('instagram_access_token', e.target.value)}
                  placeholder="Instagram Access Token"
                  className="bg-white"
                />
              </div>
            </div>
          </Card>

          {/* LinkedIn */}
          <Card className="p-6 glass border-white/30 mb-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center">
                <Linkedin className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-800">LinkedIn</h3>
                <p className="text-sm text-slate-600">Connect your LinkedIn Company Page</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-700 mb-2">Page ID</Label>
                <Input 
                  value={credentials.linkedin_page_id}
                  onChange={(e) => handleChange('linkedin_page_id', e.target.value)}
                  placeholder="LinkedIn Page ID"
                  className="bg-white"
                />
              </div>
              <div>
                <Label className="text-slate-700 mb-2">Access Token</Label>
                <Input 
                  type="password"
                  value={credentials.linkedin_access_token}
                  onChange={(e) => handleChange('linkedin_access_token', e.target.value)}
                  placeholder="LinkedIn Access Token"
                  className="bg-white"
                />
              </div>
            </div>
          </Card>

          {/* Twitter/X */}
          <Card className="p-6 glass border-white/30 mb-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center">
                <Twitter className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-800">Twitter / X</h3>
                <p className="text-sm text-slate-600">Connect your Twitter/X account for posting</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-700 mb-2">API Key</Label>
                <Input 
                  value={credentials.twitter_api_key}
                  onChange={(e) => handleChange('twitter_api_key', e.target.value)}
                  placeholder="Twitter API Key"
                  className="bg-white"
                />
              </div>
              <div>
                <Label className="text-slate-700 mb-2">API Secret</Label>
                <Input 
                  type="password"
                  value={credentials.twitter_api_secret}
                  onChange={(e) => handleChange('twitter_api_secret', e.target.value)}
                  placeholder="Twitter API Secret"
                  className="bg-white"
                />
              </div>
              <div>
                <Label className="text-slate-700 mb-2">Access Token</Label>
                <Input 
                  type="password"
                  value={credentials.twitter_access_token}
                  onChange={(e) => handleChange('twitter_access_token', e.target.value)}
                  placeholder="Access Token"
                  className="bg-white"
                />
              </div>
              <div>
                <Label className="text-slate-700 mb-2">Access Secret</Label>
                <Input 
                  type="password"
                  value={credentials.twitter_access_secret}
                  onChange={(e) => handleChange('twitter_access_secret', e.target.value)}
                  placeholder="Access Secret"
                  className="bg-white"
                />
              </div>
            </div>
          </Card>

          {/* Other Settings */}
          <Card className="p-6 glass border-white/30 mb-6">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Other Settings</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-700 mb-2">Website URL</Label>
                <Input 
                  value={credentials.website_url}
                  onChange={(e) => handleChange('website_url', e.target.value)}
                  placeholder="https://your-website.com"
                  className="bg-white"
                />
              </div>
              <div>
                <Label className="text-slate-700 mb-2">Google Analytics ID</Label>
                <Input 
                  value={credentials.google_analytics_id}
                  onChange={(e) => handleChange('google_analytics_id', e.target.value)}
                  placeholder="UA-XXXXXXXXX-X or G-XXXXXXXXXX"
                  className="bg-white"
                />
              </div>
            </div>
          </Card>

          {/* Save Button */}
          <div className="flex justify-end">
            <Button 
              onClick={handleSave}
              disabled={saving}
              className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white px-8 py-6 text-lg shadow-xl shadow-cyan-500/30"
            >
              <Save className="w-5 h-5 mr-2" />
              {saving ? 'Saving...' : 'Save Settings'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
