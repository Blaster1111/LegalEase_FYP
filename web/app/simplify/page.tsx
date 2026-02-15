'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';

export default function SimplifyPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();

  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [simplified, setSimplified] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      const ext = selectedFile.name.split('.').pop()?.toLowerCase();

      if (!['pdf', 'txt', 'docx'].includes(ext || '')) {
        setError('Only PDF, TXT, and DOCX files are supported');
        setFile(null);
        return;
      }

      setFile(selectedFile);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError('');
    setSimplified('');
    setSuccess('');
    setStatus('PROCESSING');

    try {
      const resp = await api.simplifyFile(file);

      setSuccess(`Document "${resp.filename}" simplified successfully!`);
      setSimplified(resp.simplified_text);
      setStatus('READY');
    } catch (e: any) {
      setError(e.message || 'Simplification failed');
      setStatus('FAILED');
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Legal Simplifier
            </h1>
            <p className="text-slate-600 dark:text-slate-400 mt-2">
              Convert complex legal text into plain, easy-to-understand language
            </p>
          </div>
          <Button variant="outline" onClick={() => router.push('/dashboard')}>
            ← Back
          </Button>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Upload Card */}
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>📤 Upload Document</CardTitle>
              <CardDescription>
                Supported formats: PDF, TXT, DOCX
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {success && (
                <Alert className="bg-green-50 border-green-200">
                  <AlertDescription>{success}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label>Select File</Label>
                <Input
                  type="file"
                  accept=".pdf,.txt,.docx"
                  onChange={handleFileChange}
                  disabled={loading}
                />

                {file && (
                  <div className="flex items-center gap-2 text-sm bg-slate-50 dark:bg-slate-800 p-3 rounded">
                    <span>📄</span>
                    <span className="font-medium">{file.name}</span>
                    <span className="text-xs">
                      ({(file.size / 1024).toFixed(2)} KB)
                    </span>
                  </div>
                )}
              </div>

              <Button
                onClick={handleUpload}
                disabled={!file || loading}
                className="w-full bg-green-600 hover:bg-green-700"
              >
                {loading ? 'Simplifying...' : 'Upload & Simplify'}
              </Button>

              {status && (
                <div className="text-sm mt-2">
                  Status:{' '}
                  <span
                    className={`font-semibold px-2 py-1 rounded ${
                      status === 'READY'
                        ? 'bg-green-100 text-green-700'
                        : status === 'PROCESSING'
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-red-100 text-red-700'
                    }`}
                  >
                    {status}
                  </span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Simplified Text Card */}
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>📄 Simplified Text</CardTitle>
              <CardDescription>
                Plain-language version of your legal document
              </CardDescription>
            </CardHeader>

            <CardContent>
              {loading && (
                <div className="text-center py-12 text-slate-500">
                  ⏳ Processing document…
                </div>
              )}

              {!loading && !simplified && (
                <div className="text-center py-12 text-slate-400">
                  Upload a document to see the simplified version here.
                </div>
              )}

              {simplified && (
                <p className="whitespace-pre-wrap text-slate-700 dark:text-slate-300">
                  {simplified}
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
