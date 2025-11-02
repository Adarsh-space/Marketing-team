import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import {
  Search,
  MapPin,
  Globe,
  Linkedin,
  Download,
  RefreshCw,
  Mail,
  Phone,
  ExternalLink,
  Database
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export default function ScrapingDashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('google-maps');
  const [loading, setLoading] = useState(false);
  const [scrapedData, setScrapedData] = useState([]);

  // Google Maps scraping state
  const [googleMapsQuery, setGoogleMapsQuery] = useState('');
  const [googleMapsLocation, setGoogleMapsLocation] = useState('');
  const [googleMapsMaxResults, setGoogleMapsMaxResults] = useState(20);

  // Website scraping state
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [extractEmails, setExtractEmails] = useState(true);
  const [extractPhones, setExtractPhones] = useState(true);
  const [extractLinks, setExtractLinks] = useState(false);

  const tenantId = localStorage.getItem('tenant_id');
  const authToken = localStorage.getItem('auth_token');

  const handleGoogleMapsScrape = async (e) => {
    e.preventDefault();

    if (!googleMapsQuery || !googleMapsLocation) {
      toast.error('Please enter search query and location');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/scraping/google-maps`,
        {
          tenant_id: tenantId,
          query: googleMapsQuery,
          location: googleMapsLocation,
          max_results: googleMapsMaxResults
        },
        {
          headers: { Authorization: `Bearer ${authToken}` }
        }
      );

      if (response.data.status === 'success') {
        setScrapedData(response.data.data || []);
        toast.success(`Scraped ${response.data.count} businesses!`);
      } else {
        toast.error(response.data.message || 'Scraping failed');
      }
    } catch (error) {
      console.error('Google Maps scraping error:', error);
      toast.error(error.response?.data?.message || 'Scraping failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleWebsiteScrape = async (e) => {
    e.preventDefault();

    if (!websiteUrl) {
      toast.error('Please enter a website URL');
      return;
    }

    // Validate URL
    try {
      new URL(websiteUrl);
    } catch {
      toast.error('Please enter a valid URL');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/scraping/website`,
        {
          tenant_id: tenantId,
          url: websiteUrl,
          extract_emails: extractEmails,
          extract_phones: extractPhones,
          extract_links: extractLinks
        },
        {
          headers: { Authorization: `Bearer ${authToken}` }
        }
      );

      if (response.data.status === 'success') {
        setScrapedData([response.data.data]);
        toast.success('Website scraped successfully!');
      } else {
        toast.error(response.data.message || 'Scraping failed');
      }
    } catch (error) {
      console.error('Website scraping error:', error);
      toast.error(error.response?.data?.message || 'Scraping failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = () => {
    if (scrapedData.length === 0) {
      toast.error('No data to export');
      return;
    }

    // Create CSV content
    const headers = Object.keys(scrapedData[0]);
    const csvContent = [
      headers.join(','),
      ...scrapedData.map(row =>
        headers.map(header => JSON.stringify(row[header] || '')).join(',')
      )
    ].join('\n');

    // Download
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scraped-data-${Date.now()}.csv`;
    a.click();

    toast.success('Data exported to CSV!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 to-indigo-100 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Data Scraping</h1>
            <p className="text-gray-600 mt-1">Collect business data from multiple sources</p>
          </div>
          {scrapedData.length > 0 && (
            <Button onClick={exportToCSV}>
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
          )}
        </div>
      </div>

      {/* Scraping Interface */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Scraping Form */}
        <div>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="google-maps">
                <MapPin className="w-4 h-4 mr-2" />
                Google Maps
              </TabsTrigger>
              <TabsTrigger value="website">
                <Globe className="w-4 h-4 mr-2" />
                Website
              </TabsTrigger>
              <TabsTrigger value="linkedin" disabled>
                <Linkedin className="w-4 h-4 mr-2" />
                LinkedIn
              </TabsTrigger>
            </TabsList>

            {/* Google Maps Tab */}
            <TabsContent value="google-maps">
              <Card>
                <CardHeader>
                  <CardTitle>Google Maps Business Scraper</CardTitle>
                  <CardDescription>
                    Find businesses with contact information
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleGoogleMapsScrape} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="query">Search Query *</Label>
                      <Input
                        id="query"
                        placeholder="e.g., restaurants, plumbers, dentists"
                        value={googleMapsQuery}
                        onChange={(e) => setGoogleMapsQuery(e.target.value)}
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="location">Location *</Label>
                      <Input
                        id="location"
                        placeholder="e.g., New York, NY"
                        value={googleMapsLocation}
                        onChange={(e) => setGoogleMapsLocation(e.target.value)}
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="maxResults">Maximum Results</Label>
                      <Input
                        id="maxResults"
                        type="number"
                        min="1"
                        max="100"
                        value={googleMapsMaxResults}
                        onChange={(e) => setGoogleMapsMaxResults(parseInt(e.target.value))}
                      />
                      <p className="text-xs text-gray-500">
                        Cost: {(googleMapsMaxResults * 0.05).toFixed(2)} credits
                      </p>
                    </div>

                    <Button type="submit" className="w-full" disabled={loading}>
                      {loading ? (
                        <span className="flex items-center gap-2">
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          Scraping...
                        </span>
                      ) : (
                        <span className="flex items-center gap-2">
                          <Search className="w-4 h-4" />
                          Start Scraping
                        </span>
                      )}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Website Tab */}
            <TabsContent value="website">
              <Card>
                <CardHeader>
                  <CardTitle>Website Scraper</CardTitle>
                  <CardDescription>
                    Extract emails, phones, and links from any website
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleWebsiteScrape} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="url">Website URL *</Label>
                      <Input
                        id="url"
                        type="url"
                        placeholder="https://example.com"
                        value={websiteUrl}
                        onChange={(e) => setWebsiteUrl(e.target.value)}
                        required
                      />
                    </div>

                    <div className="space-y-3">
                      <Label>Extract:</Label>

                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          id="emails"
                          checked={extractEmails}
                          onChange={(e) => setExtractEmails(e.target.checked)}
                          className="w-4 h-4"
                        />
                        <Label htmlFor="emails" className="cursor-pointer">
                          Email addresses
                        </Label>
                      </div>

                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          id="phones"
                          checked={extractPhones}
                          onChange={(e) => setExtractPhones(e.target.checked)}
                          className="w-4 h-4"
                        />
                        <Label htmlFor="phones" className="cursor-pointer">
                          Phone numbers
                        </Label>
                      </div>

                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          id="links"
                          checked={extractLinks}
                          onChange={(e) => setExtractLinks(e.target.checked)}
                          className="w-4 h-4"
                        />
                        <Label htmlFor="links" className="cursor-pointer">
                          Links (up to 50)
                        </Label>
                      </div>
                    </div>

                    <p className="text-xs text-gray-500">
                      Cost: 0.03 credits per page
                    </p>

                    <Button type="submit" className="w-full" disabled={loading}>
                      {loading ? (
                        <span className="flex items-center gap-2">
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          Scraping...
                        </span>
                      ) : (
                        <span className="flex items-center gap-2">
                          <Search className="w-4 h-4" />
                          Start Scraping
                        </span>
                      )}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </TabsContent>

            {/* LinkedIn Tab (Disabled) */}
            <TabsContent value="linkedin">
              <Card>
                <CardHeader>
                  <CardTitle>LinkedIn Scraper</CardTitle>
                  <CardDescription>Coming soon...</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8 text-gray-500">
                    <Linkedin className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p>LinkedIn scraping requires LinkedIn API access</p>
                    <p className="text-sm mt-2">
                      Consider using PhantomBuster or Apify for LinkedIn data
                    </p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Right: Results */}
        <div>
          <Card className="h-full">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Scraped Results</CardTitle>
                  <CardDescription>
                    {scrapedData.length > 0
                      ? `${scrapedData.length} record(s) found`
                      : 'No data yet'}
                  </CardDescription>
                </div>
                {scrapedData.length > 0 && (
                  <Badge variant="outline">
                    <Database className="w-3 h-3 mr-1" />
                    {scrapedData.length}
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {scrapedData.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Search className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <p>No scraped data yet</p>
                  <p className="text-sm">Start scraping to see results here</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {scrapedData.map((item, index) => (
                    <Card key={index} className="p-4">
                      {/* Google Maps Result */}
                      {item.name && (
                        <div>
                          <h3 className="font-semibold text-lg">{item.name}</h3>
                          {item.address && (
                            <p className="text-sm text-gray-600 flex items-center gap-1 mt-1">
                              <MapPin className="w-3 h-3" />
                              {item.address}
                            </p>
                          )}
                          {item.phone && (
                            <p className="text-sm text-gray-600 flex items-center gap-1 mt-1">
                              <Phone className="w-3 h-3" />
                              {item.phone}
                            </p>
                          )}
                          {item.website && (
                            <a
                              href={item.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 flex items-center gap-1 mt-1 hover:underline"
                            >
                              <Globe className="w-3 h-3" />
                              {item.website}
                            </a>
                          )}
                          {item.rating && (
                            <p className="text-sm text-gray-600 mt-1">
                              ⭐ {item.rating} ({item.total_ratings} reviews)
                            </p>
                          )}
                        </div>
                      )}

                      {/* Website Result */}
                      {item.url && (
                        <div>
                          <h3 className="font-semibold text-lg">{item.title || 'Website Data'}</h3>
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 flex items-center gap-1 mt-1 hover:underline"
                          >
                            <ExternalLink className="w-3 h-3" />
                            {item.url}
                          </a>
                          {item.emails && item.emails.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs font-semibold text-gray-500">Emails:</p>
                              {item.emails.map((email, i) => (
                                <p key={i} className="text-sm text-gray-700 flex items-center gap-1">
                                  <Mail className="w-3 h-3" />
                                  {email}
                                </p>
                              ))}
                            </div>
                          )}
                          {item.phones && item.phones.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs font-semibold text-gray-500">Phones:</p>
                              {item.phones.map((phone, i) => (
                                <p key={i} className="text-sm text-gray-700 flex items-center gap-1">
                                  <Phone className="w-3 h-3" />
                                  {phone}
                                </p>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
