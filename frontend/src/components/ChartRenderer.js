import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2 } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000/api';

const ChartRenderer = ({ chartId, title, description, userId = 'default_user' }) => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (chartId) {
      loadChartData();
    }
  }, [chartId]);

  const loadChartData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_URL}/zoho/analytics/chart/${chartId}/data?user_id=${userId}`
      );
      const data = await response.json();

      if (data.status === 'success' && data.chart_data) {
        setChartData(data.chart_data);
      } else {
        setError(data.message || 'Failed to load chart data');
      }
    } catch (err) {
      console.error('Error loading chart:', err);
      setError('Failed to load chart data');
    } finally {
      setLoading(false);
    }
  };

  const renderChart = () => {
    if (!chartData) return null;

    // Simple bar chart rendering using HTML/CSS
    // For production, you'd use a library like recharts or chart.js
    const { labels, values, chart_type } = chartData;

    if (chart_type === 'bar' || chart_type === 'column') {
      const maxValue = Math.max(...values);

      return (
        <div className="space-y-3">
          {labels.map((label, index) => {
            const percentage = (values[index] / maxValue) * 100;
            return (
              <div key={index} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>{label}</span>
                  <span className="font-semibold">{values[index]}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-6">
                  <div
                    className="bg-blue-600 h-6 rounded-full transition-all duration-500"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      );
    }

    if (chart_type === 'pie' || chart_type === 'donut') {
      const total = values.reduce((sum, val) => sum + val, 0);

      return (
        <div className="space-y-2">
          {labels.map((label, index) => {
            const percentage = ((values[index] / total) * 100).toFixed(1);
            return (
              <div key={index} className="flex items-center justify-between p-2 border rounded">
                <div className="flex items-center gap-2">
                  <div
                    className="w-4 h-4 rounded"
                    style={{
                      backgroundColor: `hsl(${(index * 360) / labels.length}, 70%, 50%)`
                    }}
                  />
                  <span className="text-sm">{label}</span>
                </div>
                <div className="text-sm">
                  <span className="font-semibold">{values[index]}</span>
                  <span className="text-gray-500 ml-2">({percentage}%)</span>
                </div>
              </div>
            );
          })}
        </div>
      );
    }

    if (chart_type === 'line') {
      return (
        <div className="space-y-3">
          <div className="text-sm text-gray-500">Line Chart Data</div>
          {labels.map((label, index) => (
            <div key={index} className="flex justify-between text-sm border-b pb-2">
              <span>{label}</span>
              <span className="font-semibold">{values[index]}</span>
            </div>
          ))}
        </div>
      );
    }

    // Default table view for unsupported chart types
    return (
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left p-2">Label</th>
              <th className="text-right p-2">Value</th>
            </tr>
          </thead>
          <tbody>
            {labels.map((label, index) => (
              <tr key={index} className="border-b">
                <td className="p-2">{label}</td>
                <td className="text-right p-2 font-semibold">{values[index]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <Card>
      <CardHeader>
        {title && <CardTitle>{title}</CardTitle>}
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : error ? (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : (
          renderChart()
        )}
      </CardContent>
    </Card>
  );
};

export default ChartRenderer;
