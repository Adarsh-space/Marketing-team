import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import {
  Coins,
  TrendingUp,
  DollarSign,
  AlertCircle,
  RefreshCw,
  ShoppingCart,
  Activity,
  Calendar
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export default function CreditsDashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [creditsBalance, setCreditsBalance] = useState(0);
  const [usageSummary, setUsageSummary] = useState(null);
  const [transactionHistory, setTransactionHistory] = useState([]);
  const [planType, setPlanType] = useState('Free');

  const tenantId = localStorage.getItem('tenant_id');
  const authToken = localStorage.getItem('auth_token');

  useEffect(() => {
    loadCreditsData();
  }, []);

  const loadCreditsData = async () => {
    if (!authToken) {
      navigate('/login');
      return;
    }

    try {
      setLoading(true);

      // Get credits balance
      const balanceResponse = await axios.get(
        `${BACKEND_URL}/api/credits/balance`,
        {
          headers: { Authorization: `Bearer ${authToken}` },
          params: { tenant_id: tenantId }
        }
      );

      if (balanceResponse.data.status === 'success') {
        setCreditsBalance(balanceResponse.data.credits_balance || 0);
        setPlanType(balanceResponse.data.plan_type || 'Free');
      }

      // Get usage summary
      const usageResponse = await axios.get(
        `${BACKEND_URL}/api/credits/usage`,
        {
          headers: { Authorization: `Bearer ${authToken}` },
          params: { tenant_id: tenantId, days: 30 }
        }
      );

      if (usageResponse.data.status === 'success') {
        setUsageSummary(usageResponse.data.summary);
      }

      // Get transaction history
      const historyResponse = await axios.get(
        `${BACKEND_URL}/api/credits/history`,
        {
          headers: { Authorization: `Bearer ${authToken}` },
          params: { tenant_id: tenantId }
        }
      );

      if (historyResponse.data.status === 'success') {
        setTransactionHistory(historyResponse.data.transactions || []);
      }

    } catch (error) {
      console.error('Error loading credits data:', error);
      toast.error('Failed to load credits data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadCreditsData();
    setRefreshing(false);
    toast.success('Credits data refreshed');
  };

  const getCreditStatusColor = () => {
    if (creditsBalance < 10) return 'text-red-600 bg-red-50';
    if (creditsBalance < 100) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };

  const getCreditStatusIcon = () => {
    if (creditsBalance < 10) return <AlertCircle className="w-5 h-5 text-red-600" />;
    if (creditsBalance < 100) return <AlertCircle className="w-5 h-5 text-yellow-600" />;
    return <Coins className="w-5 h-5 text-green-600" />;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading credits data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 to-indigo-100 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Credits Dashboard</h1>
            <p className="text-gray-600 mt-1">Manage your credits and monitor usage</p>
          </div>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button onClick={() => navigate('/payment')}>
              <ShoppingCart className="w-4 h-4 mr-2" />
              Buy Credits
            </Button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        {/* Credits Balance */}
        <Card className={getCreditStatusColor()}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Credits Balance</CardTitle>
            {getCreditStatusIcon()}
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{creditsBalance.toFixed(2)}</div>
            <p className="text-xs mt-2">
              {creditsBalance < 10 && '⚠️ Critical - Buy credits now!'}
              {creditsBalance >= 10 && creditsBalance < 100 && '⚠️ Low balance'}
              {creditsBalance >= 100 && '✅ Good balance'}
            </p>
          </CardContent>
        </Card>

        {/* Plan Type */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Plan Type</CardTitle>
            <TrendingUp className="w-5 h-5 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{planType}</div>
            <p className="text-xs text-gray-500 mt-2">
              {planType === 'Free' && 'Upgrade for more credits'}
              {planType !== 'Free' && `${planType} plan active`}
            </p>
          </CardContent>
        </Card>

        {/* Total Spent (30 days) */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Credits Spent (30d)</CardTitle>
            <Activity className="w-5 h-5 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {usageSummary?.total_credits_spent?.toFixed(2) || '0.00'}
            </div>
            <p className="text-xs text-gray-500 mt-2">Last 30 days</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto">
        <Tabs defaultValue="usage" className="space-y-4">
          <TabsList>
            <TabsTrigger value="usage">Usage Breakdown</TabsTrigger>
            <TabsTrigger value="history">Transaction History</TabsTrigger>
          </TabsList>

          {/* Usage Breakdown Tab */}
          <TabsContent value="usage" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Usage by Feature (Last 30 Days)</CardTitle>
                <CardDescription>
                  See how your credits are being used across different features
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {usageSummary?.usage_by_type && Object.keys(usageSummary.usage_by_type).length > 0 ? (
                  Object.entries(usageSummary.usage_by_type).map(([type, data]) => (
                    <div key={type} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Activity className="w-5 h-5 text-gray-400" />
                          <div>
                            <p className="font-medium capitalize">{type.replace(/_/g, ' ')}</p>
                            <p className="text-sm text-gray-500">{data.count} operations</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold">{data.credits_spent?.toFixed(4)} credits</p>
                        </div>
                      </div>
                      <Progress
                        value={
                          ((data.credits_spent / usageSummary.total_credits_spent) * 100) || 0
                        }
                        className="h-2"
                      />
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Activity className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p>No usage data for the last 30 days</p>
                    <p className="text-sm">Start using features to see usage breakdown</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Transaction History Tab */}
          <TabsContent value="history" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Credit Purchase History</CardTitle>
                <CardDescription>
                  View all your credit purchases and additions
                </CardDescription>
              </CardHeader>
              <CardContent>
                {transactionHistory.length > 0 ? (
                  <div className="space-y-3">
                    {transactionHistory.map((transaction, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                      >
                        <div className="flex items-center gap-3">
                          <DollarSign className="w-5 h-5 text-green-600" />
                          <div>
                            <p className="font-medium">{transaction.package} Package</p>
                            <p className="text-sm text-gray-500 flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              {new Date(transaction.timestamp).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold text-green-600">
                            +{transaction.credits_added} credits
                          </p>
                          <p className="text-sm text-gray-500">
                            ${transaction.amount_usd}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <DollarSign className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p>No purchase history yet</p>
                    <p className="text-sm mb-4">Buy credits to see your transaction history</p>
                    <Button onClick={() => navigate('/payment')}>
                      <ShoppingCart className="w-4 h-4 mr-2" />
                      Buy Credits Now
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
