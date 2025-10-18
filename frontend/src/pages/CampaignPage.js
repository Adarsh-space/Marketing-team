import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Sparkles, Target, Clock, CheckCircle2, TrendingUp, Mail, Share2, Search, DollarSign, BarChart3, FileText, ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CampaignPage = () => {
  const { campaignId } = useParams();
  const navigate = useNavigate();
  const [campaign, setCampaign] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCampaign();
  }, [campaignId]);

  const loadCampaign = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/campaigns/${campaignId}`);
      setCampaign(response.data);
    } catch (error) {
      console.error('Error loading campaign:', error);
      toast.error('Failed to load campaign');
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const getAgentIcon = (agentName) => {
    const icons = {
      'MarketResearchAgent': <TrendingUp className="w-5 h-5" />,
      'ContentAgent': <FileText className="w-5 h-5" />,
      'EmailAgent': <Mail className="w-5 h-5" />,
      'SocialMediaAgent': <Share2 className="w-5 h-5" />,
      'SEOAgent': <Search className="w-5 h-5" />,
      'PPCAgent': <DollarSign className="w-5 h-5" />,
      'AnalyticsAgent': <BarChart3 className="w-5 h-5" />,
      'ReportingAgent': <FileText className="w-5 h-5" />
    };
    return icons[agentName] || <Target className="w-5 h-5" />;
  };

  const getAgentColor = (agentName) => {
    const colors = {
      'MarketResearchAgent': 'from-purple-400 to-purple-600',
      'ContentAgent': 'from-pink-400 to-pink-600',
      'EmailAgent': 'from-blue-400 to-blue-600',
      'SocialMediaAgent': 'from-green-400 to-green-600',
      'SEOAgent': 'from-yellow-400 to-yellow-600',
      'PPCAgent': 'from-red-400 to-red-600',
      'AnalyticsAgent': 'from-indigo-400 to-indigo-600',
      'ReportingAgent': 'from-cyan-400 to-cyan-600'
    };
    return colors[agentName] || 'from-gray-400 to-gray-600';
  };

  const formatAgentName = (name) => {
    return name.replace('Agent', '').replace(/([A-Z])/g, ' $1').trim();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center mx-auto mb-4 animate-pulse shadow-lg shadow-cyan-500/30">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <p className="text-slate-600">Loading campaign...</p>
        </div>
      </div>
    );
  }

  if (!campaign) return null;

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
            onClick={() => navigate('/dashboard')}
            variant="outline"
            className="border-cyan-200 hover:bg-cyan-50"
            data-testid="back-to-dashboard-btn"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
        </div>
      </nav>

      {/* Campaign Content */}
      <div className="pt-24 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Campaign Header */}
          <Card className="p-8 glass border-white/30 mb-8 shadow-xl">
            <div className="flex items-start justify-between mb-6">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-4">
                  <Badge className="bg-green-100 text-green-700 border-green-200" data-testid="campaign-status-badge">
                    <CheckCircle2 className="w-4 h-4 mr-1" />
                    {campaign.status}
                  </Badge>
                  <span className="text-sm text-slate-500">
                    Created {new Date(campaign.created_at).toLocaleDateString()}
                  </span>
                </div>
                <h1 className="text-3xl font-bold mb-3 text-slate-800" data-testid="campaign-title">
                  {campaign.brief?.product || 'Marketing Campaign'}
                </h1>
                <p className="text-lg text-slate-600 mb-4" data-testid="campaign-objective">
                  {campaign.brief?.objective}
                </p>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline" className="border-cyan-200 text-cyan-700">
                    <Target className="w-3 h-3 mr-1" />
                    {campaign.brief?.target_audience}
                  </Badge>
                  <Badge variant="outline" className="border-cyan-200 text-cyan-700">
                    <Clock className="w-3 h-3 mr-1" />
                    {campaign.brief?.timeline}
                  </Badge>
                  {campaign.brief?.budget && (
                    <Badge variant="outline" className="border-cyan-200 text-cyan-700">
                      <DollarSign className="w-3 h-3 mr-1" />
                      {campaign.brief?.budget}
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            {/* Channels */}
            <div className="flex flex-wrap gap-2 pt-4 border-t border-white/20">
              <span className="text-sm font-medium text-slate-600 mr-2">Channels:</span>
              {campaign.brief?.channels?.map((channel, i) => (
                <Badge key={i} className="bg-cyan-100 text-cyan-700 border-cyan-200">
                  {channel}
                </Badge>
              ))}
            </div>
          </Card>

          {/* Tabs */}
          <Tabs defaultValue="plan" className="space-y-6">
            <TabsList className="glass border-white/30 p-1.5" data-testid="campaign-tabs">
              <TabsTrigger value="plan" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-cyan-500 data-[state=active]:to-blue-500 data-[state=active]:text-white" data-testid="plan-tab">Campaign Plan</TabsTrigger>
              <TabsTrigger value="results" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-cyan-500 data-[state=active]:to-blue-500 data-[state=active]:text-white" data-testid="results-tab">Agent Results</TabsTrigger>
            </TabsList>

            {/* Campaign Plan Tab */}
            <TabsContent value="plan" className="space-y-6">
              {campaign.plan ? (
                <>
                  {/* Plan Overview */}
                  <Card className="p-6 glass border-white/30" data-testid="plan-overview">
                    <h2 className="text-xl font-semibold mb-4 text-slate-800">Campaign Overview</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-slate-600 mb-1">Campaign Name</p>
                        <p className="font-medium text-slate-800">{campaign.plan.campaign_name}</p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-600 mb-1">Duration</p>
                        <p className="font-medium text-slate-800">{campaign.plan.timeline_days} days</p>
                      </div>
                    </div>
                  </Card>

                  {/* Tasks */}
                  <Card className="p-6 glass border-white/30">
                    <h2 className="text-xl font-semibold mb-4 text-slate-800" data-testid="tasks-title">Campaign Tasks</h2>
                    <Accordion type="single" collapsible className="space-y-3">
                      {campaign.plan.tasks?.map((task, index) => (
                        <AccordionItem 
                          key={task.task_id} 
                          value={task.task_id}
                          className="glass border-white/30 rounded-xl overflow-hidden"
                          data-testid={`task-accordion-${index}`}
                        >
                          <AccordionTrigger className="px-6 hover:no-underline hover:bg-white/50 transition-all">
                            <div className="flex items-center gap-4 flex-1 text-left">
                              <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${getAgentColor(task.agent_assigned)} flex items-center justify-center text-white shadow-lg`}>
                                {getAgentIcon(task.agent_assigned)}
                              </div>
                              <div className="flex-1">
                                <h3 className="font-semibold text-slate-800">{task.task_name}</h3>
                                <p className="text-sm text-slate-600">{formatAgentName(task.agent_assigned)}</p>
                              </div>
                              <Badge variant="outline" className="border-cyan-200 text-cyan-700">
                                {task.estimated_duration_days} days
                              </Badge>
                            </div>
                          </AccordionTrigger>
                          <AccordionContent className="px-6 pb-6">
                            <div className="pt-4 space-y-3">
                              <div>
                                <p className="text-sm font-medium text-slate-700 mb-1">Description</p>
                                <p className="text-sm text-slate-600">{task.description}</p>
                              </div>
                              {task.dependencies?.length > 0 && (
                                <div>
                                  <p className="text-sm font-medium text-slate-700 mb-1">Dependencies</p>
                                  <div className="flex flex-wrap gap-2">
                                    {task.dependencies.map(dep => (
                                      <Badge key={dep} variant="outline" className="text-xs border-slate-200">
                                        {dep}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </AccordionContent>
                        </AccordionItem>
                      ))}
                    </Accordion>
                  </Card>

                  {/* KPIs */}
                  {campaign.plan.kpis && campaign.plan.kpis.length > 0 && (
                    <Card className="p-6 glass border-white/30" data-testid="kpis-card">
                      <h2 className="text-xl font-semibold mb-4 text-slate-800">Key Performance Indicators</h2>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {campaign.plan.kpis.map((kpi, index) => (
                          <div key={index} className="p-4 bg-white/50 rounded-xl border border-white/30">
                            <p className="text-sm text-slate-600 mb-1">{kpi.metric}</p>
                            <p className="text-lg font-semibold text-slate-800">{kpi.target}</p>
                          </div>
                        ))}
                      </div>
                    </Card>
                  )}
                </>
              ) : (
                <Card className="p-12 glass border-white/30 text-center">
                  <p className="text-slate-600">No plan available for this campaign</p>
                </Card>
              )}
            </TabsContent>

            {/* Results Tab */}
            <TabsContent value="results" className="space-y-6">
              {campaign.results && Object.keys(campaign.results).length > 0 ? (
                <div className="space-y-4">
                  {Object.entries(campaign.results).map(([taskId, result], index) => (
                    <Card key={taskId} className="p-6 glass border-white/30" data-testid={`result-card-${index}`}>
                      <div className="flex items-start gap-4 mb-4">
                        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${getAgentColor(result.agent)} flex items-center justify-center text-white shadow-lg`}>
                          {getAgentIcon(result.agent)}
                        </div>
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold mb-1 text-slate-800">{formatAgentName(result.agent)}</h3>
                          <p className="text-sm text-slate-600">Task ID: {taskId}</p>
                        </div>
                        <Badge className={result.status === 'success' ? 'bg-green-100 text-green-700 border-green-200' : 'bg-red-100 text-red-700 border-red-200'}>
                          {result.status}
                        </Badge>
                      </div>
                      <div className="bg-white/50 p-4 rounded-xl border border-white/30">
                        <pre className="text-sm text-slate-700 whitespace-pre-wrap overflow-x-auto max-h-96 overflow-y-auto">
                          {typeof result.result === 'object' ? JSON.stringify(result.result, null, 2) : result.result}
                        </pre>
                      </div>
                    </Card>
                  ))}
                </div>
              ) : (
                <Card className="p-12 glass border-white/30 text-center">
                  <div className="w-20 h-20 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center mx-auto mb-6 shadow-lg shadow-cyan-500/30">
                    <Clock className="w-10 h-10 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2 text-slate-800">No results yet</h3>
                  <p className="text-slate-600">Campaign is still being executed or no results have been generated</p>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default CampaignPage;
