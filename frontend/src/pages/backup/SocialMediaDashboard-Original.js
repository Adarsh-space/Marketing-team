import React, { useCallback, useEffect, useMemo, useState } from "react";
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
import { toast } from "sonner";
import {
  Share2,
  Send,
  CalendarClock,
  RefreshCw,
  Loader2,
  Layers,
  CheckCircle2,
  AlertCircle,
  Clock,
  Target,
  ListChecks,
  Sparkles,
  Trash2,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { api, DEFAULT_USER_ID, handleApiError } from "@/lib/api";
import {
  SOCIAL_PLATFORMS,
  getPlatformLabel,
} from "@/constants/socialPlatforms";

const INITIAL_CONTENT = {
  text: "",
  imageUrl: "",
  videoUrl: "",
  link: "",
};

const JOB_STATUS_STYLES = {
  pending: "border-amber-200 bg-amber-50 text-amber-700",
  processing: "border-blue-200 bg-blue-50 text-blue-700",
  completed: "border-emerald-200 bg-emerald-50 text-emerald-700",
  failed: "border-red-200 bg-red-50 text-red-700",
  cancelled: "border-slate-200 bg-slate-50 text-slate-600",
};

const parseDateValue = (value) => {
  if (!value) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const buildContentPayload = (content) => {
  const payload = {};
  if (content.text?.trim()) payload.text = content.text.trim();
  if (content.imageUrl?.trim()) payload.image_url = content.imageUrl.trim();
  if (content.videoUrl?.trim()) payload.video_url = content.videoUrl.trim();
  if (content.link?.trim()) payload.link = content.link.trim();
  return payload;
};

const SocialMediaDashboard = () => {
  const navigate = useNavigate();

  const [accounts, setAccounts] = useState([]);
  const [accountsLoading, setAccountsLoading] = useState(true);
  const [isRefreshingAccounts, setIsRefreshingAccounts] = useState(false);
  const [selectedAccounts, setSelectedAccounts] = useState([]);
  const [content, setContent] = useState(INITIAL_CONTENT);
  const [posting, setPosting] = useState(false);
  const [postResult, setPostResult] = useState(null);
  const [scheduleDate, setScheduleDate] = useState("");
  const [scheduleTime, setScheduleTime] = useState("");
  const [scheduling, setScheduling] = useState(false);
  const [scheduledResult, setScheduledResult] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [jobsLoading, setJobsLoading] = useState(true);
  const [jobFilter, setJobFilter] = useState("pending");
  const [cancellingJobId, setCancellingJobId] = useState(null);
  const [lastAccountsSyncAt, setLastAccountsSyncAt] = useState(null);
  const [lastJobsSyncAt, setLastJobsSyncAt] = useState(null);

  const totalConnected = accounts.length;
  const selectedCount = selectedAccounts.length;

  const accountsByPlatform = useMemo(() => {
    return SOCIAL_PLATFORMS.reduce((acc, platform) => {
      acc[platform.id] = accounts.filter(
        (account) => account.platform === platform.id
      );
      return acc;
    }, {});
  }, [accounts]);

  useEffect(() => {
    setSelectedAccounts((prev) =>
      prev.filter((accountId) =>
        accounts.some((account) => account.account_id === accountId)
      )
    );
  }, [accounts]);

  const fetchAccounts = useCallback(
    async ({ silent = false } = {}) => {
      if (!silent) {
        setAccountsLoading(true);
      }
      setIsRefreshingAccounts(true);
      try {
        const data = await api.get("/social/accounts", {
          params: { user_id: DEFAULT_USER_ID },
        });
        const list = Array.isArray(data?.accounts) ? data.accounts : [];
        setAccounts(list);
        setLastAccountsSyncAt(new Date());
        if (!silent) {
          toast.success("Connected accounts refreshed");
        }
      } catch (error) {
        toast.error(handleApiError(error, "Unable to load connected accounts"));
      } finally {
        setIsRefreshingAccounts(false);
        setAccountsLoading(false);
      }
    },
    []
  );

  const fetchJobs = useCallback(
    async ({ status = jobFilter, silent = false } = {}) => {
      if (!silent) {
        setJobsLoading(true);
      }
      try {
        const params = {
          user_id: DEFAULT_USER_ID,
          job_type: "scheduled_post",
        };
        if (status !== "all") {
          params.status = status;
        }

        const data = await api.get("/jobs/user", { params });
        const list = Array.isArray(data?.jobs) ? data.jobs : [];
        setJobs(list);
        setLastJobsSyncAt(new Date());
      } catch (error) {
        toast.error(handleApiError(error, "Unable to load scheduled jobs"));
      } finally {
        setJobsLoading(false);
      }
    },
    [jobFilter]
  );

  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  useEffect(() => {
    fetchJobs({ status: jobFilter });
  }, [fetchJobs, jobFilter]);

  const toggleAccountSelection = (accountId) => {
    setSelectedAccounts((prev) =>
      prev.includes(accountId)
        ? prev.filter((id) => id !== accountId)
        : [...prev, accountId]
    );
  };

  const togglePlatformSelection = (platformId) => {
    const platformAccountIds = accounts
      .filter((account) => account.platform === platformId)
      .map((account) => account.account_id);

    const hasAllSelected = platformAccountIds.every((id) =>
      selectedAccounts.includes(id)
    );

    setSelectedAccounts((prev) => {
      if (hasAllSelected) {
        return prev.filter((id) => !platformAccountIds.includes(id));
      }
      const merged = new Set([...prev, ...platformAccountIds]);
      return Array.from(merged);
    });
  };

  const toggleAllAccounts = () => {
    if (selectedAccounts.length === accounts.length) {
      setSelectedAccounts([]);
    } else {
      setSelectedAccounts(accounts.map((account) => account.account_id));
    }
  };

  const handleContentChange = (field) => (event) => {
    const value = event.target.value;
    setContent((prev) => ({ ...prev, [field]: value }));
  };

  const ensureAccountsSelected = () => {
    if (!selectedAccounts.length) {
      toast.error("Select at least one account to continue");
      return false;
    }
    return true;
  };

  const ensureContentPresent = (contentPayload) => {
    if (!contentPayload || Object.keys(contentPayload).length === 0) {
      toast.error("Add some copy, media, or a link before posting");
      return false;
    }
    return true;
  };

  const handlePostNow = async () => {
    const contentPayload = buildContentPayload(content);
    if (!ensureAccountsSelected() || !ensureContentPresent(contentPayload)) {
      return;
    }

    setPosting(true);
    setPostResult(null);
    try {
      const response = await api.post("/social/post/multiple", {
        account_ids: selectedAccounts,
        content: contentPayload,
        user_id: DEFAULT_USER_ID,
      });
      setPostResult(response);
      const successful = response?.summary?.successful ?? selectedAccounts.length;
      toast.success(
        `Published to ${successful} account${successful === 1 ? "" : "s"}`
      );
      setContent(INITIAL_CONTENT);
    } catch (error) {
      toast.error(handleApiError(error, "Failed to publish content"));
    } finally {
      setPosting(false);
    }
  };

  const handleSchedulePost = async () => {
    const contentPayload = buildContentPayload(content);
    if (!ensureAccountsSelected() || !ensureContentPresent(contentPayload)) {
      return;
    }

    if (!scheduleDate || !scheduleTime) {
      toast.error("Choose a date and time for the scheduled post");
      return;
    }

    const combined = new Date(`${scheduleDate}T${scheduleTime}`);
    if (Number.isNaN(combined.getTime())) {
      toast.error("Invalid schedule date or time");
      return;
    }

    if (combined.getTime() <= Date.now()) {
      toast.error("Scheduled time must be in the future");
      return;
    }

    setScheduling(true);
    setScheduledResult(null);
    try {
      const response = await api.post("/social/post/schedule", {
        account_ids: selectedAccounts,
        content: contentPayload,
        scheduled_time: combined.toISOString(),
        user_id: DEFAULT_USER_ID,
      });
      setScheduledResult(response);
      toast.success("Post scheduled successfully");
      setScheduleDate("");
      setScheduleTime("");
      fetchJobs({ status: jobFilter, silent: true });
    } catch (error) {
      toast.error(handleApiError(error, "Failed to schedule post"));
    } finally {
      setScheduling(false);
    }
  };

  const handleCancelJob = async (jobId) => {
    try {
      setCancellingJobId(jobId);
      await api.delete(`/jobs/${jobId}`, {
        params: { user_id: DEFAULT_USER_ID },
      });
      toast.success("Scheduled post cancelled");
      fetchJobs({ status: jobFilter, silent: true });
    } catch (error) {
      toast.error(handleApiError(error, "Unable to cancel scheduled post"));
    } finally {
      setCancellingJobId(null);
    }
  };

  const renderComposerActions = () => (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex flex-wrap gap-2">
        <Button onClick={handlePostNow} disabled={posting || !selectedCount}>
          {posting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Posting...
            </>
          ) : (
            <>
              <Send className="mr-2 h-4 w-4" />
              Post Now
            </>
          )}
        </Button>
        <Button
          variant="outline"
          onClick={handleSchedulePost}
          disabled={scheduling || !selectedCount}
        >
          {scheduling ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Scheduling...
            </>
          ) : (
            <>
              <CalendarClock className="mr-2 h-4 w-4" />
              Schedule Post
            </>
          )}
        </Button>
      </div>
      <div className="text-sm text-slate-500">
        {selectedCount
          ? `Ready to deliver to ${selectedCount} account${
              selectedCount === 1 ? "" : "s"
            }`
          : "Select at least one account to enable posting"}
      </div>
    </div>
  );

  const renderAccountsSection = () => (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <CardTitle className="flex items-center gap-2 text-xl">
            <Layers className="h-5 w-5 text-slate-600" />
            Connected Accounts
          </CardTitle>
          <CardDescription>
            Choose the profiles that should receive published content.
          </CardDescription>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchAccounts({ silent: true })}
            disabled={isRefreshingAccounts}
          >
            {isRefreshingAccounts ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Syncing...
              </>
            ) : (
              <>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh
              </>
            )}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate("/social-media-credentials")}
          >
            <Share2 className="mr-2 h-4 w-4" />
            Manage Connections
          </Button>
          {totalConnected > 0 && (
            <Button variant="outline" size="sm" onClick={toggleAllAccounts}>
              <ListChecks className="mr-2 h-4 w-4" />
              {selectedCount === totalConnected ? "Clear All" : "Select All"}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {totalConnected === 0 ? (
          <Alert className="border-dashed border-slate-200 bg-white text-slate-600">
            <AlertDescription className="flex items-center gap-3 text-sm">
              <AlertCircle className="h-5 w-5 text-amber-500" />
              No social accounts connected yet. Connect your profiles to start
              posting.
            </AlertDescription>
          </Alert>
        ) : (
          SOCIAL_PLATFORMS.map((platform) => {
            const platformAccounts = accountsByPlatform[platform.id] || [];
            if (!platformAccounts.length) {
              return null;
            }

            const Icon = platform.icon;
            const platformSelections = platformAccounts.filter((account) =>
              selectedAccounts.includes(account.account_id)
            ).length;

            return (
              <div key={platform.id} className="space-y-3 rounded-lg border border-slate-200 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100">
                      <Icon className="h-4 w-4" />
                    </span>
                    <div>
                      <p className="text-sm font-semibold text-slate-800">
                        {platform.label}
                      </p>
                      <p className="text-xs text-slate-500">
                        {platformSelections}/{platformAccounts.length} selected
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => togglePlatformSelection(platform.id)}
                  >
                    <ListChecks className="mr-2 h-4 w-4" />
                    {platformSelections === platformAccounts.length
                      ? "Clear"
                      : "Select"}{" "}
                    All
                  </Button>
                </div>
                <div className="space-y-2">
                  {platformAccounts.map((account) => {
                    const connectedAt =
                      parseDateValue(account.connected_at) ||
                      parseDateValue(account.connectedAt);

                    return (
                      <label
                        key={account.account_id}
                        className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2"
                      >
                        <div className="flex items-center gap-3">
                          <Checkbox
                            checked={selectedAccounts.includes(
                              account.account_id
                            )}
                            onCheckedChange={() =>
                              toggleAccountSelection(account.account_id)
                            }
                          />
                          <div>
                            <p className="text-sm font-medium text-slate-800">
                              {account.account_name ||
                                account.display_name ||
                                account.account_id}
                            </p>
                            {connectedAt && (
                              <p className="text-xs text-slate-500">
                                Connected{" "}
                                {formatDistanceToNow(connectedAt, {
                                  addSuffix: true,
                                })}
                              </p>
                            )}
                          </div>
                        </div>
                        <Badge
                          variant="outline"
                          className={platform.badgeClass}
                        >
                          {platform.label}
                        </Badge>
                      </label>
                    );
                  })}
                </div>
              </div>
            );
          })
        )}

        {lastAccountsSyncAt && (
          <p className="text-xs text-slate-500">
            Synced {formatDistanceToNow(lastAccountsSyncAt, { addSuffix: true })}
          </p>
        )}
      </CardContent>
    </Card>
  );

  const renderComposer = () => (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-xl">
          <Share2 className="h-5 w-5 text-slate-600" />
          Multi-Platform Composer
        </CardTitle>
        <CardDescription>
          Create once and distribute everywhere. Supports text, media, and link
          rich posts.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-4">
          <div className="space-y-2">
            <Label htmlFor="post-text">Post Caption</Label>
            <Textarea
              id="post-text"
              placeholder="Share your announcement, promotion, or update..."
              rows={5}
              value={content.text}
              onChange={handleContentChange("text")}
            />
          </div>
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="post-image">Image URL</Label>
              <Input
                id="post-image"
                placeholder="https://example.com/image.jpg"
                value={content.imageUrl}
                onChange={handleContentChange("imageUrl")}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="post-video">Video URL</Label>
              <Input
                id="post-video"
                placeholder="https://example.com/video.mp4"
                value={content.videoUrl}
                onChange={handleContentChange("videoUrl")}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="post-link">Link URL</Label>
              <Input
                id="post-link"
                placeholder="https://your-site.com"
                value={content.link}
                onChange={handleContentChange("link")}
              />
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <p className="flex items-center gap-2 text-xs text-slate-500">
            <Sparkles className="h-4 w-4 text-amber-500" />
            Tip: Provide both copy and media links to unlock the richest post
            formats on each network.
          </p>
        </div>

        <div className="rounded-lg border border-slate-200 p-4">
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="schedule-date">Schedule Date</Label>
              <Input
                id="schedule-date"
                type="date"
                value={scheduleDate}
                onChange={(event) => setScheduleDate(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="schedule-time">Schedule Time</Label>
              <Input
                id="schedule-time"
                type="time"
                value={scheduleTime}
                onChange={(event) => setScheduleTime(event.target.value)}
              />
            </div>
          </div>
          <p className="mt-2 text-xs text-slate-500">
            Leave both fields blank to publish immediately. Timezone uses the
            browser&apos;s local setting.
          </p>
        </div>

        {renderComposerActions()}
      </CardContent>
    </Card>
  );

  const renderPostResults = () => (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-xl">
          <CheckCircle2 className="h-5 w-5 text-emerald-600" />
          Latest Actions
        </CardTitle>
        <CardDescription>
          Review the outcomes from the most recent publish or schedule.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {postResult ? (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
            <p className="font-semibold">Publish Summary</p>
            <p className="mt-1">
              {postResult?.summary?.successful ?? 0} successful /{" "}
              {postResult?.summary?.failed ?? 0} failed
            </p>
            {postResult?.results && (
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {Object.entries(postResult.results).map(
                  ([accountId, result]) => (
                    <li key={accountId}>
                      <span className="font-medium">{accountId}</span>:{" "}
                      {result.success ? "Posted successfully" : "Failed"}
                      {result.message ? ` (${result.message})` : ""}
                    </li>
                  )
                )}
              </ul>
            )}
          </div>
        ) : (
          <Alert className="border-slate-200 bg-slate-50 text-slate-600">
            <AlertDescription className="text-sm">
              Publish a post to see success details here.
            </AlertDescription>
          </Alert>
        )}

        {scheduledResult ? (
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800">
            <p className="font-semibold">Schedule Confirmed</p>
            <p className="mt-1">
              Job ID: <code className="rounded bg-blue-100 px-1">{scheduledResult?.job_id}</code>
            </p>
            <p className="mt-1">
              Scheduled for{" "}
              {scheduledResult?.scheduled_time
                ? format(new Date(scheduledResult.scheduled_time), "PPpp")
                : "processing..."}
            </p>
          </div>
        ) : (
          <Alert className="border-slate-200 bg-white text-slate-600">
            <AlertDescription className="text-sm">
              Schedule a future post to capture job details and timing.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );

  const renderJobs = () => (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <CardTitle className="flex items-center gap-2 text-xl">
            <CalendarClock className="h-5 w-5 text-slate-600" />
            Scheduled Posts
          </CardTitle>
          <CardDescription>
            Monitor and manage queued social posts.
          </CardDescription>
        </div>
        <div className="flex flex-wrap gap-2">
          {["pending", "processing", "completed", "failed", "all"].map(
            (status) => (
              <Button
                key={status}
                variant={jobFilter === status ? "default" : "outline"}
                size="sm"
                onClick={() => setJobFilter(status)}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </Button>
            )
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchJobs({ status: jobFilter, silent: true })}
            disabled={jobsLoading}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {jobsLoading ? (
          <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3">
            <Loader2 className="h-4 w-4 animate-spin text-slate-500" />
            <span className="text-sm text-slate-500">
              Loading scheduled posts...
            </span>
          </div>
        ) : jobs.length === 0 ? (
          <Alert className="border-slate-200 bg-white text-slate-600">
            <AlertDescription className="text-sm">
              No scheduled posts found for this filter.
            </AlertDescription>
          </Alert>
        ) : (
          <div className="space-y-3">
            {jobs.map((job) => {
              const scheduledFor = parseDateValue(job.scheduled_time);
              const createdAt = parseDateValue(job.created_at);
              const statusStyle =
                JOB_STATUS_STYLES[job.status] || JOB_STATUS_STYLES.pending;

              return (
                <div
                  key={job.job_id}
                  className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4 md:flex-row md:items-center md:justify-between"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-slate-800">
                        {job.job_id}
                      </span>
                      <Badge variant="outline" className={statusStyle}>
                        {job.status.toUpperCase()}
                      </Badge>
                    </div>
                    {scheduledFor && (
                      <p className="mt-2 flex items-center gap-2 text-xs text-slate-500">
                        <Clock className="h-4 w-4 text-slate-400" />
                        Scheduled for {format(scheduledFor, "PPpp")} (
                        {formatDistanceToNow(scheduledFor, { addSuffix: true })}
                        )
                      </p>
                    )}
                    {createdAt && (
                      <p className="mt-1 text-xs text-slate-500">
                        Created {formatDistanceToNow(createdAt, { addSuffix: true })}
                      </p>
                    )}
                  </div>
                  {["pending", "processing"].includes(job.status) && (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleCancelJob(job.job_id)}
                      disabled={cancellingJobId === job.job_id}
                    >
                      {cancellingJobId === job.job_id ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Cancelling...
                        </>
                      ) : (
                        <>
                          <Trash2 className="mr-2 h-4 w-4" />
                          Cancel
                        </>
                      )}
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {lastJobsSyncAt && (
          <p className="text-xs text-slate-500">
            Last updated{" "}
            {formatDistanceToNow(lastJobsSyncAt, { addSuffix: true })}
          </p>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className="container mx-auto px-4 py-10">
      <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            Unified Social Operations
          </h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-600">
            Connect, publish, and schedule campaigns across Facebook, Instagram,
            Twitter, and LinkedIn. Token refresh, analytics sync, and cleanup
            run automatically in the background.
          </p>
        </div>
        <div className="flex flex-col items-start gap-2 md:items-end">
          <Badge className="w-fit border-emerald-200 bg-emerald-50 text-emerald-700">
            {totalConnected} account{totalConnected === 1 ? "" : "s"} connected
          </Badge>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/analytics")}
            >
              <Target className="mr-2 h-4 w-4" />
              View Analytics
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/dashboard")}
            >
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Dashboard Overview
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1">{renderAccountsSection()}</div>
        <div className="lg:col-span-2">{renderComposer()}</div>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">{renderJobs()}</div>
        <div className="lg:col-span-1">{renderPostResults()}</div>
      </div>
    </div>
  );
};

export default SocialMediaDashboard;
