'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';

// QAHistory interface
interface QAHistory {
  question: string;
  answer: string;
  contexts: string[];
  timestamp: Date;
}

// helper to check if document is ready
function isReady(status?: string | null) {
  if (!status) return false;
  const s = status.toLowerCase();
  return s === 'processed' || s === 'ready' || s === 'completed';
}

function QAContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated } = useAuth();
  const [documentId, setDocumentId] = useState<string>('');
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusLoading, setStatusLoading] = useState(true);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<QAHistory[]>([]);
  const [docStatus, setDocStatus] = useState<string>('');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    const docId = searchParams.get('document_id');
    if (!docId) {
      router.push('/rag');
      return;
    }
    setDocumentId(docId);

    // Polling document status
    let interval: number | undefined;
    const checkStatus = async () => {
      try {
        const resp = await api.getDocumentStatus(docId);
        setDocStatus(resp.status);
        setStatusLoading(false);
        if (isReady(resp.status) && interval) {
          window.clearInterval(interval);
        }
        if (resp.status === 'FAILED' || resp.status?.toLowerCase() === 'failed') {
          if (interval) window.clearInterval(interval);
          setError(resp.error || 'Document processing failed');
        }
      } catch (e: any) {
        console.warn('Status check failed', e);
        setStatusLoading(false);
        setError(e.message || 'Could not check document status');
      }
    };

    // Initial status check
    checkStatus();
    interval = window.setInterval(checkStatus, 2000);

    return () => {
      if (interval) window.clearInterval(interval);
    };
  }, [isAuthenticated, router, searchParams]);

  // Load chat history once doc is ready
  useEffect(() => {
    if (!documentId || !isReady(docStatus)) return;

    const fetchHistory = async () => {
      try {
        const chats = await api.getQAHistory(documentId);
        setHistory(
          chats.map((chat) => ({
            ...chat,
            timestamp: new Date(chat.timestamp),
          }))
        );
      } catch (e: any) {
        console.warn('Failed to fetch chat history', e);
      }
    };

    fetchHistory();
  }, [documentId, docStatus]);

  const handleAskQuestion = async () => {
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    // Double-check document ready
    try {
      const statusResp = await api.getDocumentStatus(documentId);
      if (!isReady(statusResp.status)) {
        setError('Document not ready yet. Please wait until processing completes.');
        return;
      }
    } catch (e: any) {
      setError(e.message || 'Could not verify document status');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await api.askQuestion({
        document_id: documentId,
        question: question.trim(),
        top_k: 3,
      });

      setHistory((prev) => [
        {
          question: question.trim(),
          answer: response.answer,
          contexts: response.contexts,
          timestamp: new Date(),
        },
        ...prev,
      ]);
      setQuestion('');
    } catch (err: any) {
      setError(err.message || 'Failed to get answer');
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated || !documentId) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Document Q&A
          </h1>
          <Button variant="outline" onClick={() => router.push('/dashboard')}>
            ← Back to Dashboard
          </Button>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Question Input */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>❓ Ask a Question</CardTitle>
                <CardDescription>Ask questions about your legal document</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                {statusLoading ? (
                  <div className="text-center py-8">
                    <div className="text-xl mb-2">Checking document status...</div>
                    <div className="text-sm text-slate-500">Please wait — processing may take 30–60 seconds.</div>
                  </div>
                ) : !isReady(docStatus) ? (
                  <div className="text-center py-8">
                    <div className="text-xl mb-2">Document is still processing</div>
                    <div className="text-sm text-slate-500">Please wait until processing completes to ask questions.</div>
                  </div>
                ) : (
                  <>
                    <Textarea
                      placeholder="e.g., What are the payment terms in this contract?"
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      rows={4}
                      disabled={loading}
                    />

                    <Button onClick={handleAskQuestion} disabled={loading || !question.trim()} className="w-full">
                      {loading ? 'Getting Answer...' : 'Ask Question'}
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Q&A History */}
            <div className="mt-6 space-y-4">
              {history.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-12 text-slate-500">
                    No questions asked yet. Start by asking a question above!
                  </CardContent>
                </Card>
              ) : (
                history.map((item, index) => (
                  <Card key={index}>
                    <CardHeader>
                      <CardTitle className="text-lg">Q: {item.question}</CardTitle>
                      <CardDescription>{item.timestamp.toLocaleString()}</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <h4 className="font-semibold mb-2 text-green-600">Answer:</h4>
                        <p className="text-slate-700 dark:text-slate-300 whitespace-pre-wrap">{item.answer}</p>
                      </div>

                      {item.contexts.length > 0 && (
                        <>
                          <Separator />
                          <div>
                            <h4 className="font-semibold mb-2 text-blue-600">Relevant Contexts:</h4>
                            <div className="space-y-2">
                              {item.contexts.map((context, idx) => (
                                <div key={idx} className="p-3 bg-slate-50 dark:bg-slate-800 rounded text-sm">
                                  <span className="font-medium text-blue-600">[{idx + 1}]</span> {context}
                                </div>
                              ))}
                            </div>
                          </div>
                        </>
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>

          {/* Tips Sidebar */}
          <div>
            <Card className="sticky top-8">
              <CardHeader>
                <CardTitle>💡 Tips</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div>
                  <h4 className="font-semibold mb-1">Be Specific</h4>
                  <p className="text-slate-600 dark:text-slate-400">Ask detailed questions about specific clauses or terms</p>
                </div>
                <Separator />
                <div>
                  <h4 className="font-semibold mb-1">Reference Sections</h4>
                  <p className="text-slate-600 dark:text-slate-400">Mention specific sections if you know them</p>
                </div>
                <Separator />
                <div>
                  <h4 className="font-semibold mb-1">Example Questions</h4>
                  <ul className="list-disc list-inside text-slate-600 dark:text-slate-400 space-y-1">
                    <li>What are the payment terms?</li>
                    <li>What is the termination clause?</li>
                    <li>What are the parties' obligations?</li>
                    <li>What is the liability limit?</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function QAPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Loading...</div>}>
      <QAContent />
    </Suspense>
  );
}
