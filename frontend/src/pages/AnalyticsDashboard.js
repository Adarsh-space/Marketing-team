import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "sonner";
import {
  BarChart3,
  Activity,
  Users,
  Mail,
  RefreshCw,
  LineChart,
  TrendingUp,
  Building2,
  Loader2,
  CalendarRange,
} from "lucide-react";
import { format } from "date-fns";
import { api, DEFAULT_USER_ID, handleApiError } from "@/lib/api";
import {
  SOCIAL_PLATFORMS,
  getPlatformLabel,
} from "@/constants/socialPlatforms";

const PLATFORM_FIELDS = {
  facebook: [
    { key: "page_impressions", label: "Impressions" },
    { key: "page_engaged_users", label: "Engaged Users" },
    { key: "page_post_engagements", label: "Post Engagements" },
    { key: "page_fans", label: "Followers" },
  ],
  instagram: [
    { key: "impressions", label: "Impressions" },
    { key: "engagement", label: "Engagements" },
    { key: "follower_count", label: "Followers" },
  ],
  twitter: [
    { key: "total_tweets", label: "Tweets" },
    { key: "total_likes", label: "Likes" },
    { key: "total_retweets", label: "Retweets" },
  ],
  linkedin: [
    { key: "impressions", label: "Impressions" },
    { key: "clicks", label: "Clicks" },
    { key: "followers", label: "Followers" },
  ],
};

const formatNumber = (value) => {
  if (value === null || value === undefined) {
    return "--";
  }
  if (typeof value !== "number") {
    const parsed = Number(value);
    if (Number.isNaN(parsed)) {
      return String(value);
    }
    value = parsed;
  }
  if (Math.abs(value) >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `${(value / 1_000).toFixed(1)}k`;
  }
  return value.toLocaleString();
};

const formatPercent = (value) => {
  if (value === null || value === undefined) {
    return "--";
  }
  const numeric = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(numeric)) {
    return "--";
  }
  return `${numeric.toFixed(1)}%`;
};

const getMetricValue = (metrics, keys) => {
  if (!metrics) return null;
  for (const key of keys) {
    if (metrics[key] !== undefined && metrics[key] !== null) {
      return metrics[key];
    }
  }
  return null;
};

const AnalyticsDashboard = () => {
  const [aggregateData, setAggregateData] = useState(null);
  const [aggregateLoading, setAggregateLoading] = useState(true);
  const [aggregateRange, setAggregateRange] = useState(null);
  const [rangeDays, setRangeDays] = useState("30");
  const [historyData, setHistoryData] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyPlatform, setHistoryPlatform] = useState("all");
  const [historyDays, setHistoryDays] = useState("14");
  const [refreshing, setRefreshing] = useState(false);

  const fetchAggregate = useCallback(async (days = rangeDays) => {
    setAggregateLoading(true);
    try {
      const now = new Date();
      const params = { user_id: DEFAULT_USER_ID };
      if (days) {
        const duration = Number(days);
        if (!Number.isNaN(duration) && duration > 0) {
          const from = new Date(now.getTime() - (duration - 1) * 86400000);
          params.date_from = from.toISOString();
          params.date_to = now.toISOString();
        }
      }

      const response = await api.get("/social/analytics/aggregate", { params });
      setAggregateData(response?.data || null);
      if (params.date_from && params.date_to) {
        setAggregateRange({
          from: params.date_from,
          to: params.date_to,
        });
      } else {
        setAggregateRange(null);
      }
    } catch (error) {
      toast.error(handleApiError(error, "Failed to load analytics summary"));
      setAggregateData(null);
    } finally {
      setAggregateLoading(false);
    }
  }, [rangeDays]);

  const fetchHistory = useCallback(
    async (platform = historyPlatform, days = historyDays) => {
      setHistoryLoading(true);
      try {
        const params = {
          user_id: DEFAULT_USER_ID,
          days: Number(days),
        };
        if (platform && platform !== "all") {
          params.platform = platform;
        }

        const response = await api.get("/social/analytics/history", {
          params,
        });
        setHistoryData(response);
      } catch (error) {
        toast.error(handleApiError(error, "Failed to load analytics history"));
        setHistoryData(null);
      } finally {
        setHistoryLoading(false);
      }
    },
    [historyPlatform, historyDays]
  );

  useEffect(() => {
    fetchAggregate(rangeDays);
  }, [fetchAggregate, rangeDays]);

  useEffect(() => {
    fetchHistory(historyPlatform, historyDays);
  }, [fetchHistory, historyPlatform, historyDays]);

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      await Promise.all([
        fetchAggregate(rangeDays),
        fetchHistory(historyPlatform, historyDays),
      ]);
      toast.success("Analytics refreshed");
    } finally {
      setRefreshing(false);
    }
  };

  const summary = aggregateData?.summary || {};
  const socialMedia = aggregateData?.social_media || {};
  const zoho = aggregateData?.zoho || {};

  const flattenedHistory = useMemo(() => {
    if (!historyData?.by_date) {
      return [];
    }

    return Object.entries(historyData.by_date)
      .flatMap(([date, entries]) =>
        entries.map((entry) => ({
          date,
          platform: entry.platform || historyData.platform || "all",
          metrics:
            entry.insights || entry.metrics || entry.analytics || entry.data || {},
        }))
      )
      .sort((a, b) => new Date(b.date) - new Date(a.date));
  }, [historyData]);

  const renderPlatformCard = (platformId) => {
    const platformMetrics = socialMedia[platformId];
    const platformConfig = SOCIAL_PLATFORMS.find(
      (item) => item.id === platformId
    );
    if (!platformConfig) {
      return null;
    }

    const Icon = platformConfig.icon;
    const fields = PLATFORM_FIELDS[platformId] || [];
    const hasData =
      platformMetrics && Object.keys(platformMetrics).length > 0;

    return (
      <Card key={platformId} className="border-slate-200 shadow-sm">
        <CardHeader className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100">
            <Icon className="h-5 w-5" />
          </span>
          <div>
            <CardTitle>{platformConfig.label}</CardTitle>
            <CardDescription>
              {hasData
                ? "Performance metrics for the selected range"
                : "No analytics available yet"}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          {hasData ? (
            <div className="space-y-3">
              {fields.map((field) => (
                <div
                  key={field.key}
                  className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm"
                >
                  <span className="text-slate-600">{field.label}</span>
                  <span className="font-semibold text-slate-900">
                    {formatNumber(platformMetrics[field.key])}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <Alert className="border-slate-200 bg-white text-slate-600">
              <AlertDescription className="text-sm">
                Connect a {platformConfig.label} account to start collecting
                analytics.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="container mx-auto px-4 py-10">
      <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            Unified Analytics
          </h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-600">
            Aggregate performance across social platforms, Zoho CRM, and email
            campaigns. Data auto-syncs nightly and can be refreshed on demand.
          </p>
        </div>
        <div className="flex flex-col items-start gap-2 lg:items-end">
          <div className="flex flex-wrap items-center gap-2">
            <Select value={rangeDays} onValueChange={setRangeDays}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7">Last 7 days</SelectItem>
                <SelectItem value="14">Last 14 days</SelectItem>
                <SelectItem value="30">Last 30 days</SelectItem>
                <SelectItem value="60">Last 60 days</SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              {refreshing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Refreshing...
                </>
              ) : (
                <>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Refresh
                </>
              )}
            </Button>
          </div>
          {aggregateRange && (
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <CalendarRange className="h-4 w-4 text-slate-400" />
              <span>
                Showing {rangeDays}-day window (
                {format(new Date(aggregateRange.from), "PP")} →{" "}
                {format(new Date(aggregateRange.to), "PP")})
              </span>
            </div>
          )}
        </div>
      </div>

      {aggregateLoading ? (
        <div className="flex min-h-[200px] items-center justify-center rounded-lg border border-slate-200 bg-white">
          <Loader2 className="h-6 w-6 animate-spin text-slate-500" />
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Card className="border-slate-200 shadow-sm">
              <CardContent className="flex items-center justify-between px-6 py-5">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">
                    Total Impressions
                  </p>
                  <p className="mt-2 text-3xl font-semibold text-slate-900">
                    {formatNumber(summary.total_social_impressions)}
                  </p>
                </div>
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 text-blue-600">
                  <BarChart3 className="h-6 w-6" />
                </span>
              </CardContent>
            </Card>
            <Card className="border-slate-200 shadow-sm">
              <CardContent className="flex items-center justify-between px-6 py-5">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">
                    Total Engagement
                  </p>
                  <p className="mt-2 text-3xl font-semibold text-slate-900">
                    {formatNumber(summary.total_social_engagement)}
                  </p>
                </div>
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                  <Activity className="h-6 w-6" />
                </span>
              </CardContent>
            </Card>
            <Card className="border-slate-200 shadow-sm">
              <CardContent className="flex items-center justify-between px-6 py-5">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">
                    Total Followers
                  </p>
                  <p className="mt-2 text-3xl font-semibold text-slate-900">
                    {formatNumber(summary.total_social_followers)}
                  </p>
                </div>
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-purple-100 text-purple-600">
                  <Users className="h-6 w-6" />
                </span>
              </CardContent>
            </Card>
            <Card className="border-slate-200 shadow-sm">
              <CardContent className="flex items-center justify-between px-6 py-5">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">
                    Email Open Rate
                  </p>
                  <p className="mt-2 text-3xl font-semibold text-slate-900">
                    {formatPercent(summary.email_open_rate)}
                  </p>
                </div>
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-orange-100 text-orange-600">
                  <Mail className="h-6 w-6" />
                </span>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card className="border-slate-200 shadow-sm">
              <CardHeader>
                <CardTitle>Zoho CRM Snapshot</CardTitle>
                <CardDescription>
                  Lead distribution and pipeline health
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-500">
                      Total Leads
                    </p>
                    <p className="mt-1 text-xl font-semibold text-slate-900">
                      {formatNumber(zoho?.crm_leads?.total_records)}
                    </p>
                  </div>
                  <span className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-200 text-slate-700">
                    <Building2 className="h-5 w-5" />
                  </span>
                </div>
                <div className="space-y-2">
                  {zoho?.crm_leads?.by_status ? (
                    Object.entries(zoho.crm_leads.by_status).map(
                      ([status, value]) => (
                        <div
                          key={status}
                          className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
                        >
                          <span className="text-slate-600">{status}</span>
                          <span className="font-semibold text-slate-900">
                            {formatNumber(value)}
                          </span>
                        </div>
                      )
                    )
                  ) : (
                    <Alert className="border-slate-200 bg-white text-slate-600">
                      <AlertDescription className="text-sm">
                        No Zoho CRM data available for this range.
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200 shadow-sm">
              <CardHeader>
                <CardTitle>Email Campaigns</CardTitle>
                <CardDescription>
                  Key metrics from Zoho Campaigns
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                    <p className="text-xs uppercase tracking-wide text-slate-500">
                      Campaigns
                    </p>
                    <p className="mt-1 text-xl font-semibold text-slate-900">
                      {formatNumber(zoho?.email_campaigns?.total_campaigns)}
                    </p>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                    <p className="text-xs uppercase tracking-wide text-slate-500">
                      Emails Sent
                    </p>
                    <p className="mt-1 text-xl font-semibold text-slate-900">
                      {formatNumber(zoho?.email_campaigns?.total_sent)}
                    </p>
                  </div>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                  <p className="text-xs uppercase tracking-wide text-slate-500">
                    Total Opens
                  </p>
                  <p className="mt-1 text-xl font-semibold text-slate-900">
                    {formatNumber(zoho?.email_campaigns?.total_opens)}
                  </p>
                  <p className="text-xs text-slate-500">
                    Open Rate:{" "}
                    <span className="font-semibold">
                      {formatPercent(zoho?.email_campaigns?.avg_open_rate)}
                    </span>
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {SOCIAL_PLATFORMS.map((platform) => renderPlatformCard(platform.id))}
          </div>

          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <LineChart className="h-5 w-5 text-slate-600" />
                  Engagement History
                </CardTitle>
                <CardDescription>
                  Rolling metrics for the selected platform and range
                </CardDescription>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Select
                  value={historyPlatform}
                  onValueChange={setHistoryPlatform}
                >
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="Platform" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Platforms</SelectItem>
                    {SOCIAL_PLATFORMS.map((platform) => (
                      <SelectItem key={platform.id} value={platform.id}>
                        {platform.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={historyDays} onValueChange={setHistoryDays}>
                  <SelectTrigger className="w-[120px]">
                    <SelectValue placeholder="Days" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="7">7 days</SelectItem>
                    <SelectItem value="14">14 days</SelectItem>
                    <SelectItem value="30">30 days</SelectItem>
                    <SelectItem value="60">60 days</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              {historyLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-slate-500" />
                </div>
              ) : flattenedHistory.length === 0 ? (
                <Alert className="border-slate-200 bg-white text-slate-600">
                  <AlertDescription className="text-sm">
                    No history data available for the selected filters.
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="border-b bg-slate-50 text-left font-medium text-slate-600">
                        <th className="px-3 py-2">Date</th>
                        <th className="px-3 py-2">Platform</th>
                        <th className="px-3 py-2 text-right">Impressions</th>
                        <th className="px-3 py-2 text-right">Engagement</th>
                        <th className="px-3 py-2 text-right">Followers</th>
                        <th className="px-3 py-2 text-right">Clicks</th>
                      </tr>
                    </thead>
                    <tbody>
                      {flattenedHistory.map((row, index) => {
                        const impressions = getMetricValue(row.metrics, [
                          "page_impressions",
                          "impressions",
                          "total_impressions",
                          "tweet_impressions",
                        ]);
                        const engagement = getMetricValue(row.metrics, [
                          "page_engaged_users",
                          "page_post_engagements",
                          "engagement",
                          "total_engagement",
                          "total_likes",
                          "likes",
                        ]);
                        const followers = getMetricValue(row.metrics, [
                          "page_fans",
                          "follower_count",
                          "followers",
                        ]);
                        const clicks = getMetricValue(row.metrics, [
                          "page_views_total",
                          "clicks",
                          "total_clicks",
                        ]);

                        return (
                          <tr
                            key={`${row.date}-${row.platform}-${index}`}
                            className="border-b last:border-none"
                          >
                            <td className="px-3 py-2 text-slate-700">
                              {format(new Date(row.date), "PP")}
                            </td>
                            <td className="px-3 py-2 text-slate-700">
                              <Badge variant="outline" className="bg-slate-50">
                                {getPlatformLabel(row.platform)}
                              </Badge>
                            </td>
                            <td className="px-3 py-2 text-right font-medium text-slate-900">
                              {formatNumber(impressions)}
                            </td>
                            <td className="px-3 py-2 text-right text-slate-900">
                              {formatNumber(engagement)}
                            </td>
                            <td className="px-3 py-2 text-right text-slate-900">
                              {formatNumber(followers)}
                            </td>
                            <td className="px-3 py-2 text-right text-slate-900">
                              {formatNumber(clicks)}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle>Automation Status</CardTitle>
              <CardDescription>
                Token refresh, analytics sync, and cleanup routines
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">
                    Platforms Connected
                  </p>
                  <p className="mt-1 text-xl font-semibold text-slate-900">
                    {formatNumber(summary.platforms_connected)}
                  </p>
                </div>
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                  <TrendingUp className="h-5 w-5" />
                </span>
              </div>
              <Alert className="border-slate-200 bg-white text-slate-600">
                <AlertDescription className="text-sm leading-6">
                  <ul className="list-disc space-y-1 pl-5">
                    <li>Tokens refresh automatically every 6 hours</li>
                    <li>Social & Zoho analytics sync nightly at 2 AM</li>
                    <li>Old data cleanup runs weekly on Sunday at 3 AM</li>
                  </ul>
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;
