import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "sonner";
import { BarChart3, TrendingUp, Activity, RefreshCw } from "lucide-react";
import ChartRenderer from "@/components/ChartRenderer";
import DataTable from "@/components/DataTable";

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000/api';

const AnalyticsDashboard = () => {
  const [loading, setLoading] = useState(false);
  const [workspaces, setWorkspaces] = useState([]);
  const [sampleData, setSampleData] = useState([]);

  useEffect(() => {
    loadSampleData();
  }, []);

  const loadSampleData = () => {
    // Sample data for demonstration
    // In production, this would come from Zoho Analytics API
    setSampleData([
      {
        id: 1,
        campaign_name: 'Summer Sale 2025',
        status: 'Active',
        emails_sent: 5000,
        open_rate: 32.5,
        click_rate: 12.3,
        conversion_rate: 4.8,
        revenue: 12500,
        date: '2025-01-15'
      },
      {
        id: 2,
        campaign_name: 'Product Launch',
        status: 'Completed',
        emails_sent: 8000,
        open_rate: 28.7,
        click_rate: 10.5,
        conversion_rate: 3.2,
        revenue: 18900,
        date: '2025-01-10'
      },
      {
        id: 3,
        campaign_name: 'Newsletter Q1',
        status: 'Active',
        emails_sent: 3500,
        open_rate: 45.2,
        click_rate: 18.9,
        conversion_rate: 6.5,
        revenue: 8700,
        date: '2025-01-20'
      },
      {
        id: 4,
        campaign_name: 'Black Friday',
        status: 'Completed',
        emails_sent: 12000,
        open_rate: 38.4,
        click_rate: 15.7,
        conversion_rate: 7.2,
        revenue: 45600,
        date: '2024-11-29'
      },
      {
        id: 5,
        campaign_name: 'Customer Appreciation',
        status: 'Completed',
        emails_sent: 6000,
        open_rate: 52.3,
        click_rate: 22.1,
        conversion_rate: 9.8,
        revenue: 21300,
        date: '2025-01-05'
      }
    ]);
  };

  const handleRefresh = async () => {
    setLoading(true);
    // In production, fetch real data from Zoho Analytics
    await new Promise(resolve => setTimeout(resolve, 1000));
    loadSampleData();
    setLoading(false);
    toast.success('Data refreshed');
  };

  const columns = [
    {
      key: 'campaign_name',
      label: 'Campaign',
      width: '200px'
    },
    {
      key: 'status',
      label: 'Status',
      width: '100px',
      render: (value) => (
        <Badge variant={value === 'Active' ? 'success' : 'secondary'}>
          {value}
        </Badge>
      )
    },
    {
      key: 'emails_sent',
      label: 'Emails Sent',
      type: 'number',
      width: '120px'
    },
    {
      key: 'open_rate',
      label: 'Open Rate',
      width: '100px',
      format: (value) => `${value}%`
    },
    {
      key: 'click_rate',
      label: 'Click Rate',
      width: '100px',
      format: (value) => `${value}%`
    },
    {
      key: 'conversion_rate',
      label: 'Conversion',
      width: '100px',
      format: (value) => `${value}%`
    },
    {
      key: 'revenue',
      label: 'Revenue',
      type: 'currency',
      width: '120px'
    },
    {
      key: 'date',
      label: 'Date',
      type: 'date',
      width: '120px'
    }
  ];

  // Calculate summary metrics
  const totalEmailsSent = sampleData.reduce((sum, item) => sum + item.emails_sent, 0);
  const averageOpenRate = (sampleData.reduce((sum, item) => sum + item.open_rate, 0) / sampleData.length).toFixed(1);
  const averageClickRate = (sampleData.reduce((sum, item) => sum + item.click_rate, 0) / sampleData.length).toFixed(1);
  const totalRevenue = sampleData.reduce((sum, item) => sum + item.revenue, 0);

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">Analytics Dashboard</h1>
            <p className="text-gray-600">
              Campaign performance metrics and data visualization
            </p>
          </div>
          <Button onClick={handleRefresh} variant="outline" disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Emails Sent</p>
                  <p className="text-2xl font-bold">{totalEmailsSent.toLocaleString()}</p>
                </div>
                <Activity className="h-8 w-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Avg Open Rate</p>
                  <p className="text-2xl font-bold text-green-600">{averageOpenRate}%</p>
                </div>
                <TrendingUp className="h-8 w-8 text-green-400" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Avg Click Rate</p>
                  <p className="text-2xl font-bold text-purple-600">{averageClickRate}%</p>
                </div>
                <BarChart3 className="h-8 w-8 text-purple-400" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Revenue</p>
                  <p className="text-2xl font-bold text-orange-600">
                    ${totalRevenue.toLocaleString()}
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-orange-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <Card>
            <CardHeader>
              <CardTitle>Campaign Performance</CardTitle>
              <CardDescription>Revenue by campaign</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {sampleData.map((item, index) => {
                  const maxRevenue = Math.max(...sampleData.map(d => d.revenue));
                  const percentage = (item.revenue / maxRevenue) * 100;

                  return (
                    <div key={index} className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span>{item.campaign_name}</span>
                        <span className="font-semibold">${item.revenue.toLocaleString()}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-6">
                        <div
                          className="bg-gradient-to-r from-blue-600 to-purple-600 h-6 rounded-full transition-all duration-500"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Engagement Metrics</CardTitle>
              <CardDescription>Open vs Click rates</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {sampleData.map((item, index) => (
                  <div key={index} className="border-b pb-3">
                    <div className="flex justify-between text-sm mb-2">
                      <span className="font-medium">{item.campaign_name}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Open: </span>
                        <span className="font-semibold text-green-600">{item.open_rate}%</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Click: </span>
                        <span className="font-semibold text-blue-600">{item.click_rate}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Data Table */}
        <DataTable
          title="Campaign Performance Data"
          description="Detailed metrics for all campaigns"
          columns={columns}
          data={sampleData}
          pageSize={10}
        />

        {/* Zoho Analytics Integration Info */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Zoho Analytics Integration</CardTitle>
          </CardHeader>
          <CardContent>
            <Alert>
              <AlertDescription>
                <div className="space-y-2">
                  <p>
                    <strong>Available Chart Types:</strong> Bar, Column, Line, Area, Pie, Donut,
                    Funnel, Pyramid, Scatter, Bubble, Heat Map, Sankey, and 65+ more chart types
                  </p>
                  <p>
                    <strong>Features:</strong> Real-time data synchronization, custom dashboards,
                    automated reports, data blending, and advanced analytics
                  </p>
                  <p className="text-sm text-gray-600">
                    Connect your Zoho account in the Zoho Connections page to enable
                    live data visualization from Zoho Analytics
                  </p>
                </div>
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
