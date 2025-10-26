import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { CheckCircle2, XCircle, Facebook, Instagram, Unlink, RefreshCw } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000/api';

const SocialMediaCredentialsPage = () => {
  const [facebookConnected, setFacebookConnected] = useState(false);
  const [instagramConnected, setInstagramConnected] = useState(false);
  const [facebookPages, setFacebookPages] = useState([]);
  const [instagramAccounts, setInstagramAccounts] = useState([]);
  const [selectedPage, setSelectedPage] = useState('');
  const [selectedInstagram, setSelectedInstagram] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    checkConnectionStatus();

    // Check for OAuth callback params
    const params = new URLSearchParams(window.location.search);
    if (params.get('facebook') === 'connected') {
      toast.success('Successfully connected to Facebook!');
      setFacebookConnected(true);
      loadFacebookPages();
      loadInstagramAccounts();
    } else if (params.get('facebook') === 'error') {
      toast.error('Failed to connect to Facebook. Please try again.');
    }
  }, []);

  const checkConnectionStatus = async () => {
    // Check if credentials exist by trying to load pages/accounts
    await loadFacebookPages();
    await loadInstagramAccounts();
  };

  const loadFacebookPages = async () => {
    try {
      const response = await fetch(`${API_URL}/social-media/facebook/pages?user_id=default_user`);
      const data = await response.json();

      if (data.status === 'success' && data.pages && data.pages.length > 0) {
        setFacebookPages(data.pages);
        setFacebookConnected(true);
        if (data.pages.length > 0) {
          setSelectedPage(data.pages[0].id);
        }
      } else {
        setFacebookConnected(false);
        setFacebookPages([]);
      }
    } catch (error) {
      console.error('Error loading Facebook pages:', error);
      setFacebookConnected(false);
    }
  };

  const loadInstagramAccounts = async () => {
    try {
      const response = await fetch(`${API_URL}/social-media/instagram/accounts?user_id=default_user`);
      const data = await response.json();

      if (data.status === 'success' && data.accounts && data.accounts.length > 0) {
        setInstagramAccounts(data.accounts);
        setInstagramConnected(true);
        if (data.accounts.length > 0) {
          setSelectedInstagram(data.accounts[0].instagram_account_id);
        }
      } else {
        setInstagramConnected(false);
        setInstagramAccounts([]);
      }
    } catch (error) {
      console.error('Error loading Instagram accounts:', error);
      setInstagramConnected(false);
    }
  };

  const handleFacebookConnect = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/social-media/facebook/connect?user_id=default_user`);
      const data = await response.json();

      if (data.status === 'success') {
        // Redirect to Facebook OAuth
        window.location.href = data.authorization_url;
      } else {
        toast.error('Failed to initiate Facebook connection');
        setLoading(false);
      }
    } catch (error) {
      console.error('Error connecting to Facebook:', error);
      toast.error('Failed to connect to Facebook');
      setLoading(false);
    }
  };

  const handleDisconnectFacebook = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/social-media/credentials/facebook?user_id=default_user`, {
        method: 'DELETE'
      });

      const data = await response.json();

      if (data.status === 'success') {
        setFacebookConnected(false);
        setFacebookPages([]);
        setInstagramConnected(false);
        setInstagramAccounts([]);
        toast.success('Disconnected from Facebook and Instagram');
      } else {
        toast.error('Failed to disconnect');
      }
    } catch (error) {
      console.error('Error disconnecting:', error);
      toast.error('Failed to disconnect');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setLoading(true);
    await checkConnectionStatus();
    setLoading(false);
    toast.success('Connection status refreshed');
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Social Media Connections</h1>
        <p className="text-gray-600 mb-6">
          Connect your social media accounts to enable direct posting
        </p>

        {/* Facebook Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Facebook className="h-5 w-5 text-blue-600" />
                Facebook
              </span>
              {facebookConnected ? (
                <Badge variant="success" className="flex items-center gap-1">
                  <CheckCircle2 className="h-4 w-4" />
                  Connected
                </Badge>
              ) : (
                <Badge variant="secondary" className="flex items-center gap-1">
                  <XCircle className="h-4 w-4" />
                  Not Connected
                </Badge>
              )}
            </CardTitle>
            <CardDescription>
              Post to your Facebook pages automatically
            </CardDescription>
          </CardHeader>
          <CardContent>
            {facebookConnected ? (
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Select Facebook Page
                  </label>
                  <Select value={selectedPage} onValueChange={setSelectedPage}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a page" />
                    </SelectTrigger>
                    <SelectContent>
                      {facebookPages.map((page) => (
                        <SelectItem key={page.id} value={page.id}>
                          {page.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-gray-500 mt-1">
                    Posts will be published to this page
                  </p>
                </div>

                <Alert>
                  <AlertDescription>
                    <strong>{facebookPages.length}</strong> page(s) available for posting
                  </AlertDescription>
                </Alert>

                <div className="flex gap-2">
                  <Button
                    onClick={handleDisconnectFacebook}
                    variant="destructive"
                    disabled={loading}
                  >
                    <Unlink className="mr-2 h-4 w-4" />
                    Disconnect
                  </Button>
                  <Button
                    onClick={handleRefresh}
                    variant="outline"
                    disabled={loading}
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Refresh
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <Alert>
                  <AlertDescription>
                    Connect your Facebook account to:
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>Post directly to your Facebook pages</li>
                      <li>Share images and links automatically</li>
                      <li>Schedule posts for later</li>
                      <li>AI-generated content posting</li>
                    </ul>
                  </AlertDescription>
                </Alert>

                <Button
                  onClick={handleFacebookConnect}
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Facebook className="mr-2 h-4 w-4" />
                  {loading ? 'Connecting...' : 'Connect Facebook'}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Instagram Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Instagram className="h-5 w-5 text-pink-600" />
                Instagram
              </span>
              {instagramConnected ? (
                <Badge variant="success" className="flex items-center gap-1">
                  <CheckCircle2 className="h-4 w-4" />
                  Connected
                </Badge>
              ) : (
                <Badge variant="secondary" className="flex items-center gap-1">
                  <XCircle className="h-4 w-4" />
                  Not Connected
                </Badge>
              )}
            </CardTitle>
            <CardDescription>
              Post to your Instagram Business accounts
            </CardDescription>
          </CardHeader>
          <CardContent>
            {instagramConnected ? (
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Select Instagram Account
                  </label>
                  <Select value={selectedInstagram} onValueChange={setSelectedInstagram}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select an account" />
                    </SelectTrigger>
                    <SelectContent>
                      {instagramAccounts.map((account) => (
                        <SelectItem key={account.instagram_account_id} value={account.instagram_account_id}>
                          {account.page_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-gray-500 mt-1">
                    Posts will be published to this Instagram account
                  </p>
                </div>

                <Alert>
                  <AlertDescription>
                    <strong>{instagramAccounts.length}</strong> Business account(s) available for posting
                  </AlertDescription>
                </Alert>

                <Alert variant="warning">
                  <AlertDescription>
                    Note: Instagram posting requires a Business or Creator account linked to a Facebook page.
                    Images must be publicly accessible URLs.
                  </AlertDescription>
                </Alert>
              </div>
            ) : (
              <div className="space-y-4">
                <Alert>
                  <AlertDescription>
                    Instagram posting requires:
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>Instagram Business or Creator account</li>
                      <li>Account linked to a Facebook page</li>
                      <li>Facebook connection (connect Facebook first)</li>
                    </ul>
                  </AlertDescription>
                </Alert>

                {!facebookConnected && (
                  <Alert variant="info">
                    <AlertDescription>
                      <strong>Connect Facebook first</strong> to enable Instagram posting.
                    </AlertDescription>
                  </Alert>
                )}

                <Button
                  onClick={handleFacebookConnect}
                  disabled={loading || facebookConnected}
                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                >
                  <Instagram className="mr-2 h-4 w-4" />
                  {facebookConnected ? 'Instagram Connected via Facebook' : 'Connect Instagram (via Facebook)'}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Info Card */}
        <Card>
          <CardHeader>
            <CardTitle>Important Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 text-sm">
              <div>
                <h4 className="font-semibold mb-1">Facebook Posting</h4>
                <ul className="list-disc list-inside text-gray-600 space-y-1">
                  <li>Can only post to pages (not personal timeline)</li>
                  <li>Requires page admin access</li>
                  <li>Supports text, images, and links</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold mb-1">Instagram Posting</h4>
                <ul className="list-disc list-inside text-gray-600 space-y-1">
                  <li>Requires Business or Creator account</li>
                  <li>Must be linked to a Facebook page</li>
                  <li>Images must be publicly accessible URLs</li>
                  <li>Cannot post stories via API</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold mb-1">Security</h4>
                <p className="text-gray-600">
                  Your credentials are encrypted and stored securely in Zoho CRM.
                  You can disconnect at any time.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default SocialMediaCredentialsPage;
