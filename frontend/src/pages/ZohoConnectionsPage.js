import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "sonner";
import { CheckCircle2, XCircle, RefreshCw, Link as LinkIcon, Unlink } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const API_URL = `${BACKEND_URL}/api`;

const ZohoConnectionsPage = () => {
  const [connected, setConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    checkConnectionStatus();

    // Check for OAuth callback params
    const params = new URLSearchParams(window.location.search);
    if (params.get('zoho') === 'connected') {
      toast.success('Successfully connected to Zoho!');
      checkConnectionStatus();
    } else if (params.get('zoho') === 'error') {
      toast.error('Failed to connect to Zoho. Please try again.');
    }
  }, []);

  const checkConnectionStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/zoho/status?user_id=default_user`);
      const data = await response.json();

      if (data.connected && !data.is_expired) {
        setConnected(true);
        setConnectionStatus(data);
      } else {
        setConnected(false);
        setConnectionStatus(null);
      }
    } catch (error) {
      console.error('Error checking connection status:', error);
      setConnected(false);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/zoho/connect?user_id=default_user`);
      const data = await response.json();

      if (data.status === 'success') {
        // Redirect to Zoho OAuth page
        window.location.href = data.authorization_url;
      } else {
        toast.error('Failed to initiate Zoho connection');
      }
    } catch (error) {
      console.error('Error connecting to Zoho:', error);
      toast.error('Failed to connect to Zoho');
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/zoho/disconnect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'default_user' })
      });

      const data = await response.json();

      if (data.status === 'success') {
        setConnected(false);
        setConnectionStatus(null);
        toast.success('Disconnected from Zoho');
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

  const formatDate = (isoString) => {
    if (!isoString) return 'N/A';
    return new Date(isoString).toLocaleString();
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Zoho Integration</h1>
        <p className="text-gray-600 mb-6">
          Connect your Zoho account to enable campaigns, email marketing, and analytics
        </p>

        {/* Connection Status Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Connection Status</span>
              {connected ? (
                <Badge variant="success" className="ml-2 flex items-center gap-1">
                  <CheckCircle2 className="h-4 w-4" />
                  Connected
                </Badge>
              ) : (
                <Badge variant="secondary" className="ml-2 flex items-center gap-1">
                  <XCircle className="h-4 w-4" />
                  Not Connected
                </Badge>
              )}
            </CardTitle>
            <CardDescription>
              Manage your Zoho account connection
            </CardDescription>
          </CardHeader>
          <CardContent>
            {connected && connectionStatus ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Connected At</p>
                    <p className="font-medium">{formatDate(connectionStatus.updated_at)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Token Expires</p>
                    <p className="font-medium">{formatDate(connectionStatus.expires_at)}</p>
                  </div>
                </div>

                {connectionStatus.scope && (
                  <div>
                    <p className="text-sm text-gray-500 mb-2">Permissions Granted</p>
                    <div className="flex flex-wrap gap-2">
                      {connectionStatus.scope.split(',').map((scope, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {scope.trim()}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex gap-2 pt-4">
                  <Button
                    onClick={handleDisconnect}
                    variant="destructive"
                    disabled={loading}
                  >
                    <Unlink className="mr-2 h-4 w-4" />
                    Disconnect
                  </Button>
                  <Button
                    onClick={checkConnectionStatus}
                    variant="outline"
                    disabled={loading}
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Refresh Status
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <Alert>
                  <AlertDescription>
                    Connect to Zoho to unlock powerful features including:
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>Campaign Management in Zoho CRM</li>
                      <li>Email Sending via Zoho Mail</li>
                      <li>Email Marketing Campaigns</li>
                      <li>Data Visualization with Zoho Analytics</li>
                      <li>Customer Data Management</li>
                    </ul>
                  </AlertDescription>
                </Alert>

                <Button
                  onClick={handleConnect}
                  disabled={loading}
                  className="w-full sm:w-auto"
                >
                  <LinkIcon className="mr-2 h-4 w-4" />
                  {loading ? 'Connecting...' : 'Connect to Zoho'}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Features Card */}
        <Card>
          <CardHeader>
            <CardTitle>Available Zoho Services</CardTitle>
            <CardDescription>
              Services available after connecting
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 border rounded-lg">
                <h3 className="font-semibold mb-2">Zoho CRM</h3>
                <p className="text-sm text-gray-600">
                  Manage campaigns, track leads, and store customer data
                </p>
              </div>

              <div className="p-4 border rounded-lg">
                <h3 className="font-semibold mb-2">Zoho Mail</h3>
                <p className="text-sm text-gray-600">
                  Send individual and bulk emails with personalization
                </p>
              </div>

              <div className="p-4 border rounded-lg">
                <h3 className="font-semibold mb-2">Zoho Campaigns</h3>
                <p className="text-sm text-gray-600">
                  Create and manage email marketing campaigns with analytics
                </p>
              </div>

              <div className="p-4 border rounded-lg">
                <h3 className="font-semibold mb-2">Zoho Analytics</h3>
                <p className="text-sm text-gray-600">
                  Visualize data with 75+ chart types and custom dashboards
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ZohoConnectionsPage;
