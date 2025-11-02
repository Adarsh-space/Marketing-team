import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { UserPlus, Mail, Lock, User, Building } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export default function SignupPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
    companyName: ''
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (field) => (e) => {
    setFormData(prev => ({
      ...prev,
      [field]: e.target.value
    }));
  };

  const handleSignup = async (e) => {
    e.preventDefault();

    // Validation
    if (!formData.email || !formData.password || !formData.fullName) {
      toast.error('Please fill in all required fields');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    if (formData.password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${BACKEND_URL}/api/auth/signup`, {
        email: formData.email,
        password: formData.password,
        full_name: formData.fullName,
        company_name: formData.companyName || formData.fullName
      });

      if (response.data.status === 'success') {
        // Store auth token and user data
        localStorage.setItem('auth_token', response.data.token);
        localStorage.setItem('user_id', response.data.user_id);
        localStorage.setItem('tenant_id', response.data.tenant_id);
        localStorage.setItem('user_email', response.data.email);
        localStorage.setItem('user_name', response.data.full_name);

        toast.success('Account created successfully! Welcome to Marketing Minds AI!');

        // Redirect to dashboard
        setTimeout(() => {
          navigate('/dashboard');
        }, 1000);
      } else {
        toast.error(response.data.message || 'Signup failed');
      }
    } catch (error) {
      console.error('Signup error:', error);
      toast.error(error.response?.data?.message || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Marketing Minds AI
          </h1>
          <p className="text-gray-600 mt-2">Create your free account</p>
        </div>

        {/* Signup Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserPlus className="w-5 h-5" />
              Sign Up
            </CardTitle>
            <CardDescription>
              Get started with 100 free credits
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSignup} className="space-y-4">
              {/* Full Name */}
              <div className="space-y-2">
                <Label htmlFor="fullName">Full Name *</Label>
                <div className="relative">
                  <User className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                  <Input
                    id="fullName"
                    type="text"
                    placeholder="John Doe"
                    value={formData.fullName}
                    onChange={handleChange('fullName')}
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              {/* Email */}
              <div className="space-y-2">
                <Label htmlFor="email">Email *</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={formData.email}
                    onChange={handleChange('email')}
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              {/* Company Name */}
              <div className="space-y-2">
                <Label htmlFor="companyName">Company Name (Optional)</Label>
                <div className="relative">
                  <Building className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                  <Input
                    id="companyName"
                    type="text"
                    placeholder="Acme Inc."
                    value={formData.companyName}
                    onChange={handleChange('companyName')}
                    className="pl-10"
                  />
                </div>
              </div>

              {/* Password */}
              <div className="space-y-2">
                <Label htmlFor="password">Password *</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={handleChange('password')}
                    className="pl-10"
                    required
                  />
                </div>
                <p className="text-xs text-gray-500">
                  Minimum 6 characters
                </p>
              </div>

              {/* Confirm Password */}
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password *</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={handleChange('confirmPassword')}
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                className="w-full"
                disabled={loading}
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Creating account...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <UserPlus className="w-4 h-4" />
                    Create Account
                  </span>
                )}
              </Button>

              {/* Terms */}
              <p className="text-xs text-gray-500 text-center">
                By signing up, you agree to our Terms of Service and Privacy Policy
              </p>
            </form>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">
                  Already have an account?
                </span>
              </div>
            </div>

            {/* Login Link */}
            <Button
              variant="outline"
              className="w-full"
              onClick={() => navigate('/login')}
            >
              Sign In
            </Button>
          </CardContent>
        </Card>

        {/* Features */}
        <div className="mt-6 space-y-2 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
            <span>100 free credits to get started</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
            <span>Multi-platform social media management</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
            <span>AI-powered content generation</span>
          </div>
        </div>
      </div>
    </div>
  );
}
