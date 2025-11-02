import React, { useEffect, useState } from "react";
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
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import {
  Share2,
  Send,
  CalendarClock,
  RefreshCw,
  Loader2,
  Sparkles,
  Trash2,
  ArrowLeft,
  CheckCircle2,
  Clock,
  AlertCircle,
  Facebook,
  Instagram,
  Twitter,
  Linkedin,
  X,
  Calendar,
  Image as ImageIcon,
  Link as LinkIcon
} from "lucide-react";
import { format } from "date-fns";
import {
  getConnectedAccounts,
  postToMultipleAccounts,
  schedulePost,
  getUserJobs,
  cancelJob,
  buildScheduleTime
} from "@/services/marketingApi";
import { DEFAULT_USER_ID } from "@/lib/api";

const PLATFORM_ICONS = {
  facebook: Facebook,
  instagram: Instagram,
  twitter: Twitter,
  linkedin: Linkedin
};

const PLATFORM_COLORS = {
  facebook: "text-blue-600",
  instagram: "text-pink-600",
  twitter: "text-slate-700",
  linkedin: "text-sky-600"
};

const JOB_STATUS_STYLES = {
  pending: { badge: "bg-amber-50 text-amber-700 border-amber-200", icon: Clock },
  processing: { badge: "bg-blue-50 text-blue-700 border-blue-200", icon: Loader2 },
  completed: { badge: "bg-green-50 text-green-700 border-green-200", icon: CheckCircle2 },
  failed: { badge: "bg-red-50 text-red-700 border-red-200", icon: AlertCircle },
  cancelled: { badge: "bg-gray-50 text-gray-600 border-gray-200", icon: X }
};

const SocialMediaDashboard = () => {
  const navigate = useNavigate();

  // Accounts State
  const [accounts, setAccounts] = useState([]);
  const [accountsLoading, setAccountsLoading] = useState(true);
  const [selectedAccounts, setSelectedAccounts] = useState([]);

  // Post Content State
  const [content, setContent] = useState({
    text: "",
    image_url: "",
    video_url: "",
    link: ""
  });

  // Posting State
  const [posting, setPosting] = useState(false);
  const [postResult, setPostResult] = useState(null);

  // Scheduling State
  const [scheduleDate, setScheduleDate] = useState("");
  const [scheduleTime, setScheduleTime] = useState("");
  const [scheduling, setScheduling] = useState(false);
  const [scheduleResult, setScheduleResult] = useState(null);

  // Jobs State
  const [jobs, setJobs] = useState([]);
  const [jobsLoading, setJobsLoading] = useState(true);
  const [jobFilter, setJobFilter] = useState("pending");
  const [cancellingJobId, setCancellingJobId] = useState(null);

  // Active Tab
  const [activeTab, setActiveTab] = useState("post");

  useEffect(() => {
    loadAccounts();
    loadJobs();

    // Refresh jobs every 30 seconds
    const interval = setInterval(loadJobs, 30000);
    return () => clearInterval(interval);
  }, [jobFilter]);

  const loadAccounts = async () => {
    try {
      setAccountsLoading(true);
      const response = await getConnectedAccounts(DEFAULT_USER_ID);

      if (response.success) {
        setAccounts(response.accounts || []);
      }
    } catch (error) {
      console.error('Error loading accounts:', error);
      toast.error('Failed to load connected accounts');
    } finally {
      setAccountsLoading(false);
    }
  };

  const loadJobs = async () => {
    try {
      setJobsLoading(true);
      const response = await getUserJobs(
        DEFAULT_USER_ID,
        jobFilter === "all" ? null : jobFilter,
        "scheduled_post"
      );

      if (response.success) {
        setJobs(response.jobs || []);
      }
    } catch (error) {
      console.error('Error loading jobs:', error);
    } finally {
      setJobsLoading(false);
    }
  };

  const handleSelectAccount = (accountId) => {
    setSelectedAccounts(prev =>
      prev.includes(accountId)
        ? prev.filter(id => id !== accountId)
        : [...prev, accountId]
    );
  };

  const handleSelectAll = () => {
    if (selectedAccounts.length === accounts.length) {
      setSelectedAccounts([]);
    } else {
      setSelectedAccounts(accounts.map(acc => acc.account_id));
    }
  };

  const handlePostNow = async () => {
    if (selectedAccounts.length === 0) {
      toast.error('Please select at least one account');
      return;
    }

    if (!content.text && !content.image_url && !content.video_url) {
      toast.error('Please add some content to post');
      return;
    }

    try {
      setPosting(true);
      setPostResult(null);

      const postContent = {};
      if (content.text) postContent.text = content.text;
      if (content.image_url) postContent.image_url = content.image_url;
      if (content.video_url) postContent.video_url = content.video_url;
      if (content.link) postContent.link = content.link;

      const response = await postToMultipleAccounts(
        selectedAccounts,
        postContent,
        DEFAULT_USER_ID
      );

      if (response.success) {
        setPostResult(response);
        toast.success(`Posted to ${response.summary.successful} account(s) successfully!`);

        // Clear content
        setContent({ text: "", image_url: "", video_url: "", link: "" });
        setSelectedAccounts([]);
      } else {
        toast.error('Failed to post to accounts');
      }
    } catch (error) {
      console.error('Error posting:', error);
      toast.error('Failed to post to social media');
    } finally {
      setPosting(false);
    }
  };

  const handleSchedulePost = async () => {
    if (selectedAccounts.length === 0) {
      toast.error('Please select at least one account');
      return;
    }

    if (!content.text && !content.image_url && !content.video_url) {
      toast.error('Please add some content to post');
      return;
    }

    if (!scheduleDate || !scheduleTime) {
      toast.error('Please select date and time for scheduling');
      return;
    }

    try {
      setScheduling(true);
      setScheduleResult(null);

      const postContent = {};
      if (content.text) postContent.text = content.text;
      if (content.image_url) postContent.image_url = content.image_url;
      if (content.video_url) postContent.video_url = content.video_url;
      if (content.link) postContent.link = content.link;

      const scheduledTime = buildScheduleTime(new Date(scheduleDate), scheduleTime);

      const response = await schedulePost(
        selectedAccounts,
        postContent,
        scheduledTime,
        DEFAULT_USER_ID
      );

      if (response.success) {
        setScheduleResult(response);
        toast.success('Post scheduled successfully!');

        // Clear content and scheduling info
        setContent({ text: "", image_url: "", video_url: "", link: "" });
        setSelectedAccounts([]);
        setScheduleDate("");
        setScheduleTime("");

        // Reload jobs
        loadJobs();

        // Switch to scheduled tab
        setActiveTab("scheduled");
      } else {
        toast.error('Failed to schedule post');
      }
    } catch (error) {
      console.error('Error scheduling:', error);
      toast.error('Failed to schedule post');
    } finally {
      setScheduling(false);
    }
  };

  const handleCancelJob = async (jobId) => {
    try {
      setCancellingJobId(jobId);
      const response = await cancelJob(jobId);

      if (response.success) {
        toast.success('Scheduled post cancelled');
        loadJobs();
      }
    } catch (error) {
      console.error('Error cancelling job:', error);
      toast.error('Failed to cancel job');
    } finally {
      setCancellingJobId(null);
    }
  };

  const getAccountById = (accountId) => {
    return accounts.find(acc => acc.account_id === accountId);
  };

  const getPlatformIcon = (platform) => {
    const Icon = PLATFORM_ICONS[platform];
    return Icon ? <Icon className={`w-4 h-4 ${PLATFORM_COLORS[platform]}`} /> : null;
  };

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
              Social Media Manager
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={() => navigate('/settings')} variant="outline">
              Connect Accounts
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
          {/* Header Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Connected Accounts</CardDescription>
                <CardTitle className="text-3xl">{accounts.length}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Selected for Posting</CardDescription>
                <CardTitle className="text-3xl">{selectedAccounts.length}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Scheduled Posts</CardDescription>
                <CardTitle className="text-3xl">
                  {jobs.filter(j => j.status === 'pending').length}
                </CardTitle>
              </CardHeader>
            </Card>
          </div>

          {/* Main Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2 mb-6">
              <TabsTrigger value="post">
                <Send className="w-4 h-4 mr-2" />
                Create & Post
              </TabsTrigger>
              <TabsTrigger value="scheduled">
                <CalendarClock className="w-4 h-4 mr-2" />
                Scheduled Posts
              </TabsTrigger>
            </TabsList>

            {/* Post Tab */}
            <TabsContent value="post">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Account Selection */}
                <Card className="lg:col-span-1">
                  <CardHeader>
                    <CardTitle>Select Accounts</CardTitle>
                    <CardDescription>Choose where to post</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {accountsLoading ? (
                      <div className="flex justify-center py-8">
                        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                      </div>
                    ) : accounts.length === 0 ? (
                      <Alert>
                        <AlertCircle className="w-4 h-4" />
                        <AlertDescription>
                          No accounts connected. Go to Settings to connect your social media accounts.
                        </AlertDescription>
                      </Alert>
                    ) : (
                      <div className="space-y-3">
                        <div className="flex items-center space-x-2 pb-2 border-b">
                          <Checkbox
                            id="select-all"
                            checked={selectedAccounts.length === accounts.length}
                            onCheckedChange={handleSelectAll}
                          />
                          <Label htmlFor="select-all" className="font-medium cursor-pointer">
                            Select All ({accounts.length})
                          </Label>
                        </div>

                        {accounts.map((account) => (
                          <div key={account.account_id} className="flex items-center space-x-2 p-2 hover:bg-gray-50 rounded">
                            <Checkbox
                              id={account.account_id}
                              checked={selectedAccounts.includes(account.account_id)}
                              onCheckedChange={() => handleSelectAccount(account.account_id)}
                            />
                            <Label htmlFor={account.account_id} className="flex items-center gap-2 cursor-pointer flex-1">
                              {getPlatformIcon(account.platform)}
                              <span>{account.account_name || account.platform}</span>
                            </Label>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Post Composer */}
                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle>Compose Post</CardTitle>
                    <CardDescription>Create content for your selected accounts</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Text Content */}
                    <div>
                      <Label htmlFor="post-text">Post Text</Label>
                      <Textarea
                        id="post-text"
                        placeholder="What's on your mind?"
                        value={content.text}
                        onChange={(e) => setContent({ ...content, text: e.target.value })}
                        rows={6}
                        className="resize-none"
                      />
                    </div>

                    {/* Image URL */}
                    <div>
                      <Label htmlFor="image-url" className="flex items-center gap-2">
                        <ImageIcon className="w-4 h-4" />
                        Image URL (optional)
                      </Label>
                      <Input
                        id="image-url"
                        type="url"
                        placeholder="https://example.com/image.jpg"
                        value={content.image_url}
                        onChange={(e) => setContent({ ...content, image_url: e.target.value })}
                      />
                    </div>

                    {/* Video URL */}
                    <div>
                      <Label htmlFor="video-url" className="flex items-center gap-2">
                        <Share2 className="w-4 h-4" />
                        Video URL (optional)
                      </Label>
                      <Input
                        id="video-url"
                        type="url"
                        placeholder="https://example.com/video.mp4"
                        value={content.video_url}
                        onChange={(e) => setContent({ ...content, video_url: e.target.value })}
                      />
                    </div>

                    {/* Link */}
                    <div>
                      <Label htmlFor="link-url" className="flex items-center gap-2">
                        <LinkIcon className="w-4 h-4" />
                        Link (optional)
                      </Label>
                      <Input
                        id="link-url"
                        type="url"
                        placeholder="https://example.com/article"
                        value={content.link}
                        onChange={(e) => setContent({ ...content, link: e.target.value })}
                      />
                    </div>

                    <Separator />

                    {/* Scheduling */}
                    <div className="space-y-3">
                      <Label className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        Schedule Post (optional)
                      </Label>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label htmlFor="schedule-date" className="text-sm text-gray-600">Date</Label>
                          <Input
                            id="schedule-date"
                            type="date"
                            value={scheduleDate}
                            onChange={(e) => setScheduleDate(e.target.value)}
                            min={new Date().toISOString().split('T')[0]}
                          />
                        </div>
                        <div>
                          <Label htmlFor="schedule-time" className="text-sm text-gray-600">Time</Label>
                          <Input
                            id="schedule-time"
                            type="time"
                            value={scheduleTime}
                            onChange={(e) => setScheduleTime(e.target.value)}
                          />
                        </div>
                      </div>
                    </div>

                    <Separator />

                    {/* Action Buttons */}
                    <div className="flex gap-3">
                      <Button
                        onClick={handlePostNow}
                        disabled={posting || selectedAccounts.length === 0}
                        className="flex-1 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600"
                      >
                        {posting ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Posting...
                          </>
                        ) : (
                          <>
                            <Send className="w-4 h-4 mr-2" />
                            Post Now
                          </>
                        )}
                      </Button>

                      {(scheduleDate && scheduleTime) && (
                        <Button
                          onClick={handleSchedulePost}
                          disabled={scheduling || selectedAccounts.length === 0}
                          variant="outline"
                          className="flex-1"
                        >
                          {scheduling ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Scheduling...
                            </>
                          ) : (
                            <>
                              <CalendarClock className="w-4 h-4 mr-2" />
                              Schedule Post
                            </>
                          )}
                        </Button>
                      )}
                    </div>

                    {/* Post Result */}
                    {postResult && (
                      <Alert className="border-green-200 bg-green-50">
                        <CheckCircle2 className="w-4 h-4 text-green-600" />
                        <AlertDescription className="text-green-800">
                          <strong>Success!</strong> Posted to {postResult.summary.successful} account(s)
                          {postResult.summary.failed > 0 && `, ${postResult.summary.failed} failed`}
                        </AlertDescription>
                      </Alert>
                    )}

                    {/* Schedule Result */}
                    {scheduleResult && (
                      <Alert className="border-blue-200 bg-blue-50">
                        <Clock className="w-4 h-4 text-blue-600" />
                        <AlertDescription className="text-blue-800">
                          <strong>Scheduled!</strong> Post will be published at {new Date(scheduleResult.scheduled_time).toLocaleString()}
                        </AlertDescription>
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Scheduled Posts Tab */}
            <TabsContent value="scheduled">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Scheduled Posts</CardTitle>
                      <CardDescription>Manage your upcoming posts</CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setJobFilter("pending")}
                        className={jobFilter === "pending" ? "bg-amber-50" : ""}
                      >
                        Pending
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setJobFilter("completed")}
                        className={jobFilter === "completed" ? "bg-green-50" : ""}
                      >
                        Completed
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setJobFilter("all")}
                        className={jobFilter === "all" ? "bg-blue-50" : ""}
                      >
                        All
                      </Button>
                      <Button size="sm" variant="ghost" onClick={loadJobs}>
                        <RefreshCw className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {jobsLoading ? (
                    <div className="flex justify-center py-8">
                      <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                    </div>
                  ) : jobs.length === 0 ? (
                    <Alert>
                      <AlertCircle className="w-4 h-4" />
                      <AlertDescription>
                        No scheduled posts found. Create a post and schedule it for later!
                      </AlertDescription>
                    </Alert>
                  ) : (
                    <div className="space-y-3">
                      {jobs.map((job) => {
                        const StatusIcon = JOB_STATUS_STYLES[job.status]?.icon || Clock;

                        return (
                          <div key={job.job_id} className="p-4 border rounded-lg hover:shadow-md transition-shadow">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  <Badge variant="outline" className={JOB_STATUS_STYLES[job.status]?.badge}>
                                    <StatusIcon className="w-3 h-3 mr-1" />
                                    {job.status}
                                  </Badge>
                                  <span className="text-sm text-gray-500">
                                    {format(new Date(job.scheduled_time), 'MMM dd, yyyy HH:mm')}
                                  </span>
                                </div>

                                <p className="text-sm text-gray-600 mb-2">
                                  Created: {format(new Date(job.created_at), 'MMM dd, yyyy HH:mm')}
                                </p>

                                {/* Show accounts this job will post to */}
                                <div className="flex items-center gap-2 flex-wrap">
                                  {job.account_ids && job.account_ids.map((accountId) => {
                                    const account = getAccountById(accountId);
                                    return account ? (
                                      <Badge key={accountId} variant="secondary" className="text-xs">
                                        {getPlatformIcon(account.platform)}
                                        <span className="ml-1">{account.account_name || account.platform}</span>
                                      </Badge>
                                    ) : null;
                                  })}
                                </div>
                              </div>

                              {job.status === 'pending' && (
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleCancelJob(job.job_id)}
                                  disabled={cancellingJobId === job.job_id}
                                >
                                  {cancellingJobId === job.job_id ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                  ) : (
                                    <Trash2 className="w-4 h-4 text-red-500" />
                                  )}
                                </Button>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default SocialMediaDashboard;
