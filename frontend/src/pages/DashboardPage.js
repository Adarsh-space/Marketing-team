import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkles, TrendingUp, Target, Clock, ArrowRight, BarChart3, CheckCircle2, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DashboardPage = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/analytics/dashboard`);
      setStats(response.data.stats);
      setCampaigns(response.data.recent_campaigns);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      completed: 'bg-green-100 text-green-700 border-green-200',
      planning: 'bg-blue-100 text-blue-700 border-blue-200',
      executing: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      failed: 'bg-red-100 text-red-700 border-red-200'
    };
    return colors[status] || 'bg-gray-100 text-gray-700 border-gray-200';
  };

  const getStatusIcon = (status) => {
    if (status === 'completed') return <CheckCircle2 className="w-4 h-4" />;
    if (status === 'failed') return <AlertCircle className="w-4 h-4" />;
    return <Clock className="w-4 h-4" />;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center mx-auto mb-4 animate-pulse shadow-lg shadow-cyan-500/30">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <p className="text-slate-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

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
            data-testid="home-nav-btn"
          >
            Back to Home
          </Button>
        </div>
      </nav>

      {/* Dashboard Content */}
      <div className="pt-24 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-12">
            <h1 className="text-4xl font-bold mb-3 text-slate-800" data-testid="dashboard-title">Campaign Dashboard</h1>
            <p className="text-lg text-slate-600">Monitor and manage your AI-powered marketing campaigns</p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <Card className="p-6 glass border-white/30 hover:shadow-xl transition-all" data-testid="total-campaigns-card">
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/30">
                  <Target className="w-6 h-6 text-white" />
                </div>
                <Badge className="bg-cyan-100 text-cyan-700 border-cyan-200">Total</Badge>
              </div>
              <h3 className="text-3xl font-bold mb-1 text-slate-800">{stats?.total_campaigns || 0}</h3>
              <p className="text-sm text-slate-600">Total Campaigns</p>
            </Card>

            <Card className="p-6 glass border-white/30 hover:shadow-xl transition-all" data-testid="active-campaigns-card">
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center shadow-lg shadow-yellow-500/30">
                  <Clock className="w-6 h-6 text-white" />
                </div>
                <Badge className="bg-yellow-100 text-yellow-700 border-yellow-200">Active</Badge>
              </div>
              <h3 className="text-3xl font-bold mb-1 text-slate-800">{stats?.active_campaigns || 0}</h3>
              <p className="text-sm text-slate-600">In Progress</p>
            </Card>

            <Card className="p-6 glass border-white/30 hover:shadow-xl transition-all" data-testid="completed-campaigns-card">
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center shadow-lg shadow-green-500/30">
                  <CheckCircle2 className="w-6 h-6 text-white" />
                </div>
                <Badge className="bg-green-100 text-green-700 border-green-200">Done</Badge>
              </div>
              <h3 className="text-3xl font-bold mb-1 text-slate-800">{stats?.completed_campaigns || 0}</h3>
              <p className="text-sm text-slate-600">Completed</p>
            </Card>
          </div>

          {/* Recent Campaigns */}
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-slate-800" data-testid="recent-campaigns-title">Recent Campaigns</h2>
              <Button 
                onClick={() => navigate('/')}
                className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white shadow-lg shadow-cyan-500/30"
                data-testid="create-new-campaign-btn"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                Create New Campaign
              </Button>
            </div>

            {campaigns.length === 0 ? (
              <Card className="p-12 glass border-white/30 text-center" data-testid="no-campaigns-message">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center mx-auto mb-6 shadow-lg shadow-cyan-500/30">
                  <Target className="w-10 h-10 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-2 text-slate-800">No campaigns yet</h3>
                <p className="text-slate-600 mb-6">Create your first AI-powered marketing campaign to get started</p>
                <Button 
                  onClick={() => navigate('/')}
                  className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white shadow-lg shadow-cyan-500/30"
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  Get Started
                </Button>
              </Card>
            ) : (
              <div className="space-y-4">
                {campaigns.map((campaign, index) => (
                  <Card 
                    key={campaign.campaign_id} 
                    className="p-6 glass border-white/30 hover:shadow-xl hover:-translate-y-0.5 transition-all cursor-pointer"
                    onClick={() => navigate(`/campaign/${campaign.campaign_id}`)}
                    data-testid={`campaign-card-${index}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <Badge className={getStatusColor(campaign.status)} data-testid={`campaign-status-${index}`}>
                            {getStatusIcon(campaign.status)}
                            <span className="ml-1.5 capitalize">{campaign.status}</span>
                          </Badge>
                          <span className="text-sm text-slate-500">
                            {new Date(campaign.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        <h3 className="text-lg font-semibold mb-2 text-slate-800">
                          {campaign.brief?.product || 'Marketing Campaign'}
                        </h3>
                        <p className="text-sm text-slate-600 mb-3 line-clamp-2">
                          {campaign.brief?.objective || 'No objective specified'}
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {campaign.brief?.channels?.slice(0, 3).map((channel, i) => (
                            <Badge key={i} variant="outline" className="text-xs border-cyan-200 text-cyan-700">
                              {channel}
                            </Badge>
                          ))}
                          {campaign.brief?.channels?.length > 3 && (
                            <Badge variant="outline" className="text-xs border-cyan-200 text-cyan-700">
                              +{campaign.brief.channels.length - 3} more
                            </Badge>
                          )}
                        </div>
                      </div>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        className="ml-4"
                        data-testid={`view-campaign-${index}`}
                      >
                        <ArrowRight className="w-5 h-5" />
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
