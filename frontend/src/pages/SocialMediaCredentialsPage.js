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
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "sonner";
import {
  Link2,
  Unlink,
  RefreshCw,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { api, DEFAULT_USER_ID, handleApiError } from "@/lib/api";
import { SOCIAL_PLATFORMS, getPlatformLabel } from "@/constants/socialPlatforms";

const parseDateValue = (value) => {
  if (!value) {
    return null;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const computeExpiryInfo = (account) => {
  const now = Date.now();
  const expiryIso = account.token_expires_at || account.expires_at;
  const ttlSeconds =
    typeof account.time_until_expiry_seconds === "number"
      ? account.time_until_expiry_seconds
      : null;

  let expiresAt = null;
  if (expiryIso) {
    expiresAt = parseDateValue(expiryIso);
  } else if (ttlSeconds !== null) {
    expiresAt = new Date(now + ttlSeconds * 1000);
  }

  if (!expiresAt) {
    return {
      expiresAt: null,
      isExpired: Boolean(account.is_expired),
      isExpiringSoon: Boolean(account.is_expiring_soon),
    };
  }

  const diffMs = expiresAt.getTime() - now;
  const isExpired = account.is_expired ?? diffMs <= 0;
  const isExpiringSoon = account.is_expiring_soon ?? diffMs < 72 * 3600 * 1000;

  return {
    expiresAt,
    isExpired,
    isExpiringSoon,
  };
};

const groupAccountsByPlatform = (accounts) => {
  return SOCIAL_PLATFORMS.reduce(
    (acc, platform) => ({
      ...acc,
      [platform.id]: accounts.filter((account) => account.platform === platform.id),
    }),
    {}
  );
};

const SocialMediaCredentialsPage = () => {
  const [accounts, setAccounts] = useState([]);
  const [pageLoading, setPageLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [connectingPlatform, setConnectingPlatform] = useState(null);
  const [disconnectingAccount, setDisconnectingAccount] = useState(null);
  const [lastRefreshedAt, setLastRefreshedAt] = useState(null);

  const accountsByPlatform = useMemo(
    () => groupAccountsByPlatform(accounts),
    [accounts]
  );

  const refreshAccounts = useCallback(
    async ({ silent = false } = {}) => {
      setIsRefreshing(true);
      try {
        const data = await api.get("/social/accounts", {
          params: { user_id: DEFAULT_USER_ID },
        });

        setAccounts(Array.isArray(data?.accounts) ? data.accounts : []);
        setLastRefreshedAt(new Date());
        if (!silent) {
          toast.success("Connection status refreshed");
        }
      } catch (error) {
        toast.error(handleApiError(error, "Failed to load connected accounts"));
      } finally {
        setIsRefreshing(false);
        setPageLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const status = params.get("status");
    const platform = params.get("platform");
    const message = params.get("message");
    const state = params.get("state");

    if (platform) {
      const stateKey = `social_oauth_state_${platform}`;
      const cachedState = localStorage.getItem(stateKey);
      if (cachedState) {
        if (state && cachedState !== state) {
          toast.warning(
            "State mismatch detected. If this was unexpected, try reconnecting the account."
          );
        }
        localStorage.removeItem(stateKey);
      }
    }

    if (status === "success") {
      toast.success(`${getPlatformLabel(platform)} connected successfully`);
    } else if (status === "error") {
      toast.error(
        message || `Failed to connect ${getPlatformLabel(platform)} account`
      );
    } else if (status === "cancelled") {
      toast(message || "Connection was cancelled");
    }

    if (status || platform || message) {
      window.history.replaceState({}, document.title, window.location.pathname);
    }

    refreshAccounts({ silent: true });
  }, [refreshAccounts]);

  const handleConnect = async (platformId) => {
    try {
      setConnectingPlatform(platformId);
      const redirectUri = `${window.location.origin}/social-media-credentials`;
      const data = await api.get(`/social/connect/${platformId}`, {
        params: {
          user_id: DEFAULT_USER_ID,
          redirect_uri: redirectUri,
        },
      });

      if (!data?.auth_url) {
        throw new Error("Authorization URL not provided by the server");
      }

      if (data.state) {
        localStorage.setItem(`social_oauth_state_${platformId}`, data.state);
      }

      window.location.href = data.auth_url;
    } catch (error) {
      toast.error(
        handleApiError(
          error,
          `Unable to start ${getPlatformLabel(platformId)} connection`
        )
      );
    } finally {
      setConnectingPlatform(null);
    }
  };

  const handleDisconnect = async (accountId, platformId) => {
    try {
      setDisconnectingAccount(accountId);
      await api.delete(`/social/accounts/${accountId}`, {
        params: { user_id: DEFAULT_USER_ID },
      });
      toast.success(`${getPlatformLabel(platformId)} account disconnected`);
      refreshAccounts({ silent: true });
    } catch (error) {
      toast.error(
        handleApiError(
          error,
          `Failed to disconnect ${getPlatformLabel(platformId)} account`
        )
      );
    } finally {
      setDisconnectingAccount(null);
    }
  };

  if (pageLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex items-center gap-3 rounded-lg border border-slate-100 bg-white px-6 py-4 shadow-sm">
          <Loader2 className="h-5 w-5 animate-spin text-slate-500" />
          <span className="text-sm font-medium text-slate-600">
            Loading social connections...
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-10">
      <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            Social Account Connections
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-600">
            Connect Facebook, Instagram, Twitter, and LinkedIn to unlock unified
            posting, scheduling, analytics, and automated token refresh.
          </p>
        </div>
        <div className="flex flex-col items-start gap-2 md:items-end">
          {lastRefreshedAt && (
            <span className="text-xs uppercase tracking-wide text-slate-500">
              Last synced{" "}
              {formatDistanceToNow(lastRefreshedAt, { addSuffix: true })}
            </span>
          )}
          <Button
            variant="outline"
            onClick={() => refreshAccounts()}
            disabled={isRefreshing}
          >
            {isRefreshing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Syncing...
              </>
            ) : (
              <>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh Status
              </>
            )}
          </Button>
        </div>
      </div>

      <Alert className="mb-8 border-slate-200 bg-slate-50 text-slate-700">
        <AlertDescription className="flex items-start gap-3">
          <CheckCircle2 className="mt-0.5 h-5 w-5 text-emerald-500" />
          <span className="text-sm leading-6">
            Tokens refresh automatically every six hours. Daily analytics sync
            runs at 2 AM and weekly cleanup executes on Sundays at 3 AM.
          </span>
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {SOCIAL_PLATFORMS.map((platform) => {
          const Icon = platform.icon;
          const platformAccounts = accountsByPlatform[platform.id] || [];

          return (
            <Card key={platform.id} className="border-slate-200 shadow-sm">
              <CardHeader className="flex flex-row items-start justify-between gap-4">
                <div>
                  <CardTitle className="flex items-center gap-2 text-xl">
                    <span className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100">
                      <Icon className="h-5 w-5" />
                    </span>
                    {platform.label}
                  </CardTitle>
                  <CardDescription>{platform.description}</CardDescription>
                </div>
                <Badge
                  variant="outline"
                  className={`whitespace-nowrap ${platform.badgeClass}`}
                >
                  {platformAccounts.length > 0
                    ? `${platformAccounts.length} connected`
                    : "Not connected"}
                </Badge>
              </CardHeader>
              <CardContent className="space-y-4">
                {platformAccounts.length > 0 ? (
                  <div className="space-y-3">
                    {platformAccounts.map((account) => {
                      const connectedAt =
                        parseDateValue(account.connected_at) ||
                        parseDateValue(account.connectedAt);
                      const expiryInfo = computeExpiryInfo(account);

                      return (
                        <div
                          key={account.account_id}
                          className="flex flex-col gap-4 rounded-lg border border-slate-200 bg-slate-50 p-4 sm:flex-row sm:items-center sm:justify-between"
                        >
                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-semibold text-slate-900">
                                {account.account_name || account.display_name || account.account_id}
                              </span>
                              {expiryInfo.isExpired ? (
                                <Badge variant="destructive">
                                  Token expired
                                </Badge>
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
                            {connectedAt && (
                              <p className="flex items-center gap-2 text-xs text-slate-500">
                                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                                Connected{" "}
                                {formatDistanceToNow(connectedAt, {
                                  addSuffix: true,
                                })}
                              </p>
                            )}
                            {expiryInfo.expiresAt ? (
                              <p className="flex items-center gap-2 text-xs text-slate-500">
                                <Clock className="h-4 w-4 text-slate-400" />
                                {expiryInfo.isExpired
                                  ? `Token expired ${formatDistanceToNow(
                                      expiryInfo.expiresAt,
                                      { addSuffix: true }
                                    )}`
                                  : `Expires ${formatDistanceToNow(
                                      expiryInfo.expiresAt,
                                      { addSuffix: true }
                                    )} (${format(
                                      expiryInfo.expiresAt,
                                      "PPpp"
                                    )})`}
                              </p>
                            ) : (
                              <p className="flex items-center gap-2 text-xs text-slate-500">
                                <AlertTriangle className="h-4 w-4 text-amber-500" />
                                Token expiry data unavailable
                              </p>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() =>
                                handleDisconnect(account.account_id, platform.id)
                              }
                              disabled={disconnectingAccount === account.account_id}
                            >
                              {disconnectingAccount === account.account_id ? (
                                <>
                                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                  Removing...
                                </>
                              ) : (
                                <>
                                  <Unlink className="mr-2 h-4 w-4" />
                                  Disconnect
                                </>
                              )}
                            </Button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <Alert className="border-dashed border-slate-200 bg-white text-slate-600">
                    <AlertDescription className="text-sm leading-6">
                      No {platform.label} accounts connected yet. Click{" "}
                      <strong>Connect</strong> to start the OAuth flow, approve
                      access, and return here to manage the connection.
                    </AlertDescription>
                  </Alert>
                )}

                <div className="flex flex-wrap gap-2 pt-2">
                  <Button
                    onClick={() => handleConnect(platform.id)}
                    disabled={connectingPlatform === platform.id}
                    className="w-full sm:w-auto"
                  >
                    {connectingPlatform === platform.id ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Redirecting...
                      </>
                    ) : (
                      <>
                        <Link2 className="mr-2 h-4 w-4" />
                        Connect {platform.label}
                      </>
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => refreshAccounts({ silent: true })}
                    disabled={isRefreshing}
                    className="w-full sm:w-auto"
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Sync Accounts
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default SocialMediaCredentialsPage;
