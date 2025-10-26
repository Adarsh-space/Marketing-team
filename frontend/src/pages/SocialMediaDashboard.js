import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "sonner";
import { Sparkles, Facebook, Instagram, Image as ImageIcon, Send, CheckCircle, AlertCircle, Clock } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000/api';

const SocialMediaDashboard = () => {
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [facebookPages, setFacebookPages] = useState([]);
  const [instagramAccounts, setInstagramAccounts] = useState([]);
  const [facebookConnected, setFacebookConnected] = useState(false);
  const [instagramConnected, setInstagramConnected] = useState(false);

  // Content generation state
  const [prompt, setPrompt] = useState('');
  const [generatedContent, setGeneratedContent] = useState(null);

  // Post configuration
  const [postConfig, setPostConfig] = useState({
    platform: 'facebook',
    selectedPage: '',
    selectedInstagram: '',
    imageUrl: '',
    autoPost: false
  });

  // Post history
  const [postHistory, setPostHistory] = useState([]);

  useEffect(() => {
    checkConnections();
  }, []);

  const checkConnections = async () => {
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
          setPostConfig(prev => ({ ...prev, selectedPage: data.pages[0].id }));
        }
      } else {
        setFacebookConnected(false);
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
          setPostConfig(prev => ({ ...prev, selectedInstagram: data.accounts[0].instagram_account_id }));
        }
      } else {
        setInstagramConnected(false);
      }
    } catch (error) {
      console.error('Error loading Instagram accounts:', error);
      setInstagramConnected(false);
    }
  };

  const handleGenerateContent = async () => {
    try {
      setGenerating(true);

      const response = await fetch(`${API_URL}/social-media/ai-post`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'default_user',
          prompt: prompt,
          platform: postConfig.platform,
          auto_post: false // Just generate, don't post yet
        })
      });

      const data = await response.json();

      if (data.status === 'success' && data.content) {
        setGeneratedContent(data.content);
        toast.success('Content generated successfully!');
      } else {
        toast.error(data.message || 'Failed to generate content');
      }
    } catch (error) {
      console.error('Error generating content:', error);
      toast.error('Failed to generate content');
    } finally {
      setGenerating(false);
    }
  };

  const handlePostToFacebook = async () => {
    try {
      setLoading(true);

      const response = await fetch(`${API_URL}/social-media/facebook/post`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'default_user',
          message: generatedContent.message || generatedContent,
          page_id: postConfig.selectedPage,
          image_url: postConfig.imageUrl || null
        })
      });

      const data = await response.json();

      if (data.status === 'success') {
        toast.success('Posted to Facebook successfully!');
        addToHistory('facebook', 'success', data.post_id);
        setGeneratedContent(null);
        setPrompt('');
        setPostConfig(prev => ({ ...prev, imageUrl: '' }));
      } else {
        toast.error(data.message || 'Failed to post to Facebook');
        addToHistory('facebook', 'failed', null);
      }
    } catch (error) {
      console.error('Error posting to Facebook:', error);
      toast.error('Failed to post to Facebook');
      addToHistory('facebook', 'failed', null);
    } finally {
      setLoading(false);
    }
  };

  const handlePostToInstagram = async () => {
    try {
      setLoading(true);

      if (!postConfig.imageUrl) {
        toast.error('Instagram posts require an image URL');
        return;
      }

      const response = await fetch(`${API_URL}/social-media/instagram/post`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'default_user',
          image_url: postConfig.imageUrl,
          caption: generatedContent.message || generatedContent,
          instagram_account_id: postConfig.selectedInstagram
        })
      });

      const data = await response.json();

      if (data.status === 'success') {
        toast.success('Posted to Instagram successfully!');
        addToHistory('instagram', 'success', data.post_id);
        setGeneratedContent(null);
        setPrompt('');
        setPostConfig(prev => ({ ...prev, imageUrl: '' }));
      } else {
        toast.error(data.message || 'Failed to post to Instagram');
        addToHistory('instagram', 'failed', null);
      }
    } catch (error) {
      console.error('Error posting to Instagram:', error);
      toast.error('Failed to post to Instagram');
      addToHistory('instagram', 'failed', null);
    } finally {
      setLoading(false);
    }
  };

  const addToHistory = (platform, status, postId) => {
    const historyItem = {
      id: Date.now(),
      platform,
      status,
      postId,
      content: generatedContent,
      timestamp: new Date().toISOString()
    };
    setPostHistory(prev => [historyItem, ...prev].slice(0, 10));
  };

  const renderContentPreview = () => {
    if (!generatedContent) return null;

    const content = typeof generatedContent === 'string'
      ? { message: generatedContent, hashtags: [] }
      : generatedContent;

    return (
      <Card className="mt-4 border-2 border-purple-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-600" />
            Generated Content Preview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <p className="whitespace-pre-wrap">{content.message}</p>
            </div>
            {content.hashtags && content.hashtags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {content.hashtags.map((tag, index) => (
                  <Badge key={index} variant="secondary">
                    #{tag}
                  </Badge>
                ))}
              </div>
            )}
            {postConfig.imageUrl && (
              <div>
                <img
                  src={postConfig.imageUrl}
                  alt="Post preview"
                  className="max-w-md rounded-lg border"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    toast.error('Failed to load image');
                  }}
                />
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  const canPost = (platform) => {
    if (platform === 'facebook') {
      return facebookConnected && postConfig.selectedPage && generatedContent;
    } else if (platform === 'instagram') {
      return instagramConnected && postConfig.selectedInstagram && generatedContent && postConfig.imageUrl;
    }
    return false;
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Social Media Dashboard</h1>
        <p className="text-gray-600 mb-6">
          Generate AI-powered content and post to Facebook and Instagram
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content Area */}
          <div className="lg:col-span-2 space-y-6">
            {/* Connection Status */}
            <Card>
              <CardHeader>
                <CardTitle>Connection Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex gap-4">
                  <div className="flex items-center gap-2">
                    <Facebook className="h-5 w-5 text-blue-600" />
                    {facebookConnected ? (
                      <Badge variant="success" className="flex items-center gap-1">
                        <CheckCircle className="h-3 w-3" />
                        Connected
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" />
                        Not Connected
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Instagram className="h-5 w-5 text-pink-600" />
                    {instagramConnected ? (
                      <Badge variant="success" className="flex items-center gap-1">
                        <CheckCircle className="h-3 w-3" />
                        Connected
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" />
                        Not Connected
                      </Badge>
                    )}
                  </div>
                </div>
                {(!facebookConnected && !instagramConnected) && (
                  <Alert className="mt-4">
                    <AlertDescription>
                      Please connect your social media accounts in the Social Media Credentials page first.
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>

            {/* Content Generator */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-purple-600" />
                  AI Content Generator
                </CardTitle>
                <CardDescription>
                  Describe what you want to post, and AI will generate the content
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid gap-2">
                    <Label htmlFor="prompt">What would you like to post about?</Label>
                    <Textarea
                      id="prompt"
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      placeholder="e.g., 'Create an engaging post about our new summer product launch with a professional tone'"
                      rows={4}
                    />
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="platform">Target Platform</Label>
                    <Select
                      value={postConfig.platform}
                      onValueChange={(value) => setPostConfig({ ...postConfig, platform: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="facebook">
                          <div className="flex items-center gap-2">
                            <Facebook className="h-4 w-4" />
                            Facebook
                          </div>
                        </SelectItem>
                        <SelectItem value="instagram">
                          <div className="flex items-center gap-2">
                            <Instagram className="h-4 w-4" />
                            Instagram
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Button
                    onClick={handleGenerateContent}
                    disabled={generating || !prompt}
                    className="w-full bg-purple-600 hover:bg-purple-700"
                  >
                    <Sparkles className="mr-2 h-4 w-4" />
                    {generating ? 'Generating...' : 'Generate Content with AI'}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Content Preview */}
            {renderContentPreview()}

            {/* Post Configuration */}
            {generatedContent && (
              <Card>
                <CardHeader>
                  <CardTitle>Post Configuration</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {postConfig.platform === 'facebook' && facebookPages.length > 0 && (
                      <div className="grid gap-2">
                        <Label htmlFor="fb-page">Facebook Page</Label>
                        <Select
                          value={postConfig.selectedPage}
                          onValueChange={(value) => setPostConfig({ ...postConfig, selectedPage: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {facebookPages.map((page) => (
                              <SelectItem key={page.id} value={page.id}>
                                {page.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}

                    {postConfig.platform === 'instagram' && instagramAccounts.length > 0 && (
                      <div className="grid gap-2">
                        <Label htmlFor="ig-account">Instagram Account</Label>
                        <Select
                          value={postConfig.selectedInstagram}
                          onValueChange={(value) => setPostConfig({ ...postConfig, selectedInstagram: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {instagramAccounts.map((account) => (
                              <SelectItem key={account.instagram_account_id} value={account.instagram_account_id}>
                                {account.page_name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}

                    <div className="grid gap-2">
                      <Label htmlFor="image-url">Image URL (optional for Facebook, required for Instagram)</Label>
                      <Input
                        id="image-url"
                        type="url"
                        value={postConfig.imageUrl}
                        onChange={(e) => setPostConfig({ ...postConfig, imageUrl: e.target.value })}
                        placeholder="https://example.com/image.jpg"
                      />
                      <p className="text-xs text-gray-500">
                        Must be a publicly accessible URL
                      </p>
                    </div>

                    {postConfig.platform === 'instagram' && !postConfig.imageUrl && (
                      <Alert variant="warning">
                        <AlertDescription>
                          Instagram requires an image URL to post
                        </AlertDescription>
                      </Alert>
                    )}

                    <div className="flex gap-2">
                      {postConfig.platform === 'facebook' && (
                        <Button
                          onClick={handlePostToFacebook}
                          disabled={loading || !canPost('facebook')}
                          className="flex-1 bg-blue-600 hover:bg-blue-700"
                        >
                          <Send className="mr-2 h-4 w-4" />
                          Post to Facebook
                        </Button>
                      )}
                      {postConfig.platform === 'instagram' && (
                        <Button
                          onClick={handlePostToInstagram}
                          disabled={loading || !canPost('instagram')}
                          className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                        >
                          <Send className="mr-2 h-4 w-4" />
                          Post to Instagram
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar - Post History */}
          <div className="lg:col-span-1">
            <Card className="sticky top-4">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Recent Posts
                </CardTitle>
                <CardDescription>
                  Your posting history
                </CardDescription>
              </CardHeader>
              <CardContent>
                {postHistory.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-4">
                    No posts yet
                  </p>
                ) : (
                  <div className="space-y-3">
                    {postHistory.map((item) => (
                      <div key={item.id} className="border rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          {item.platform === 'facebook' ? (
                            <Facebook className="h-4 w-4 text-blue-600" />
                          ) : (
                            <Instagram className="h-4 w-4 text-pink-600" />
                          )}
                          {item.status === 'success' ? (
                            <Badge variant="success" className="text-xs">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Posted
                            </Badge>
                          ) : (
                            <Badge variant="destructive" className="text-xs">
                              <AlertCircle className="h-3 w-3 mr-1" />
                              Failed
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-gray-600 line-clamp-2">
                          {typeof item.content === 'string'
                            ? item.content
                            : item.content?.message || 'No content'}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          {new Date(item.timestamp).toLocaleString()}
                        </p>
                        {item.postId && (
                          <p className="text-xs text-gray-500 mt-1">
                            Post ID: {item.postId}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SocialMediaDashboard;
