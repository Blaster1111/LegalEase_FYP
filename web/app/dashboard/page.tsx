'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, logout } = useAuth();

  // Fix: redirect inside useEffect
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-10">

        {/* Header */}
        <div className="flex justify-between items-center mb-12">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              LegalEase Dashboard
            </h1>
            <p className="text-slate-600 dark:text-slate-400 mt-2">
              AI-powered legal document understanding
            </p>
          </div>

          <Button variant="outline" onClick={handleLogout}>
            Logout
          </Button>
        </div>

        {/* Services Section */}
        <div className="mb-10 text-center">
          <h2 className="text-3xl font-bold mb-3">Our Services</h2>
          <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
            LegalEase helps you understand complex legal documents using advanced AI.
            Upload contracts, agreements, or notices and get instant insights.
          </p>
        </div>

        {/* Service Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">

          {/* RAG Service */}
          <Card className="shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer">
            <CardHeader>
              <CardTitle className="text-2xl flex items-center gap-2">
                📚 Ask Questions
              </CardTitle>
              <CardDescription>
                Upload legal documents and ask questions using AI-powered retrieval.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
                <li>• Ask natural language questions</li>
                <li>• Get precise answers from your document</li>
                <li>• Context-aware legal insights</li>
              </ul>

              <Button
                className="w-full bg-blue-600 hover:bg-blue-700"
                onClick={() => router.push('/qa')}
              >
                Go to RAG
              </Button>
            </CardContent>
          </Card>

          {/* Summarization Service */}
          <Card className="shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer">
            <CardHeader>
              <CardTitle className="text-2xl flex items-center gap-2">
                📝 Summarize Documents
              </CardTitle>
              <CardDescription>
                Generate clear, concise summaries of legal contracts instantly.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
                <li>• Automatic legal document summaries</li>
                <li>• Easy-to-understand output</li>
                <li>• Supports PDF, DOCX, and TXT</li>
              </ul>

              <Button
                className="w-full bg-purple-600 hover:bg-purple-700"
                onClick={() => router.push('/summary')}
              >
                Go to Summarizer
              </Button>
            </CardContent>
          </Card>

          {/* Simplification Service */}
          <Card className="shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer">
            <CardHeader>
              <CardTitle className="text-2xl flex items-center gap-2">
                📄 Simplify Legal Text
              </CardTitle>
              <CardDescription>
                Convert complex legal language into plain, easy-to-understand text.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
                <li>• Simplifies legal terminology</li>
                <li>• Easy-to-read plain language output</li>
                <li>• Supports PDF, DOCX, and TXT</li>
              </ul>

              <Button
                className="w-full bg-green-600 hover:bg-green-700"
                onClick={() => router.push('/simplify')}
              >
                Go to Simplifier
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Bottom Info Section */}
        <div className="grid md:grid-cols-3 gap-6 mt-14">
          <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-900">
            <CardHeader>
              <CardTitle className="text-lg">🤖 AI-Powered</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Advanced NLP models built specifically for legal documents.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-900">
            <CardHeader>
              <CardTitle className="text-lg">⚡ Fast Insights</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Get summaries and answers in seconds.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-900">
            <CardHeader>
              <CardTitle className="text-lg">🔒 Secure</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Your legal documents remain private and protected.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
