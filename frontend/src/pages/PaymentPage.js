import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import {
  CreditCard,
  Check,
  Sparkles,
  Zap,
  Rocket,
  ArrowLeft,
  Coins
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export default function PaymentPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [packages, setPackages] = useState([]);
  const [currentBalance, setCurrentBalance] = useState(0);

  const tenantId = localStorage.getItem('tenant_id');
  const authToken = localStorage.getItem('auth_token');

  useEffect(() => {
    loadPackages();
    loadCurrentBalance();
  }, []);

  const loadPackages = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/payment/packages`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      if (response.data.status === 'success') {
        setPackages(response.data.packages || []);
      }
    } catch (error) {
      console.error('Error loading packages:', error);
    }
  };

  const loadCurrentBalance = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/credits/balance`, {
        headers: { Authorization: `Bearer ${authToken}` },
        params: { tenant_id: tenantId }
      });

      if (response.data.status === 'success') {
        setCurrentBalance(response.data.credits_balance || 0);
      }
    } catch (error) {
      console.error('Error loading balance:', error);
    }
  };

  const handleBuyCredits = async (packageName) => {
    if (!authToken) {
      navigate('/login');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/payment/checkout`,
        {
          tenant_id: tenantId,
          package_name: packageName,
          success_url: `${window.location.origin}/payment-success`,
          cancel_url: `${window.location.origin}/payment`
        },
        {
          headers: { Authorization: `Bearer ${authToken}` }
        }
      );

      if (response.data.status === 'success') {
        // Redirect to Stripe Checkout
        window.location.href = response.data.checkout_url;
      } else {
        toast.error(response.data.message || 'Failed to create checkout session');
      }
    } catch (error) {
      console.error('Error creating checkout:', error);
      toast.error('Failed to initiate payment. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getPackageIcon = (name) => {
    switch (name.toLowerCase()) {
      case 'starter':
        return <Sparkles className="w-6 h-6" />;
      case 'professional':
        return <Zap className="w-6 h-6" />;
      case 'enterprise':
        return <Rocket className="w-6 h-6" />;
      default:
        return <Coins className="w-6 h-6" />;
    }
  };

  const getPackageColor = (name) => {
    switch (name.toLowerCase()) {
      case 'starter':
        return 'from-blue-500 to-cyan-500';
      case 'professional':
        return 'from-purple-500 to-pink-500';
      case 'enterprise':
        return 'from-orange-500 to-red-500';
      default:
        return 'from-gray-500 to-gray-600';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 to-indigo-100 p-6">
      {/* Header */}
      <div className="max-w-6xl mx-auto mb-8">
        <Button
          variant="ghost"
          onClick={() => navigate('/credits')}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Credits Dashboard
        </Button>

        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Buy Credits</h1>
          <p className="text-gray-600 text-lg">
            Choose a package that fits your needs
          </p>
          <div className="mt-4 inline-flex items-center gap-2 bg-white px-6 py-3 rounded-full shadow-sm">
            <Coins className="w-5 h-5 text-green-600" />
            <span className="font-semibold">Current Balance:</span>
            <span className="text-green-600 font-bold">{currentBalance.toFixed(2)} credits</span>
          </div>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {packages.map((pkg) => {
          const isPopular = pkg.name === 'professional';

          return (
            <Card
              key={pkg.name}
              className={`relative ${isPopular ? 'ring-2 ring-purple-500 shadow-xl' : ''}`}
            >
              {isPopular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <Badge className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-1">
                    Most Popular
                  </Badge>
                </div>
              )}

              <CardHeader className="text-center pb-4">
                <div className={`w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-r ${getPackageColor(pkg.name)} flex items-center justify-center text-white`}>
                  {getPackageIcon(pkg.name)}
                </div>
                <CardTitle className="text-2xl capitalize">{pkg.name}</CardTitle>
                <CardDescription>
                  {pkg.name === 'starter' && 'Perfect for getting started'}
                  {pkg.name === 'professional' && 'Best value for regular users'}
                  {pkg.name === 'enterprise' && 'For power users'}
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-6">
                {/* Price */}
                <div className="text-center">
                  <div className="text-4xl font-bold">${pkg.price_usd}</div>
                  <p className="text-sm text-gray-500 mt-1">
                    ${pkg.price_per_credit?.toFixed(4)}/credit
                  </p>
                </div>

                {/* Credits */}
                <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Base Credits:</span>
                    <span className="font-semibold">{pkg.credits.toLocaleString()}</span>
                  </div>
                  {pkg.bonus_credits > 0 && (
                    <div className="flex items-center justify-between text-green-600">
                      <span>Bonus Credits:</span>
                      <span className="font-semibold">+{pkg.bonus_credits.toLocaleString()}</span>
                    </div>
                  )}
                  <div className="border-t pt-2 flex items-center justify-between font-bold text-lg">
                    <span>Total Credits:</span>
                    <span>{pkg.total_credits.toLocaleString()}</span>
                  </div>
                </div>

                {/* Features */}
                <ul className="space-y-3">
                  <li className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <span className="text-sm">
                      {pkg.total_credits >= 20000 && 'Unlimited LLM requests'}
                      {pkg.total_credits < 20000 && pkg.total_credits >= 5000 && 'High volume operations'}
                      {pkg.total_credits < 5000 && 'Standard operations'}
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <span className="text-sm">Social media posting</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <span className="text-sm">Email campaigns</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <span className="text-sm">Data scraping</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <span className="text-sm">Analytics & reports</span>
                  </li>
                </ul>

                {/* Buy Button */}
                <Button
                  className={`w-full ${isPopular ? 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600' : ''}`}
                  onClick={() => handleBuyCredits(pkg.name)}
                  disabled={loading}
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Processing...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <CreditCard className="w-4 h-4" />
                      Buy Now
                    </span>
                  )}
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Info Section */}
      <div className="max-w-6xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>Payment Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <CreditCard className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold">Secure Payment</h3>
                  <p className="text-sm text-gray-600">
                    Powered by Stripe. Your payment information is encrypted and secure.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                  <Zap className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <h3 className="font-semibold">Instant Activation</h3>
                  <p className="text-sm text-gray-600">
                    Credits are added to your account immediately after payment.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                  <Coins className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-semibold">No Expiration</h3>
                  <p className="text-sm text-gray-600">
                    Your credits never expire. Use them at your own pace.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
