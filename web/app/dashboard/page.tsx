// app/dashboard/page.tsx
'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import { api, DocumentResponse } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';

function isReady(status?: string | null) {
  if (!status) return false;
  const s = status.toLowerCase();
  return s === 'processed' || s === 'ready' || s === 'completed' || s === 'ready';
}

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, logout } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const pollingRefs = useRef<Record<string, number>>({}); // store intervals

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    // load user's existing documents
    (async () => {
      try {
        const docs = await api.getUserDocuments();
        setDocuments(docs);
        // start polling for any that are not ready
        docs.forEach((d) => {
          if (!isReady(d.status)) startPollingStatus(d.document_id);
        });
      } catch (e: any) {
        console.warn('Could not fetch documents', e);
        setError(e.message || 'Could not fetch documents');
      }
    })();

    return () => {
      Object.values(pollingRefs.current).forEach((id) => clearInterval(id));
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  const startPollingStatus = (docId: string) => {
    if (pollingRefs.current[docId]) return;

    const intervalId = window.setInterval(async () => {
      try {
        const statusResp = await api.getDocumentStatus(docId);
        setDocuments((prev) =>
          prev.map((d) => (d.document_id === docId ? { ...d, status: statusResp.status } : d))
        );

        if (isReady(statusResp.status)) {
          clearInterval(intervalId);
          delete pollingRefs.current[docId];
        }

        if (statusResp.status === 'FAILED' || statusResp.status?.toLowerCase() === 'failed') {
          clearInterval(intervalId);
          delete pollingRefs.current[docId];
        }
      } catch (e) {
        console.warn('Status poll error', e);
      }
    }, 2000);

    pollingRefs.current[docId] = intervalId;
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess('');

    try {
      const response = await api.uploadDocument(file);
      setDocuments((prev) => [response, ...prev]);
      setSuccess(`Document "${response.filename}" uploaded successfully! Processing...`);
      setFile(null);
      const fileInput = document.getElementById('file-upload') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

      startPollingStatus(response.document_id);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const openQAPage = (docId: string) => {
    router.push(`/qa?document_id=${docId}`);
  };

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              LegalEase Dashboard
            </h1>
            <p className="text-slate-600 dark:text-slate-400 mt-2">Manage and analyze your legal documents</p>
          </div>
          <Button variant="outline" onClick={handleLogout}>
            Logout
          </Button>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Upload Section */}
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span className="text-2xl">📤</span>
                Upload Document
              </CardTitle>
              <CardDescription>Upload a legal document (PDF, TXT, or DOCX) for AI-powered analysis</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {success && (
                <Alert className="bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-900">
                  <AlertDescription className="text-green-800 dark:text-green-300">{success}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="file-upload">Select File</Label>
                <Input
                  id="file-upload"
                  type="file"
                  accept=".pdf,.txt,.docx"
                  onChange={handleFileChange}
                  disabled={uploading}
                  className="cursor-pointer"
                />
                {file && (
                  <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800 p-3 rounded">
                    <span>📄</span>
                    <span className="font-medium">{file.name}</span>
                    <span className="text-xs">({(file.size / 1024).toFixed(2)} KB)</span>
                  </div>
                )}
              </div>

              <Button onClick={handleUpload} disabled={!file || uploading} className="w-full bg-blue-600 hover:bg-blue-700">
                {uploading ? (
                  <span className="flex items-center gap-2">
                    <span className="animate-spin">⏳</span>
                    Uploading...
                  </span>
                ) : (
                  'Upload Document'
                )}
              </Button>

              <div className="text-xs text-slate-500 dark:text-slate-400 space-y-1">
                <p>• Supported formats: PDF, TXT, DOCX</p>
                <p>• Maximum file size: 10MB</p>
                <p>• Processing typically takes 30-60 seconds</p>
              </div>
            </CardContent>
          </Card>

          {/* Documents List */}
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span className="text-2xl">📚</span>
                Your Documents
              </CardTitle>
              <CardDescription>{documents.length > 0 ? `${documents.length} document${documents.length > 1 ? 's' : ''} uploaded` : 'No documents uploaded yet'}</CardDescription>
            </CardHeader>
            <CardContent>
              {documents.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📄</div>
                  <p className="text-slate-500 dark:text-slate-400 mb-2">No documents uploaded yet</p>
                  <p className="text-sm text-slate-400 dark:text-slate-500">Upload your first document to get started</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[500px] overflow-y-auto">
                  {documents.map((doc, index) => (
                    <div key={doc.document_id || index}>
                      <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">{doc.filename}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-slate-500 dark:text-slate-400">Status:</span>
                            <span
                              className={`text-xs font-semibold px-2 py-1 rounded ${
                                isReady(doc.status)
                                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                  : doc.status === 'processing' || doc.status === 'PROCESSING'
                                  ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                                  : doc.status === 'failed' || doc.status === 'FAILED'
                                  ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                                  : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                              }`}
                            >
                              {doc.status}
                            </span>
                          </div>
                        </div>

                        {isReady(doc.status) && (
                          <Button size="sm" onClick={() => openQAPage(doc.document_id)} className="ml-4 bg-blue-600 hover:bg-blue-700">
                            Ask Questions →
                          </Button>
                        )}
                        {!isReady(doc.status) && doc.status !== 'failed' && (
                          <span className="ml-4 text-sm text-yellow-600 dark:text-yellow-400 flex items-center gap-2">
                            <span className="animate-spin">⏳</span>
                            Processing...
                          </span>
                        )}
                        {doc.status === 'failed' && (
                          <span className="ml-4 text-sm text-red-600 dark:text-red-400">Processing failed</span>
                        )}
                      </div>
                      {index < documents.length - 1 && <Separator className="my-3" />}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Info Cards */}
        <div className="grid md:grid-cols-3 gap-6 mt-6">
          <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-900">
            <CardHeader>
              <CardTitle className="text-lg">🤖 AI-Powered</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600 dark:text-slate-400">Advanced RAG technology for accurate document analysis</p>
            </CardContent>
          </Card>

          <Card className="bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-900">
            <CardHeader>
              <CardTitle className="text-lg">🔒 Secure</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600 dark:text-slate-400">Your documents are encrypted and securely stored</p>
            </CardContent>
          </Card>

          <Card className="bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-900">
            <CardHeader>
              <CardTitle className="text-lg">⚡ Fast</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600 dark:text-slate-400">Get instant answers from your legal documents</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
