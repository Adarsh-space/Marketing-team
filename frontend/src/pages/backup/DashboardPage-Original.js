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
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "sonner";
import {
  RefreshCw,
  Clock,
  AlertCircle,
  Loader2,
  CalendarClock,
  Share2,
  BarChart3,
  Activity,
  ShieldCheck,
  Play,
  Pause,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { api, DEFAULT_USER_ID, handleApiError } from "@/lib/api";
import {
  SOCIAL_PLATFORMS,
  getPlatformLabel,
} from "@/constants/socialPlatforms";

const parseDateValue = (value) => {
  if (!value) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const computeExpiryInfo = (token) => {
  const now = Date.now();
  const expiresIso = token.expires_at || token.token_expires_at;
  const ttlSeconds =
    typeof token.time_until_expiry_seconds === "number"
      ? token.time_until_expiry_seconds
      : null;

  let expiresAt = null;
  if (expiresIso) {
    expiresAt = parseDateValue(expiresIso);
  } else if (ttlSeconds !== null) {
    expiresAt = new Date(now + ttlSeconds * 1000);
  }

  if (!expiresAt) {
    return {
      expiresAt: null,
      isExpired: Boolean(token.is_expired),
      isExpiringSoon: Boolean(token.is_expiring_soon),
    };
  }

  const diffMs = expiresAt.getTime() - now;
  const isExpired = token.is_expired ?? diffMs <= 0;
  const isExpiringSoon = token.is_expiring_soon ?? diffMs < 72 * 3600 * 1000;

  return {
    expiresAt,
    isExpired,
    isExpiringSoon,
  };
};

const DashboardPage = () => {
  const navigate = useNavigate();
  const [overview, setOverview] = useState(null);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [scheduler, setScheduler] = useState(null);
  const [schedulerLoading, setSchedulerLoading] = useState(true);
  const [refreshingOverview, setRefreshingOverview] = useState(false);
  const [refreshingTokens, setRefreshingTokens] = useState(false);
  const [schedulerActionLoading, setSchedulerActionLoading] = useState(false);

  const fetchOverview = useCallback(async () => {
    setOverviewLoading(true);
    try {
      const response = await api.get("/dashboard/overview", {
        params: { user_id: DEFAULT_USER_ID },
      });
      setOverview(response);
    } catch (error) {
      toast.error(handleApiError(error, "Failed to load dashboard overview"));
      setOverview(null);
    } finally {
      setOverviewLoading(false);
    }
  }, []);

  const fetchScheduler = useCallback(async () => {
    setSchedulerLoading(true);
    try {
      const response = await api.get("/jobs/scheduler/status");
      setScheduler(response);
    } catch (error) {
      toast.error(handleApiError(error, "Failed to load scheduler status"));
      setScheduler(null);
    } finally {
      setSchedulerLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOverview();
    fetchScheduler();
  }, [fetchOverview, fetchScheduler]);

  const handleRefreshOverview = async () => {
    try {
      setRefreshingOverview(true);
      await Promise.all([fetchOverview(), fetchScheduler()]);
      toast.success("Dashboard data refreshed");
    } finally {
      setRefreshingOverview(false);
    }
  };

  const handleRefreshTokens = async (platform) => {
    try {
      setRefreshingTokens(true);
      const params = { user_id: DEFAULT_USER_ID };
      if (platform && platform !== "all") {
        params.platform = platform;
      }

      await api.post("/tokens/refresh", {}, { params });

      toast.success(
        platform && platform !== "all"
          ? `${getPlatformLabel(platform)} tokens refreshed`
          : "Token refresh triggered"
      );
      fetchOverview();
    } catch (error) {
      toast.error(handleApiError(error, "Failed to refresh tokens"));
    } finally {
      setRefreshingTokens(false);
    }
  };

  const handleSchedulerAction = async (action) => {
    try {
      setSchedulerActionLoading(true);
      if (action === "start") {
        await api.post("/jobs/scheduler/start");
        toast.success("Job scheduler started");
      } else {
        await api.post("/jobs/scheduler/stop");
        toast.success("Job scheduler stopped");
      }
      fetchScheduler();
    } catch (error) {
      toast.error(handleApiError(error, "Scheduler action failed"));
    } finally {
      setSchedulerActionLoading(false);
    }
  };

  const tokenStatus = overview?.token_status || {};
  const socialTokens = tokenStatus.social_accounts || [];
  const zohoToken = tokenStatus.zoho || null;
  const connectedAccounts = overview?.connected_accounts || [];
  const pendingJobs = overview?.pending_jobs || [];
  const summary = overview?.analytics?.summary || {};

  const tokensByPlatform = useMemo(() => {
    return socialTokens.reduce((acc, token) => {
      const key = token.platform || "unknown";
      if (!acc[key]) {
        acc[key] = [];
      }
      acc[key].push(token);
      return acc;
    }, {});
  }, [socialTokens]);

  const expiringCount = socialTokens.filter((token) => {
    const info = computeExpiryInfo(token);
    return info.isExpiringSoon && !info.isExpired;
  }).length;

  const expiredCount = socialTokens.filter(
    (token) => computeExpiryInfo(token).isExpired
  ).length;

  const renderTokenRow = (token) => {
    const expiryInfo = computeExpiryInfo(token);
    const expiresAt = expiryInfo.expiresAt;

    return (
      <div
        key={`${token.platform}-${token.account_id}`}
        className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4 md:flex-row md:items-center md:justify-between"
      >
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-slate-900">
              {token.account_name || token.account_id}
            </span>
            <Badge variant="outline" className="bg-white text-xs">
              {getPlatformLabel(token.platform)}
            </Badge>
            {expiryInfo.isExpired ? (
              <Badge variant="destructive">Expired</Badge>
            ) : expiryInfo.isExpiringSoon ? (
              <Badge className="border-amber-200 bg-amber-50 text-amber-700">
                Expiring soon
              </Badge>
            ) : (
              <Badge className="border-emerald-200 bg-emerald-50 text-emerald-700">
                Active
              </Badge>
            )}
          </div>
          {expiresAt ? (
            <p className="mt-1 flex items-center gap-2 text-xs text-slate-500">
              <Clock className="h-4 w-4 text-slate-400" />
              {expiryInfo.isExpired
                ? `Expired ${formatDistanceToNow(expiresAt, {
                    addSuffix: true,
                  })}`
                : `Expires ${formatDistanceToNow(expiresAt, {
                    addSuffix: true,
                  })} (${format(expiresAt, "PPpp")})`}
            </p>
          ) : (
            <p className="mt-1 flex items-center gap-2 text-xs text-slate-500">
              <AlertCircle className="h-4 w-4 text-amber-500" />
              Expiry data unavailable
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleRefreshTokens(token.platform)}
            disabled={refreshingTokens}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh Token
          </Button>
        </div>
      </div>
    );
  };

  const renderZohoToken = () => {
    if (!zohoToken) {
      return (
        <Alert className="border-slate-200 bg-white text-slate-600">
          <AlertDescription className="text-sm">
            Zoho account not connected. Connect from the Zoho page to enable CRM
            and campaigns.
          </AlertDescription>
        </Alert>
      );
    }

    const expiryInfo = computeExpiryInfo(zohoToken);
    const expiresAt = expiryInfo.expiresAt;

    return (
      <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-slate-900">
              Zoho Integration
            </span>
            {expiryInfo.isExpired ? (
              <Badge variant="destructive">Expired</Badge>
            ) : expiryInfo.isExpiringSoon ? (
              <Badge className="border-amber-200 bg-amber-50 text-amber-700">
                Expiring soon
              </Badge>
            ) : (
              <Badge className="border-emerald-200 bg-emerald-50 text-emerald-700">
                Active
              </Badge>
            )}
          </div>
          {expiresAt ? (
            <p className="mt-1 flex items-center gap-2 text-xs text-slate-500">
              <Clock className="h-4 w-4 text-slate-400" />
              {expiryInfo.isExpired
                ? `Expired ${formatDistanceToNow(expiresAt, {
                    addSuffix: true,
                  })}`
                : `Expires ${formatDistanceToNow(expiresAt, {
                    addSuffix: true,
                  })} (${format(expiresAt, "PPpp")})`}
            </p>
          ) : (
            <p className="mt-1 flex items-center gap-2 text-xs text-slate-500">
              <AlertCircle className="h-4 w-4 text-amber-500" />
              Expiry data unavailable
            </p>
          )}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate("/zoho-connections")}
        >
          Manage Zoho
        </Button>
      </div>
    );
  };

  const renderSummaryCards = () => (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="flex items-center justify-between px-6 py-5">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">
              Connected Accounts
            </p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">
              {connectedAccounts.length}
            </p>
            <p className="text-xs text-slate-500">
              Across {Object.keys(tokensByPlatform).length} platforms
            </p>
          </div>
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 text-blue-600">
            <Share2 className="h-6 w-6" />
          </span>
        </CardContent>
      </Card>

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="flex items-center justify-between px-6 py-5">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">
              Pending Jobs
            </p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">
              {pendingJobs.length}
            </p>
            <p className="text-xs text-slate-500">
              Scheduled social posts awaiting execution
            </p>
          </div>
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-purple-100 text-purple-600">
            <CalendarClock className="h-6 w-6" />
          </span>
        </CardContent>
      </Card>

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="flex items-center justify-between px-6 py-5">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">
              Tokens Expiring Soon
            </p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">
              {expiringCount}
            </p>
            <p className="text-xs text-slate-500">
              {expiredCount} already expired
            </p>
          </div>
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 text-amber-600">
            <ShieldCheck className="h-6 w-6" />
          </span>
        </CardContent>
      </Card>

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="flex items-center justify-between px-6 py-5">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">
              Engagement Rate
            </p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">
              {summary.social_engagement_rate
                ? `${Number(summary.social_engagement_rate).toFixed(1)}%`
                : "—"}
            </p>
            <p className="text-xs text-slate-500">
              Total impressions {summary.total_social_impressions ?? "—"}
            </p>
          </div>
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
            <Activity className="h-6 w-6" />
          </span>
        </CardContent>
      </Card>
    </div>
  );

  const renderConnectedAccounts = () => (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <CardTitle>Connected Accounts</CardTitle>
          <CardDescription>
            Active social profiles available for publishing
          </CardDescription>
        </div>
        <Button variant="outline" size="sm" onClick={() => navigate("/social-media-credentials")}>
          Manage Connections
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {connectedAccounts.length === 0 ? (
          <Alert className="border-slate-200 bg-white text-slate-600">
            <AlertDescription className="text-sm">
              Connect your social accounts to enable posting and analytics.
            </AlertDescription>
          </Alert>
        ) : (
          connectedAccounts.map((account, index) => {
            const platform = SOCIAL_PLATFORMS.find(
              (item) => item.id === account.platform
            );
            const Icon = platform?.icon;

            return (
              <div
                key={`${account.platform}-${account.account_name}-${index}`}
                className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white">
                    {Icon ? <Icon className="h-4 w-4" /> : <Share2 className="h-4 w-4" />}
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">
                      {account.account_name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {getPlatformLabel(account.platform)}
                    </p>
                  </div>
                </div>
                {account.connected_at && (
                  <p className="text-xs text-slate-500">
                    Linked{" "}
                    {formatDistanceToNow(new Date(account.connected_at), {
                      addSuffix: true,
                    })}
                  </p>
                )}
              </div>
            );
          })
        )}
      </CardContent>
    </Card>
  );

  const renderPendingJobs = () => (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <CardTitle>Upcoming Scheduled Posts</CardTitle>
          <CardDescription>
            Pending jobs queued in the background scheduler
          </CardDescription>
        </div>
        <Button variant="outline" size="sm" onClick={() => navigate("/social-media")}>
          View Scheduler
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {pendingJobs.length === 0 ? (
          <Alert className="border-slate-200 bg-white text-slate-600">
            <AlertDescription className="text-sm">
              No scheduled posts pending execution.
            </AlertDescription>
          </Alert>
        ) : (
          pendingJobs.map((job) => {
            const scheduledFor = parseDateValue(job.scheduled_time);
            return (
              <div
                key={job.job_id}
                className="flex flex-col gap-2 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 md:flex-row md:items-center md:justify-between"
              >
                <div>
                  <p className="text-sm font-semibold text-slate-900">
                    {job.job_id}
                  </p>
                  <p className="text-xs text-slate-500">
                    {job.job_type?.replace("_", " ") || "scheduled_post"}
                  </p>
                </div>
                {scheduledFor && (
                  <div className="text-xs text-slate-500">
                    <p>Runs {format(scheduledFor, "PPpp")}</p>
                    <p>
                      {formatDistanceToNow(scheduledFor, {
                        addSuffix: true,
                      })}
                    </p>
                  </div>
                )}
              </div>
            );
          })
        )}
      </CardContent>
    </Card>
  );

  const renderSchedulerStatus = () => (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <CardTitle>Job Scheduler</CardTitle>
          <CardDescription>
            Background automation for tokens, analytics, and cleanup
          </CardDescription>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleSchedulerAction("start")}
            disabled={schedulerActionLoading}
          >
            {schedulerActionLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Play className="mr-2 h-4 w-4" />
            )}
            Start
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleSchedulerAction("stop")}
            disabled={schedulerActionLoading}
          >
            {schedulerActionLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Pause className="mr-2 h-4 w-4" />
            )}
            Stop
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {schedulerLoading ? (
          <div className="flex items-center justify-center py-6">
            <Loader2 className="h-6 w-6 animate-spin text-slate-500" />
          </div>
        ) : !scheduler ? (
          <Alert className="border-slate-200 bg-white text-slate-600">
            <AlertDescription className="text-sm">
              Scheduler status unavailable. Refresh to try again.
            </AlertDescription>
          </Alert>
        ) : (
          <>
            <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 md:flex-row md:items-center md:justify-between">
              <div className="flex items-center gap-2 text-sm text-slate-700">
                <ShieldCheck className="h-4 w-4 text-emerald-500" />
                Scheduler is{" "}
                <span className="font-semibold text-slate-900">
                  {scheduler.is_running ? "running" : "stopped"}
                </span>
              </div>
              <div className="text-xs text-slate-500">
                Active jobs: {scheduler.active_jobs ?? 0}
              </div>
            </div>
            <div className="space-y-2">
              {(scheduler.jobs || []).map((job) => (
                <div
                  key={job.id}
                  className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm"
                >
                  <div>
                    <p className="font-semibold text-slate-900">{job.name}</p>
                    <p className="text-xs text-slate-500">{job.id}</p>
                  </div>
                  {job.next_run_time && (
                    <p className="text-xs text-slate-500">
                      Next run {formatDistanceToNow(new Date(job.next_run_time), {
                        addSuffix: true,
                      })}
                    </p>
                  )}
                </div>
              ))}
            </div>
            {scheduler.statistics && (
              <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-500">
                <p>
                  Completed: <strong>{scheduler.statistics.completed ?? 0}</strong> • Failed:{" "}
                  <strong>{scheduler.statistics.failed ?? 0}</strong> • Pending:{" "}
                  <strong>{scheduler.statistics.pending ?? 0}</strong>
                </p>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className="container mx-auto px-4 py-10">
      <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Operations Hub</h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-600">
            Monitor connections, token health, scheduled jobs, and automation
            status across the unified marketing stack.
          </p>
        </div>
        <div className="flex flex-col items-start gap-2 lg:items-end">
          <Button
            variant="outline"
            onClick={handleRefreshOverview}
            disabled={refreshingOverview}
          >
            {refreshingOverview ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Refreshing...
              </>
            ) : (
              <>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh Overview
              </>
            )}
          </Button>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/social-media")}
            >
              <Share2 className="mr-2 h-4 w-4" />
              Social Dashboard
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/analytics")}
            >
              <BarChart3 className="mr-2 h-4 w-4" />
              View Analytics
            </Button>
          </div>
        </div>
      </div>

      {overviewLoading ? (
        <div className="flex min-h-[200px] items-center justify-center rounded-lg border border-slate-200 bg-white">
          <Loader2 className="h-6 w-6 animate-spin text-slate-500" />
        </div>
      ) : (
        <div className="space-y-6">
          {renderSummaryCards()}

          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle>Token Health</CardTitle>
                <CardDescription>
                  Automatic refresh runs every 6 hours; trigger manually if
                  needed.
                </CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleRefreshTokens("all")}
                disabled={refreshingTokens}
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh All Tokens
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              {socialTokens.length === 0 ? (
                <Alert className="border-slate-200 bg-white text-slate-600">
                  <AlertDescription className="text-sm">
                    No social tokens found. Connect platforms to enable posting.
                  </AlertDescription>
                </Alert>
              ) : (
                Object.values(tokensByPlatform).map((tokens, index) => (
                  <div key={index} className="space-y-3">
                    {tokens.map((token) => renderTokenRow(token))}
                  </div>
                ))
              )}

              {renderZohoToken()}
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {renderConnectedAccounts()}
            {renderPendingJobs()}
          </div>

          {renderSchedulerStatus()}
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
