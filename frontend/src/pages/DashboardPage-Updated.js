import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Sparkles,
  ArrowLeft,
  TrendingUp,
  Users,
  Eye,
  Heart,
  Mail,
  Send,
  Calendar,
  BarChart3,
  Facebook,
  Instagram,
  Twitter,
  Linkedin,
  Globe,
  RefreshCw,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Clock
} from "lucide-react";
import { toast } from "sonner";
import {
  getDashboardOverview,
  getAggregatedAnalytics,
  getDateRange
} from "@/services/marketingApi";
import { DEFAULT_USER_ID } from "@/lib/api";

const PLATFORM_ICONS = {
  facebook: Facebook,
  instagram: Instagram,
  twitter: Twitter,
  linkedin: Linkedin
};

const PLATFORM_COLORS = {
  facebook: "text-blue-600 bg-blue-50",
  instagram: "text-pink-600 bg-pink-50",
  twitter: "text-slate-700 bg-slate-50",
  linkedin: "text-sky-600 bg-sky-50"
};

const DashboardPage = () => {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [overview, setOverview] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [dateRange, setDateRange] = useState(30); // days

  useEffect(() => {
    loadDashboard();
  }, [dateRange]);

  const loadDashboard = async () => {
    try {
      setLoading(true);

      // Load dashboard overview
      const overviewResponse = await getDashboardOverview(DEFAULT_USER_ID);
      setOverview(overviewResponse);

      // Load aggregated analytics
      const { dateFrom, dateTo } = getDateRange(dateRange);
      const analyticsResponse = await getAggregatedAnalytics(DEFAULT_USER_ID, dateFrom, dateTo);

      if (analyticsResponse.success) {
        setAnalytics(analyticsResponse.data);
      }
    } catch (error) {
      console.error('Error loading dashboard:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadDashboard();
    setRefreshing(false);
    toast.success('Dashboard refreshed');
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num;
  };

  const getPlatformIcon = (platform) => {
    const Icon = PLATFORM_ICONS[platform];
    return Icon || Globe;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-cyan-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const summary = analytics?.summary || {};
  const socialMedia = analytics?.social_media || {};
  const zoho = analytics?.zoho || {};
  const connectedAccounts = overview?.connected_accounts || [];
  const pendingJobs = overview?.pending_jobs || [];
  const tokenStatus = overview?.token_status || {};

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 to-indigo-50">
      {/* Navigation */}
      <nav className="bg-white/80 backdrop-blur-md fixed top-0 left-0 right-0 z-50 border-b border-white/20 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-600 to-blue-600 bg-clip-text text-transparent">
              Dashboard
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Button
              onClick={handleRefresh}
              disabled={refreshing}
              variant="outline"
              size="sm"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button onClick={() => navigate('/')} variant="outline">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Home
            </Button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="pt-24 pb-12 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Marketing Dashboard</h1>
            <p className="text-gray-600">Unified view of all your marketing metrics</p>
          </div>

          {/* Date Range Selector */}
          <div className="flex items-center gap-2 mb-6">
            <span className="text-sm text-gray-600">Time Period:</span>
            {[7, 30, 90].map((days) => (
              <Button
                key={days}
                size="sm"
                variant={dateRange === days ? "default" : "outline"}
                onClick={() => setDateRange(days)}
              >
                Last {days} days
              </Button>
            ))}
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card className="border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-blue-100">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardDescription className="text-blue-700">Total Impressions</CardDescription>
                  <Eye className="w-5 h-5 text-blue-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-blue-900">
                  {formatNumber(summary.total_social_impressions || 0)}
                </div>
                <p className="text-xs text-blue-700 mt-1">Across all platforms</p>
              </CardContent>
            </Card>

            <Card className="border-2 border-pink-200 bg-gradient-to-br from-pink-50 to-pink-100">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardDescription className="text-pink-700">Total Engagement</CardDescription>
                  <Heart className="w-5 h-5 text-pink-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-pink-900">
                  {formatNumber(summary.total_social_engagement || 0)}
                </div>
                <p className="text-xs text-pink-700 mt-1">
                  {summary.social_engagement_rate?.toFixed(1) || 0}% engagement rate
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 border-green-200 bg-gradient-to-br from-green-50 to-green-100">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardDescription className="text-green-700">Email Campaigns</CardDescription>
                  <Mail className="w-5 h-5 text-green-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-green-900">
                  {formatNumber(summary.total_email_sent || 0)}
                </div>
                <p className="text-xs text-green-700 mt-1">
                  {summary.email_open_rate?.toFixed(1) || 0}% open rate
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 border-purple-200 bg-gradient-to-br from-purple-50 to-purple-100">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardDescription className="text-purple-700">Total Leads</CardDescription>
                  <Users className="w-5 h-5 text-purple-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-purple-900">
                  {formatNumber(summary.total_leads || 0)}
                </div>
                <p className="text-xs text-purple-700 mt-1">From Zoho CRM</p>
              </CardContent>
            </Card>
          </div>

          {/* Main Tabs */}
          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">
                <BarChart3 className="w-4 h-4 mr-2" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="social">
                <Send className="w-4 h-4 mr-2" />
                Social Media
              </TabsTrigger>
              <TabsTrigger value="zoho">
                <Globe className="w-4 h-4 mr-2" />
                Zoho
              </TabsTrigger>
              <TabsTrigger value="scheduled">
                <Calendar className="w-4 h-4 mr-2" />
                Scheduled
              </TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Connected Accounts */}
                <Card>
                  <CardHeader>
                    <CardTitle>Connected Accounts</CardTitle>
                    <CardDescription>
                      {connectedAccounts.length} account(s) connected
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {connectedAccounts.length === 0 ? (
                      <Alert>
                        <AlertCircle className="w-4 h-4" />
                        <AlertDescription>
                          No accounts connected. Go to Settings to connect your accounts.
                        </AlertDescription>
                      </Alert>
                    ) : (
                      <div className="space-y-3">
                        {connectedAccounts.map((account) => {
                          const Icon = getPlatformIcon(account.platform);
                          const colorClass = PLATFORM_COLORS[account.platform] || "text-gray-600 bg-gray-50";

                          return (
                            <div key={account.account_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                              <div className="flex items-center gap-3">
                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colorClass}`}>
                                  <Icon className="w-5 h-5" />
                                </div>
                                <div>
                                  <p className="font-medium">{account.account_name || account.platform}</p>
                                  <p className="text-xs text-gray-500">{account.platform}</p>
                                </div>
                              </div>
                              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                                <CheckCircle2 className="w-3 h-3 mr-1" />
                                Active
                              </Badge>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Scheduled Posts */}
                <Card>
                  <CardHeader>
                    <CardTitle>Upcoming Scheduled Posts</CardTitle>
                    <CardDescription>
                      {pendingJobs.length} post(s) scheduled
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {pendingJobs.length === 0 ? (
                      <Alert>
                        <AlertCircle className="w-4 h-4" />
                        <AlertDescription>
                          No posts scheduled. Go to Social Media to schedule a post.
                        </AlertDescription>
                      </Alert>
                    ) : (
                      <div className="space-y-3">
                        {pendingJobs.slice(0, 5).map((job) => (
                          <div key={job.job_id} className="flex items-center justify-between p-3 bg-amber-50 rounded-lg border border-amber-200">
                            <div>
                              <p className="font-medium text-sm">Scheduled Post</p>
                              <p className="text-xs text-gray-600">
                                {new Date(job.scheduled_time).toLocaleString()}
                              </p>
                            </div>
                            <Clock className="w-4 h-4 text-amber-600" />
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Social Media Tab */}
            <TabsContent value="social">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {Object.entries(socialMedia).map(([platform, data]) => {
                  const Icon = getPlatformIcon(platform);
                  const colorClass = PLATFORM_COLORS[platform] || "text-gray-600 bg-gray-50";

                  return (
                    <Card key={platform} className="border-2">
                      <CardHeader>
                        <div className="flex items-center gap-3">
                          <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${colorClass}`}>
                            <Icon className="w-6 h-6" />
                          </div>
                          <div>
                            <CardTitle className="capitalize">{platform}</CardTitle>
                            <CardDescription>Performance metrics</CardDescription>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {/* Impressions */}
                          {(data.page_impressions || data.impressions) && (
                            <div>
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-sm text-gray-600">Impressions</span>
                                <span className="font-medium">
                                  {formatNumber(data.page_impressions || data.impressions)}
                                </span>
                              </div>
                              <Progress value={70} className="h-2" />
                            </div>
                          )}

                          {/* Engagement */}
                          {(data.page_engaged_users || data.engagement || data.total_likes) && (
                            <div>
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-sm text-gray-600">Engagement</span>
                                <span className="font-medium">
                                  {formatNumber(data.page_engaged_users || data.engagement || data.total_likes)}
                                </span>
                              </div>
                              <Progress value={60} className="h-2" />
                            </div>
                          )}

                          {/* Followers/Fans */}
                          {(data.page_fans || data.follower_count) && (
                            <div>
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-sm text-gray-600">Followers</span>
                                <span className="font-medium">
                                  {formatNumber(data.page_fans || data.follower_count)}
                                </span>
                              </div>
                              <Progress value={85} className="h-2" />
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>

              {Object.keys(socialMedia).length === 0 && (
                <Alert>
                  <AlertCircle className="w-4 h-4" />
                  <AlertDescription>
                    No social media data available. Connect your accounts in Settings to see analytics.
                  </AlertDescription>
                </Alert>
              )}
            </TabsContent>

            {/* Zoho Tab */}
            <TabsContent value="zoho">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* CRM Leads */}
                {zoho.crm_leads && (
                  <Card className="border-2 border-orange-200">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Users className="w-5 h-5 text-orange-600" />
                        CRM Leads
                      </CardTitle>
                      <CardDescription>Lead statistics from Zoho CRM</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="text-3xl font-bold">
                          {zoho.crm_leads.total_records || 0}
                        </div>

                        {zoho.crm_leads.by_status && (
                          <div className="space-y-2">
                            <p className="text-sm font-medium text-gray-700">By Status:</p>
                            {Object.entries(zoho.crm_leads.by_status).map(([status, count]) => (
                              <div key={status} className="flex items-center justify-between">
                                <span className="text-sm text-gray-600">{status}</span>
                                <Badge variant="secondary">{count}</Badge>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Email Campaigns */}
                {zoho.email_campaigns && (
                  <Card className="border-2 border-green-200">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Mail className="w-5 h-5 text-green-600" />
                        Email Campaigns
                      </CardTitle>
                      <CardDescription>Campaign performance from Zoho</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm text-gray-600">Campaigns</p>
                            <p className="text-2xl font-bold">{zoho.email_campaigns.total_campaigns || 0}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Sent</p>
                            <p className="text-2xl font-bold">
                              {formatNumber(zoho.email_campaigns.total_sent || 0)}
                            </p>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Open Rate</span>
                            <span className="font-medium">
                              {zoho.email_campaigns.avg_open_rate?.toFixed(1) || 0}%
                            </span>
                          </div>
                          <Progress value={zoho.email_campaigns.avg_open_rate || 0} className="h-2" />

                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Click Rate</span>
                            <span className="font-medium">
                              {zoho.email_campaigns.avg_click_rate?.toFixed(1) || 0}%
                            </span>
                          </div>
                          <Progress value={zoho.email_campaigns.avg_click_rate || 0} className="h-2" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>

              {!zoho.crm_leads && !zoho.email_campaigns && (
                <Alert>
                  <AlertCircle className="w-4 h-4" />
                  <AlertDescription>
                    No Zoho data available. Connect your Zoho account in Settings to see CRM and email analytics.
                  </AlertDescription>
                </Alert>
              )}
            </TabsContent>

            {/* Scheduled Tab */}
            <TabsContent value="scheduled">
              <Card>
                <CardHeader>
                  <CardTitle>All Scheduled Posts</CardTitle>
                  <CardDescription>Manage upcoming posts across all platforms</CardDescription>
                </CardHeader>
                <CardContent>
                  {pendingJobs.length === 0 ? (
                    <Alert>
                      <AlertCircle className="w-4 h-4" />
                      <AlertDescription>
                        No posts scheduled. Visit Social Media page to schedule posts.
                      </AlertDescription>
                    </Alert>
                  ) : (
                    <div className="space-y-3">
                      {pendingJobs.map((job) => (
                        <div key={job.job_id} className="p-4 border rounded-lg hover:shadow-md transition-shadow">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium">Scheduled Post</p>
                              <p className="text-sm text-gray-600">
                                {new Date(job.scheduled_time).toLocaleString()}
                              </p>
                              <p className="text-xs text-gray-500 mt-1">
                                Created: {new Date(job.created_at).toLocaleString()}
                              </p>
                            </div>
                            <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
                              <Clock className="w-3 h-3 mr-1" />
                              Pending
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Quick Actions */}
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              onClick={() => navigate('/social-media')}
              className="h-20 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600"
            >
              <div className="text-center">
                <Send className="w-6 h-6 mx-auto mb-1" />
                <span>Post to Social Media</span>
              </div>
            </Button>

            <Button
              onClick={() => navigate('/settings')}
              variant="outline"
              className="h-20"
            >
              <div className="text-center">
                <TrendingUp className="w-6 h-6 mx-auto mb-1" />
                <span>Connect Accounts</span>
              </div>
            </Button>

            <Button
              onClick={() => navigate('/analytics')}
              variant="outline"
              className="h-20"
            >
              <div className="text-center">
                <BarChart3 className="w-6 h-6 mx-auto mb-1" />
                <span>View Analytics</span>
              </div>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
