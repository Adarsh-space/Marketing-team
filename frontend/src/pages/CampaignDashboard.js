import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "sonner";
import { Plus, TrendingUp, Users, Target, Calendar, BarChart3, RefreshCw } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000/api';

const CampaignDashboard = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    completed: 0,
    planning: 0
  });

  // New campaign form state
  const [newCampaign, setNewCampaign] = useState({
    name: '',
    description: '',
    status: 'Planning',
    start_date: '',
    end_date: '',
    budget: '',
    target_audience: '',
    channel: 'email'
  });

  useEffect(() => {
    loadCampaigns();
  }, []);

  const loadCampaigns = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/zoho/campaigns?user_id=default_user`);
      const data = await response.json();

      if (data.status === 'success' && data.campaigns) {
        setCampaigns(data.campaigns);
        calculateStats(data.campaigns);
      }
    } catch (error) {
      console.error('Error loading campaigns:', error);
      toast.error('Failed to load campaigns');
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (campaignsList) => {
    const stats = {
      total: campaignsList.length,
      active: campaignsList.filter(c => c.Status === 'Active').length,
      completed: campaignsList.filter(c => c.Status === 'Completed').length,
      planning: campaignsList.filter(c => c.Status === 'Planning').length
    };
    setStats(stats);
  };

  const handleCreateCampaign = async () => {
    try {
      setLoading(true);

      const response = await fetch(`${API_URL}/zoho/campaigns/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'default_user',
          campaign_data: {
            name: newCampaign.name,
            description: newCampaign.description,
            status: newCampaign.status,
            start_date: newCampaign.start_date,
            end_date: newCampaign.end_date,
            budget: parseFloat(newCampaign.budget) || 0,
            target_audience: newCampaign.target_audience,
            channel: newCampaign.channel
          }
        })
      });

      const data = await response.json();

      if (data.status === 'success') {
        toast.success('Campaign created successfully!');
        setIsCreateDialogOpen(false);
        setNewCampaign({
          name: '',
          description: '',
          status: 'Planning',
          start_date: '',
          end_date: '',
          budget: '',
          target_audience: '',
          channel: 'email'
        });
        loadCampaigns();
      } else {
        toast.error(data.message || 'Failed to create campaign');
      }
    } catch (error) {
      console.error('Error creating campaign:', error);
      toast.error('Failed to create campaign');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Active':
        return 'bg-green-100 text-green-800';
      case 'Completed':
        return 'bg-blue-100 text-blue-800';
      case 'Planning':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">Campaign Dashboard</h1>
            <p className="text-gray-600">
              Manage and track your marketing campaigns
            </p>
          </div>
          <div className="flex gap-2">
            <Button onClick={loadCampaigns} variant="outline" disabled={loading}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  New Campaign
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Create New Campaign</DialogTitle>
                  <DialogDescription>
                    Fill in the details to create a new marketing campaign
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="name">Campaign Name</Label>
                    <Input
                      id="name"
                      value={newCampaign.name}
                      onChange={(e) => setNewCampaign({ ...newCampaign, name: e.target.value })}
                      placeholder="Summer Sale 2025"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      value={newCampaign.description}
                      onChange={(e) => setNewCampaign({ ...newCampaign, description: e.target.value })}
                      placeholder="Campaign description and goals..."
                      rows={3}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="grid gap-2">
                      <Label htmlFor="status">Status</Label>
                      <Select
                        value={newCampaign.status}
                        onValueChange={(value) => setNewCampaign({ ...newCampaign, status: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Planning">Planning</SelectItem>
                          <SelectItem value="Active">Active</SelectItem>
                          <SelectItem value="Completed">Completed</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="channel">Channel</Label>
                      <Select
                        value={newCampaign.channel}
                        onValueChange={(value) => setNewCampaign({ ...newCampaign, channel: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="email">Email</SelectItem>
                          <SelectItem value="social">Social Media</SelectItem>
                          <SelectItem value="both">Both</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="grid gap-2">
                      <Label htmlFor="start_date">Start Date</Label>
                      <Input
                        id="start_date"
                        type="date"
                        value={newCampaign.start_date}
                        onChange={(e) => setNewCampaign({ ...newCampaign, start_date: e.target.value })}
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="end_date">End Date</Label>
                      <Input
                        id="end_date"
                        type="date"
                        value={newCampaign.end_date}
                        onChange={(e) => setNewCampaign({ ...newCampaign, end_date: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="budget">Budget</Label>
                    <Input
                      id="budget"
                      type="number"
                      value={newCampaign.budget}
                      onChange={(e) => setNewCampaign({ ...newCampaign, budget: e.target.value })}
                      placeholder="0.00"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="target_audience">Target Audience</Label>
                    <Input
                      id="target_audience"
                      value={newCampaign.target_audience}
                      onChange={(e) => setNewCampaign({ ...newCampaign, target_audience: e.target.value })}
                      placeholder="e.g., Young professionals, age 25-35"
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateCampaign} disabled={loading || !newCampaign.name}>
                    {loading ? 'Creating...' : 'Create Campaign'}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Campaigns</p>
                  <p className="text-2xl font-bold">{stats.total}</p>
                </div>
                <BarChart3 className="h-8 w-8 text-gray-400" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Active</p>
                  <p className="text-2xl font-bold text-green-600">{stats.active}</p>
                </div>
                <TrendingUp className="h-8 w-8 text-green-400" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Planning</p>
                  <p className="text-2xl font-bold text-yellow-600">{stats.planning}</p>
                </div>
                <Target className="h-8 w-8 text-yellow-400" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Completed</p>
                  <p className="text-2xl font-bold text-blue-600">{stats.completed}</p>
                </div>
                <Users className="h-8 w-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Campaigns List */}
        <Card>
          <CardHeader>
            <CardTitle>All Campaigns</CardTitle>
            <CardDescription>
              View and manage all your marketing campaigns
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading && campaigns.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                Loading campaigns...
              </div>
            ) : campaigns.length === 0 ? (
              <Alert>
                <AlertDescription>
                  No campaigns found. Create your first campaign to get started!
                </AlertDescription>
              </Alert>
            ) : (
              <div className="space-y-4">
                {campaigns.map((campaign) => (
                  <Card key={campaign.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="pt-6">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="text-lg font-semibold">
                              {campaign.Campaign_Name || 'Untitled Campaign'}
                            </h3>
                            <Badge className={getStatusColor(campaign.Status)}>
                              {campaign.Status}
                            </Badge>
                            {campaign.AI_Generated && (
                              <Badge variant="outline" className="text-purple-600">
                                AI Generated
                              </Badge>
                            )}
                          </div>
                          <p className="text-gray-600 mb-3">
                            {campaign.Description || 'No description available'}
                          </p>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <p className="text-gray-500">Start Date</p>
                              <p className="font-medium">{formatDate(campaign.Start_Date)}</p>
                            </div>
                            <div>
                              <p className="text-gray-500">End Date</p>
                              <p className="font-medium">{formatDate(campaign.End_Date)}</p>
                            </div>
                            <div>
                              <p className="text-gray-500">Budget</p>
                              <p className="font-medium">
                                {campaign.Budget ? `$${campaign.Budget.toLocaleString()}` : 'N/A'}
                              </p>
                            </div>
                            <div>
                              <p className="text-gray-500">Channel</p>
                              <p className="font-medium capitalize">
                                {campaign.Channel || 'N/A'}
                              </p>
                            </div>
                          </div>
                          {campaign.Target_Audience && (
                            <div className="mt-3">
                              <p className="text-sm text-gray-500">Target Audience</p>
                              <p className="text-sm">{campaign.Target_Audience}</p>
                            </div>
                          )}
                        </div>
                        <div className="ml-4">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setSelectedCampaign(campaign)}
                          >
                            View Details
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Campaign Details Modal */}
        {selectedCampaign && (
          <Dialog open={!!selectedCampaign} onOpenChange={() => setSelectedCampaign(null)}>
            <DialogContent className="max-w-3xl">
              <DialogHeader>
                <DialogTitle>{selectedCampaign.Campaign_Name}</DialogTitle>
                <DialogDescription>Campaign Details and Analytics</DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Description</h4>
                  <p className="text-gray-600">{selectedCampaign.Description || 'No description'}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-semibold mb-2">Campaign Info</h4>
                    <dl className="space-y-2 text-sm">
                      <div>
                        <dt className="text-gray-500">Status</dt>
                        <dd><Badge className={getStatusColor(selectedCampaign.Status)}>{selectedCampaign.Status}</Badge></dd>
                      </div>
                      <div>
                        <dt className="text-gray-500">Start Date</dt>
                        <dd>{formatDate(selectedCampaign.Start_Date)}</dd>
                      </div>
                      <div>
                        <dt className="text-gray-500">End Date</dt>
                        <dd>{formatDate(selectedCampaign.End_Date)}</dd>
                      </div>
                      <div>
                        <dt className="text-gray-500">Budget</dt>
                        <dd>{selectedCampaign.Budget ? `$${selectedCampaign.Budget.toLocaleString()}` : 'N/A'}</dd>
                      </div>
                    </dl>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Performance Metrics</h4>
                    <Alert>
                      <AlertDescription>
                        Campaign analytics will be available once the campaign is active and has data.
                      </AlertDescription>
                    </Alert>
                  </div>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>
    </div>
  );
};

export default CampaignDashboard;
