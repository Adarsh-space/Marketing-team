import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "sonner";
import { Mail, Send, Users, TrendingUp, BarChart, Clock, CheckCircle } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000/api';

const EmailDashboard = () => {
  const [loading, setLoading] = useState(false);
  const [mailingLists, setMailingLists] = useState([]);
  const [emailCampaigns, setEmailCampaigns] = useState([]);
  const [campaignStats, setCampaignStats] = useState({});

  // Single email state
  const [singleEmail, setSingleEmail] = useState({
    to: '',
    subject: '',
    body: '',
    schedule_time: ''
  });

  // Bulk email state
  const [bulkEmail, setBulkEmail] = useState({
    recipients: '',
    subject: '',
    body: '',
    personalization: {}
  });

  // Email campaign state
  const [emailCampaign, setEmailCampaign] = useState({
    campaign_name: '',
    mailing_list_key: '',
    subject: '',
    html_content: '',
    from_email: '',
    reply_to: ''
  });

  // New mailing list state
  const [newList, setNewList] = useState({
    list_name: '',
    list_description: ''
  });

  useEffect(() => {
    loadMailingLists();
    loadEmailCampaigns();
  }, []);

  const loadMailingLists = async () => {
    try {
      const response = await fetch(`${API_URL}/zoho/campaigns/mailing-lists?user_id=default_user`);
      const data = await response.json();

      if (data.status === 'success' && data.lists) {
        setMailingLists(data.lists);
      }
    } catch (error) {
      console.error('Error loading mailing lists:', error);
    }
  };

  const loadEmailCampaigns = async () => {
    try {
      const response = await fetch(`${API_URL}/zoho/campaigns?user_id=default_user`);
      const data = await response.json();

      if (data.status === 'success' && data.campaigns) {
        setEmailCampaigns(data.campaigns);
      }
    } catch (error) {
      console.error('Error loading email campaigns:', error);
    }
  };

  const handleSendSingleEmail = async () => {
    try {
      setLoading(true);

      const response = await fetch(`${API_URL}/zoho/mail/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'default_user',
          to: singleEmail.to.split(',').map(e => e.trim()),
          subject: singleEmail.subject,
          body: singleEmail.body,
          schedule_time: singleEmail.schedule_time || null
        })
      });

      const data = await response.json();

      if (data.status === 'success') {
        toast.success(singleEmail.schedule_time ? 'Email scheduled successfully!' : 'Email sent successfully!');
        setSingleEmail({ to: '', subject: '', body: '', schedule_time: '' });
      } else {
        toast.error(data.message || 'Failed to send email');
      }
    } catch (error) {
      console.error('Error sending email:', error);
      toast.error('Failed to send email');
    } finally {
      setLoading(false);
    }
  };

  const handleSendBulkEmail = async () => {
    try {
      setLoading(true);

      const recipientList = bulkEmail.recipients.split('\n')
        .map(line => line.trim())
        .filter(line => line.includes(','));

      const recipients = recipientList.map(line => {
        const [email, ...nameParts] = line.split(',');
        return {
          email: email.trim(),
          name: nameParts.join(',').trim() || email.trim()
        };
      });

      const response = await fetch(`${API_URL}/zoho/mail/send-bulk`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'default_user',
          recipients: recipients,
          subject: bulkEmail.subject,
          body_template: bulkEmail.body,
          personalization: bulkEmail.personalization
        })
      });

      const data = await response.json();

      if (data.status === 'success') {
        toast.success(`Bulk email sent to ${recipients.length} recipients!`);
        setBulkEmail({ recipients: '', subject: '', body: '', personalization: {} });
      } else {
        toast.error(data.message || 'Failed to send bulk email');
      }
    } catch (error) {
      console.error('Error sending bulk email:', error);
      toast.error('Failed to send bulk email');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateMailingList = async () => {
    try {
      setLoading(true);

      const response = await fetch(`${API_URL}/zoho/campaigns/mailing-lists`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'default_user',
          list_name: newList.list_name,
          list_description: newList.list_description
        })
      });

      const data = await response.json();

      if (data.status === 'success') {
        toast.success('Mailing list created successfully!');
        setNewList({ list_name: '', list_description: '' });
        loadMailingLists();
      } else {
        toast.error(data.message || 'Failed to create mailing list');
      }
    } catch (error) {
      console.error('Error creating mailing list:', error);
      toast.error('Failed to create mailing list');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateEmailCampaign = async () => {
    try {
      setLoading(true);

      const response = await fetch(`${API_URL}/zoho/campaigns/email-campaign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'default_user',
          campaign_name: emailCampaign.campaign_name,
          mailing_list_key: emailCampaign.mailing_list_key,
          subject: emailCampaign.subject,
          html_content: emailCampaign.html_content,
          from_email: emailCampaign.from_email,
          reply_to: emailCampaign.reply_to
        })
      });

      const data = await response.json();

      if (data.status === 'success') {
        toast.success('Email campaign created successfully!');
        setEmailCampaign({
          campaign_name: '',
          mailing_list_key: '',
          subject: '',
          html_content: '',
          from_email: '',
          reply_to: ''
        });
        loadEmailCampaigns();
      } else {
        toast.error(data.message || 'Failed to create email campaign');
      }
    } catch (error) {
      console.error('Error creating email campaign:', error);
      toast.error('Failed to create email campaign');
    } finally {
      setLoading(false);
    }
  };

  const loadCampaignStats = async (campaignKey) => {
    try {
      const response = await fetch(`${API_URL}/zoho/campaigns/${campaignKey}/stats?user_id=default_user`);
      const data = await response.json();

      if (data.status === 'success' && data.statistics) {
        setCampaignStats(prev => ({ ...prev, [campaignKey]: data.statistics }));
      }
    } catch (error) {
      console.error('Error loading campaign stats:', error);
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Email Marketing Dashboard</h1>
        <p className="text-gray-600 mb-6">
          Send emails, manage campaigns, and track performance
        </p>

        <Tabs defaultValue="single" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="single">Single Email</TabsTrigger>
            <TabsTrigger value="bulk">Bulk Email</TabsTrigger>
            <TabsTrigger value="campaign">Email Campaigns</TabsTrigger>
            <TabsTrigger value="lists">Mailing Lists</TabsTrigger>
          </TabsList>

          {/* Single Email Tab */}
          <TabsContent value="single">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5" />
                  Send Single Email
                </CardTitle>
                <CardDescription>
                  Send individual emails via Zoho Mail
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid gap-2">
                    <Label htmlFor="to">To (comma-separated for multiple recipients)</Label>
                    <Input
                      id="to"
                      type="email"
                      value={singleEmail.to}
                      onChange={(e) => setSingleEmail({ ...singleEmail, to: e.target.value })}
                      placeholder="email@example.com, another@example.com"
                    />
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="subject">Subject</Label>
                    <Input
                      id="subject"
                      value={singleEmail.subject}
                      onChange={(e) => setSingleEmail({ ...singleEmail, subject: e.target.value })}
                      placeholder="Email subject"
                    />
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="body">Message</Label>
                    <Textarea
                      id="body"
                      value={singleEmail.body}
                      onChange={(e) => setSingleEmail({ ...singleEmail, body: e.target.value })}
                      placeholder="Email content..."
                      rows={8}
                    />
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="schedule">Schedule (optional)</Label>
                    <Input
                      id="schedule"
                      type="datetime-local"
                      value={singleEmail.schedule_time}
                      onChange={(e) => setSingleEmail({ ...singleEmail, schedule_time: e.target.value })}
                    />
                    <p className="text-xs text-gray-500">
                      Leave empty to send immediately
                    </p>
                  </div>

                  <Button
                    onClick={handleSendSingleEmail}
                    disabled={loading || !singleEmail.to || !singleEmail.subject || !singleEmail.body}
                    className="w-full"
                  >
                    <Send className="mr-2 h-4 w-4" />
                    {singleEmail.schedule_time ? 'Schedule Email' : 'Send Email'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Bulk Email Tab */}
          <TabsContent value="bulk">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Send Bulk Email
                </CardTitle>
                <CardDescription>
                  Send personalized emails to multiple recipients
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Alert>
                    <AlertDescription>
                      <strong>Format:</strong> Enter one recipient per line in format: email@example.com, Name
                      <br />
                      Example: john@example.com, John Doe
                    </AlertDescription>
                  </Alert>

                  <div className="grid gap-2">
                    <Label htmlFor="recipients">Recipients List</Label>
                    <Textarea
                      id="recipients"
                      value={bulkEmail.recipients}
                      onChange={(e) => setBulkEmail({ ...bulkEmail, recipients: e.target.value })}
                      placeholder="email@example.com, Name&#10;another@example.com, Another Name&#10;..."
                      rows={6}
                    />
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="bulk-subject">Subject</Label>
                    <Input
                      id="bulk-subject"
                      value={bulkEmail.subject}
                      onChange={(e) => setBulkEmail({ ...bulkEmail, subject: e.target.value })}
                      placeholder="Email subject"
                    />
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="bulk-body">Message Template</Label>
                    <Textarea
                      id="bulk-body"
                      value={bulkEmail.body}
                      onChange={(e) => setBulkEmail({ ...bulkEmail, body: e.target.value })}
                      placeholder="Hi {name}, &#10;&#10;Your personalized message here..."
                      rows={8}
                    />
                    <p className="text-xs text-gray-500">
                      Use {'{name}'} for personalization
                    </p>
                  </div>

                  <Button
                    onClick={handleSendBulkEmail}
                    disabled={loading || !bulkEmail.recipients || !bulkEmail.subject || !bulkEmail.body}
                    className="w-full"
                  >
                    <Send className="mr-2 h-4 w-4" />
                    Send to All Recipients
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Email Campaigns Tab */}
          <TabsContent value="campaign">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    Create Email Campaign
                  </CardTitle>
                  <CardDescription>
                    Create and manage email marketing campaigns via Zoho Campaigns
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid gap-2">
                      <Label htmlFor="campaign-name">Campaign Name</Label>
                      <Input
                        id="campaign-name"
                        value={emailCampaign.campaign_name}
                        onChange={(e) => setEmailCampaign({ ...emailCampaign, campaign_name: e.target.value })}
                        placeholder="Summer Sale 2025"
                      />
                    </div>

                    <div className="grid gap-2">
                      <Label htmlFor="mailing-list">Mailing List</Label>
                      <select
                        id="mailing-list"
                        className="w-full px-3 py-2 border rounded-md"
                        value={emailCampaign.mailing_list_key}
                        onChange={(e) => setEmailCampaign({ ...emailCampaign, mailing_list_key: e.target.value })}
                      >
                        <option value="">Select a mailing list</option>
                        {mailingLists.map((list) => (
                          <option key={list.listkey} value={list.listkey}>
                            {list.listname} ({list.contact_count} contacts)
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="grid gap-2">
                        <Label htmlFor="from-email">From Email</Label>
                        <Input
                          id="from-email"
                          type="email"
                          value={emailCampaign.from_email}
                          onChange={(e) => setEmailCampaign({ ...emailCampaign, from_email: e.target.value })}
                          placeholder="sender@yourdomain.com"
                        />
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="reply-to">Reply To</Label>
                        <Input
                          id="reply-to"
                          type="email"
                          value={emailCampaign.reply_to}
                          onChange={(e) => setEmailCampaign({ ...emailCampaign, reply_to: e.target.value })}
                          placeholder="reply@yourdomain.com"
                        />
                      </div>
                    </div>

                    <div className="grid gap-2">
                      <Label htmlFor="campaign-subject">Subject</Label>
                      <Input
                        id="campaign-subject"
                        value={emailCampaign.subject}
                        onChange={(e) => setEmailCampaign({ ...emailCampaign, subject: e.target.value })}
                        placeholder="Don't miss our summer sale!"
                      />
                    </div>

                    <div className="grid gap-2">
                      <Label htmlFor="html-content">Email Content (HTML)</Label>
                      <Textarea
                        id="html-content"
                        value={emailCampaign.html_content}
                        onChange={(e) => setEmailCampaign({ ...emailCampaign, html_content: e.target.value })}
                        placeholder="<h1>Welcome!</h1><p>Your HTML email content...</p>"
                        rows={10}
                      />
                    </div>

                    <Button
                      onClick={handleCreateEmailCampaign}
                      disabled={loading || !emailCampaign.campaign_name || !emailCampaign.mailing_list_key}
                      className="w-full"
                    >
                      Create Campaign
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Campaign Statistics */}
              {emailCampaigns.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart className="h-5 w-5" />
                      Campaign Performance
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {emailCampaigns.slice(0, 5).map((campaign) => (
                        <div key={campaign.campaign_key} className="border rounded-lg p-4">
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-semibold">{campaign.campaign_name}</h4>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => loadCampaignStats(campaign.campaign_key)}
                            >
                              Load Stats
                            </Button>
                          </div>
                          {campaignStats[campaign.campaign_key] && (
                            <div className="grid grid-cols-4 gap-4 mt-4 text-sm">
                              <div>
                                <p className="text-gray-500">Sent</p>
                                <p className="font-bold">{campaignStats[campaign.campaign_key].sent_count}</p>
                              </div>
                              <div>
                                <p className="text-gray-500">Opened</p>
                                <p className="font-bold text-green-600">
                                  {campaignStats[campaign.campaign_key].open_rate}%
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-500">Clicked</p>
                                <p className="font-bold text-blue-600">
                                  {campaignStats[campaign.campaign_key].click_rate}%
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-500">Bounced</p>
                                <p className="font-bold text-red-600">
                                  {campaignStats[campaign.campaign_key].bounce_rate}%
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          {/* Mailing Lists Tab */}
          <TabsContent value="lists">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Create Mailing List</CardTitle>
                  <CardDescription>
                    Organize your contacts into mailing lists
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid gap-2">
                      <Label htmlFor="list-name">List Name</Label>
                      <Input
                        id="list-name"
                        value={newList.list_name}
                        onChange={(e) => setNewList({ ...newList, list_name: e.target.value })}
                        placeholder="Newsletter Subscribers"
                      />
                    </div>

                    <div className="grid gap-2">
                      <Label htmlFor="list-description">Description</Label>
                      <Textarea
                        id="list-description"
                        value={newList.list_description}
                        onChange={(e) => setNewList({ ...newList, list_description: e.target.value })}
                        placeholder="Description of this mailing list..."
                        rows={3}
                      />
                    </div>

                    <Button
                      onClick={handleCreateMailingList}
                      disabled={loading || !newList.list_name}
                      className="w-full"
                    >
                      Create Mailing List
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Your Mailing Lists</CardTitle>
                  <CardDescription>
                    {mailingLists.length} list(s) available
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {mailingLists.length === 0 ? (
                    <Alert>
                      <AlertDescription>
                        No mailing lists found. Create your first mailing list above!
                      </AlertDescription>
                    </Alert>
                  ) : (
                    <div className="space-y-3">
                      {mailingLists.map((list) => (
                        <div key={list.listkey} className="border rounded-lg p-4 flex justify-between items-center">
                          <div>
                            <h4 className="font-semibold">{list.listname}</h4>
                            <p className="text-sm text-gray-600">{list.list_description}</p>
                            <p className="text-xs text-gray-500 mt-1">
                              {list.contact_count || 0} contacts
                            </p>
                          </div>
                          <Badge variant="outline">
                            {list.listkey}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default EmailDashboard;
