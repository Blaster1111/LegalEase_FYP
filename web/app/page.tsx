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
          <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
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
        </div>
      </div>
    </div>
  );
}