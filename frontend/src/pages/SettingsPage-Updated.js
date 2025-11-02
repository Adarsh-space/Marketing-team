import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import {
  Sparkles,
  ArrowLeft,
  Check,
  Facebook,
  Instagram,
  Linkedin,
  Twitter,
  Globe,
  X,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Link as LinkIcon,
  Unlink,
  Loader2
} from "lucide-react";
import { toast } from "sonner";
import {
  getSocialOAuthUrl,
  getConnectedAccounts,
  disconnectAccount,
  getZohoOAuthUrl,
  getZohoStatus,
  disconnectZoho,
  refreshTokens,
  getTokenStatus,
  isTokenExpiringSoon,
  isTokenExpired
} from "@/services/marketingApi";
import { DEFAULT_USER_ID } from "@/lib/api";

const SOCIAL_PLATFORMS = [
  {
    id: "facebook",
    name: "Facebook",
    icon: Facebook,
    color: "bg-blue-500",
    description: "Connect your Facebook Page to post and track engagement"
  },
  {
    id: "instagram",
    name: "Instagram",
    icon: Instagram,
    color: "bg-pink-500",
    description: "Connect Instagram Business account for posts and analytics"
  },
  {
    id: "twitter",
    name: "Twitter / X",
    icon: Twitter,
    color: "bg-slate-700",
    description: "Connect your X account to publish tweets and monitor performance"
  },
  {
    id: "linkedin",
    name: "LinkedIn",
    icon: Linkedin,
    color: "bg-sky-600",
    description: "Connect LinkedIn page for professional content and insights"
  }
];

const SettingsPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Social Media State
  const [connectedAccounts, setConnectedAccounts] = useState([]);
  const [accountsLoading, setAccountsLoading] = useState(true);
  const [connecting, setConnecting] = useState({});
  const [disconnecting, setDisconnecting] = useState({});
  const [tokenStatus, setTokenStatus] = useState(null);
  const [refreshingTokens, setRefreshingTokens] = useState({});

  // Zoho State
  const [zohoConnected, setZohoConnected] = useState(false);
  const [zohoLoading, setZohoLoading] = useState(true);
  const [zohoConnecting, setZohoConnecting] = useState(false);
  const [zohoDisconnecting, setZohoDisconnecting] = useState(false);
  const [zohoStatus, setZohoStatus] = useState(null);

  useEffect(() => {
    loadConnectedAccounts();
    loadZohoStatus();
    loadTokenStatus();

    // Check for OAuth callback results
    const connected = searchParams.get('connected');
    const error = searchParams.get('error');
    const zoho = searchParams.get('zoho');

    if (connected) {
      toast.success(`${connected.charAt(0).toUpperCase() + connected.slice(1)} connected successfully!`);
      // Reload accounts after OAuth success
      setTimeout(loadConnectedAccounts, 1000);
    }

    if (zoho === 'connected') {
      toast.success('Zoho connected successfully!');
      setTimeout(loadZohoStatus, 1000);
    }

    if (error) {
      toast.error(`Connection failed: ${error}`);
    }
  }, [searchParams]);

  const loadConnectedAccounts = async () => {
    try {
      setAccountsLoading(true);
      const response = await getConnectedAccounts(DEFAULT_USER_ID);
      if (response.success) {
        setConnectedAccounts(response.accounts || []);
      }
    } catch (error) {
      console.error('Error loading accounts:', error);
      toast.error('Failed to load connected accounts');
    } finally {
      setAccountsLoading(false);
    }
  };

  const loadZohoStatus = async () => {
    try {
      setZohoLoading(true);
      const status = await getZohoStatus(DEFAULT_USER_ID);
      setZohoConnected(status.connected || false);
      setZohoStatus(status);
    } catch (error) {
      console.error('Error loading Zoho status:', error);
      setZohoConnected(false);
    } finally {
      setZohoLoading(false);
    }
  };

  const loadTokenStatus = async () => {
    try {
      const status = await getTokenStatus(DEFAULT_USER_ID);
      setTokenStatus(status);
    } catch (error) {
      console.error('Error loading token status:', error);
    }
  };

  const handleConnectSocial = async (platform) => {
    try {
      setConnecting(prev => ({ ...prev, [platform]: true }));
      const response = await getSocialOAuthUrl(platform, DEFAULT_USER_ID);

      if (response.success && response.auth_url) {
        // Redirect to OAuth authorization URL
        window.location.href = response.auth_url;
      } else {
        toast.error(`Failed to get ${platform} authorization URL`);
      }
    } catch (error) {
      console.error(`Error connecting ${platform}:`, error);
      toast.error(`Failed to connect ${platform}`);
    } finally {
      setConnecting(prev => ({ ...prev, [platform]: false }));
    }
  };

  const handleDisconnectSocial = async (account) => {
    try {
      setDisconnecting(prev => ({ ...prev, [account.account_id]: true }));
      const response = await disconnectAccount(account.account_id, DEFAULT_USER_ID);

      if (response.success) {
        toast.success(`${account.platform} account disconnected`);
        loadConnectedAccounts();
      }
    } catch (error) {
      console.error('Error disconnecting account:', error);
      toast.error('Failed to disconnect account');
    } finally {
      setDisconnecting(prev => ({ ...prev, [account.account_id]: false }));
    }
  };

  const handleRefreshToken = async (platform, accountId) => {
    try {
      setRefreshingTokens(prev => ({ ...prev, [accountId]: true }));
      const response = await refreshTokens(DEFAULT_USER_ID, platform);

      if (response.success) {
        toast.success(`${platform} token refreshed successfully`);
        loadTokenStatus();
        loadConnectedAccounts();
      }
    } catch (error) {
      console.error('Error refreshing token:', error);
      toast.error('Failed to refresh token');
    } finally {
      setRefreshingTokens(prev => ({ ...prev, [accountId]: false }));
    }
  };

  const handleConnectZoho = async () => {
    try {
      setZohoConnecting(true);
      const response = await getZohoOAuthUrl(DEFAULT_USER_ID);

      if (response.authorization_url) {
        window.location.href = response.authorization_url;
      }
    } catch (error) {
      console.error('Error connecting Zoho:', error);
      toast.error('Failed to connect Zoho');
    } finally {
      setZohoConnecting(false);
    }
  };

  const handleDisconnectZoho = async () => {
    try {
      setZohoDisconnecting(true);
      const response = await disconnectZoho(DEFAULT_USER_ID);

      if (response.success) {
        toast.success('Zoho disconnected successfully');
        loadZohoStatus();
      }
    } catch (error) {
      console.error('Error disconnecting Zoho:', error);
      toast.error('Failed to disconnect Zoho');
    } finally {
      setZohoDisconnecting(false);
    }
  };

  const getAccountsForPlatform = (platformId) => {
    return connectedAccounts.filter(acc => acc.platform === platformId);
  };

  const getTokenStatusForAccount = (accountId) => {
    if (!tokenStatus || !tokenStatus.social_accounts) return null;
    return tokenStatus.social_accounts.find(t => t.account_id === accountId);
  };

  const renderTokenStatus = (account) => {
    const status = getTokenStatusForAccount(account.account_id);
    if (!status) return null;

    if (status.is_expired) {
      return (
        <div className="flex items-center gap-2 text-red-600">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">Token Expired</span>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleRefreshToken(account.platform, account.account_id)}
            disabled={refreshingTokens[account.account_id]}
            className="ml-2"
          >
            {refreshingTokens[account.account_id] ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <RefreshCw className="w-3 h-3" />
            )}
          </Button>
        </div>
      );
    }

    if (status.is_expiring_soon) {
      return (
        <div className="flex items-center gap-2 text-amber-600">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">Expires Soon</span>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleRefreshToken(account.platform, account.account_id)}
            disabled={refreshingTokens[account.account_id]}
            className="ml-2"
          >
            {refreshingTokens[account.account_id] ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <RefreshCw className="w-3 h-3" />
            )}
          </Button>
        </div>
      );
    }

    return (
      <div className="flex items-center gap-2 text-green-600">
        <CheckCircle2 className="w-4 h-4" />
        <span className="text-sm">Active</span>
      </div>
    );
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
              MarketingMinds AI
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

      {/* Main Content */}
      <div className="pt-24 pb-12 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Settings & Integrations</h1>
            <p className="text-gray-600">Connect your accounts and manage integrations</p>
          </div>

          {/* Zoho Integration Section */}
          <Card className="mb-6 border-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="w-6 h-6 text-orange-500" />
                Zoho Integration
              </CardTitle>
              <CardDescription>
                Connect Zoho for CRM, Email Campaigns, and Analytics
              </CardDescription>
            </CardHeader>
            <CardContent>
              {zohoLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                </div>
              ) : zohoConnected ? (
                <div className="space-y-4">
                  <Alert className="border-green-200 bg-green-50">
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                    <AlertDescription className="text-green-800">
                      Zoho is connected and ready to use for CRM, Email, Campaigns, and Analytics
                      {zohoStatus?.expires_at && (
                        <span className="block text-sm mt-1">
                          Token expires: {new Date(zohoStatus.expires_at).toLocaleString()}
                        </span>
                      )}
                    </AlertDescription>
                  </Alert>
                  <Button
                    onClick={handleDisconnectZoho}
                    disabled={zohoDisconnecting}
                    variant="destructive"
                  >
                    {zohoDisconnecting ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Disconnecting...
                      </>
                    ) : (
                      <>
                        <Unlink className="w-4 h-4 mr-2" />
                        Disconnect Zoho
                      </>
                    )}
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <Alert>
                    <AlertCircle className="w-4 h-4" />
                    <AlertDescription>
                      Zoho is not connected. Click the button below to authorize access to Zoho CRM, Mail, Campaigns, and Analytics.
                    </AlertDescription>
                  </Alert>
                  <Button
                    onClick={handleConnectZoho}
                    disabled={zohoConnecting}
                    className="bg-orange-500 hover:bg-orange-600"
                  >
                    {zohoConnecting ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Connecting...
                      </>
                    ) : (
                      <>
                        <LinkIcon className="w-4 h-4 mr-2" />
                        Connect Zoho
                      </>
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          <Separator className="my-6" />

          {/* Social Media Integration Section */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-1">Social Media Accounts</h2>
            <p className="text-gray-600 mb-6">Connect your social media accounts for multi-platform posting and analytics</p>
          </div>

          {accountsLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {SOCIAL_PLATFORMS.map((platform) => {
                const Icon = platform.icon;
                const accounts = getAccountsForPlatform(platform.id);
                const isConnected = accounts.length > 0;

                return (
                  <Card key={platform.id} className="border-2 hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-12 h-12 rounded-lg ${platform.color} flex items-center justify-center`}>
                            <Icon className="w-6 h-6 text-white" />
                          </div>
                          <div>
                            <CardTitle className="text-lg">{platform.name}</CardTitle>
                            <CardDescription className="text-sm">{platform.description}</CardDescription>
                          </div>
                        </div>
                        {isConnected && (
                          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Connected ({accounts.length})
                          </Badge>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent>
                      {isConnected ? (
                        <div className="space-y-3">
                          {accounts.map((account) => (
                            <div key={account.account_id} className="p-3 bg-gray-50 rounded-lg space-y-2">
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="font-medium text-gray-900">{account.account_name || 'Connected Account'}</p>
                                  <p className="text-sm text-gray-500">
                                    Connected {new Date(account.connected_at).toLocaleDateString()}
                                  </p>
                                </div>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleDisconnectSocial(account)}
                                  disabled={disconnecting[account.account_id]}
                                >
                                  {disconnecting[account.account_id] ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                  ) : (
                                    <X className="w-4 h-4" />
                                  )}
                                </Button>
                              </div>
                              {renderTokenStatus(account)}
                            </div>
                          ))}
                          <Button
                            onClick={() => handleConnectSocial(platform.id)}
                            disabled={connecting[platform.id]}
                            variant="outline"
                            className="w-full"
                          >
                            {connecting[platform.id] ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Connecting...
                              </>
                            ) : (
                              <>
                                <LinkIcon className="w-4 h-4 mr-2" />
                                Add Another Account
                              </>
                            )}
                          </Button>
                        </div>
                      ) : (
                        <Button
                          onClick={() => handleConnectSocial(platform.id)}
                          disabled={connecting[platform.id]}
                          className={`w-full ${platform.color} hover:opacity-90`}
                        >
                          {connecting[platform.id] ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Connecting...
                            </>
                          ) : (
                            <>
                              <LinkIcon className="w-4 h-4 mr-2" />
                              Connect {platform.name}
                            </>
                          )}
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          {/* Info Section */}
          <Alert className="mt-8">
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>
              <strong>OAuth Connection:</strong> When you click "Connect", you'll be redirected to the platform's authorization page.
              After authorizing, you'll be redirected back here. Your tokens are automatically refreshed to keep connections active.
            </AlertDescription>
          </Alert>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
