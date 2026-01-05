// app/page.tsx
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="flex justify-center mb-6">
            <div className="text-8xl">⚖️</div>
          </div>
          <h1 className="text-6xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            LegalEase
          </h1>
          <p className="text-2xl text-slate-600 dark:text-slate-300 mb-4">
            AI-Powered Legal Document Analysis
          </p>
          <p className="text-lg text-slate-500 dark:text-slate-400 max-w-2xl mx-auto">
            Transform the way you analyze legal documents with cutting-edge RAG technology. 
            Get instant, accurate answers from your contracts and legal files.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <Card className="shadow-lg hover:shadow-xl transition-shadow border-blue-200 dark:border-blue-900">
            <CardHeader>
              <div className="text-5xl mb-4">📄</div>
              <CardTitle className="text-xl">Upload Documents</CardTitle>
              <CardDescription className="text-base">
                Support for PDF, DOCX, and TXT files
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Securely upload your legal contracts, agreements, and documents. 
                Our system processes them instantly for intelligent analysis.
              </p>
            </CardContent>
          </Card>

          <Card className="shadow-lg hover:shadow-xl transition-shadow border-purple-200 dark:border-purple-900">
            <CardHeader>
              <div className="text-5xl mb-4">🔍</div>
              <CardTitle className="text-xl">Smart Search</CardTitle>
              <CardDescription className="text-base">
                AI-powered semantic understanding
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Ask questions in natural language and get precise answers with 
                relevant context from your documents using advanced RAG technology.
              </p>
            </CardContent>
          </Card>

          <Card className="shadow-lg hover:shadow-xl transition-shadow border-green-200 dark:border-green-900">
            <CardHeader>
              <div className="text-5xl mb-4">⚡</div>
              <CardTitle className="text-xl">Instant Results</CardTitle>
              <CardDescription className="text-base">
                Real-time document processing
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Get immediate insights with lightning-fast processing. 
                Our AI analyzes documents in seconds, not hours.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Additional Features */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg p-8 mb-16">
          <h2 className="text-3xl font-bold text-center mb-8 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Why Choose LegalEase?
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="flex items-start gap-4">
              <div className="text-3xl">🎯</div>
              <div>
                <h3 className="font-semibold text-lg mb-2">Accurate Analysis</h3>
                <p className="text-slate-600 dark:text-slate-400">
                  Powered by state-of-the-art language models for precise understanding
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="text-3xl">🔒</div>
              <div>
                <h3 className="font-semibold text-lg mb-2">Secure & Private</h3>
                <p className="text-slate-600 dark:text-slate-400">
                  Your documents are encrypted and stored with enterprise-grade security
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="text-3xl">💼</div>
              <div>
                <h3 className="font-semibold text-lg mb-2">Professional Grade</h3>
                <p className="text-slate-600 dark:text-slate-400">
                  Built for lawyers, paralegals, and legal professionals
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="text-3xl">🌐</div>
              <div>
                <h3 className="font-semibold text-lg mb-2">Always Available</h3>
                <p className="text-slate-600 dark:text-slate-400">
                  Access your documents and insights anytime, anywhere
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center">
          <h2 className="text-3xl font-bold mb-6">
            Ready to Transform Your Legal Workflow?
          </h2>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Button
              size="lg"
              onClick={() => router.push('/login')}
              className="bg-blue-600 hover:bg-blue-700 text-lg px-8 py-6"
            >
              Login
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => router.push('/signup')}
              className="text-lg px-8 py-6 border-2 border-blue-600 text-blue-600 hover:bg-blue-50 dark:hover:bg-slate-800"
            >
              Sign Up Free
            </Button>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-4">
            No credit card required • Free to get started
          </p>
        </div>
      </div>
    </div>
  );
}