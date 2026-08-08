import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { trpc } from "@/lib/trpc";
import { Loader2, ArrowLeft, Clock, Image as ImageIcon } from "lucide-react";
import { useLocation } from "wouter";
import { formatDistanceToNow } from "date-fns";

export default function History() {
  const { user, loading: authLoading } = useAuth();
  const [, setLocation] = useLocation();

  const { data: history, isLoading } = trpc.qa.getHistory.useQuery(undefined, {
    enabled: !!user,
  });

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/30">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container py-4 flex items-center justify-between">
          <Button variant="ghost" onClick={() => setLocation("/")}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
          <h1 className="text-xl font-semibold">Question History</h1>
          <div className="w-24"></div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="space-y-2">
            <h2 className="text-3xl font-bold text-foreground">Your Question History</h2>
            <p className="text-muted-foreground">Review all the questions you've asked and their answers</p>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Card key={i}>
                  <CardHeader>
                    <Skeleton className="h-6 w-3/4" />
                    <Skeleton className="h-4 w-1/4" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-5/6 mt-2" />
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* History List */}
          {history && history.length > 0 && (
            <div className="space-y-4">
              {history.map((item) => (
                <Card key={item.id} className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => {
                  if (item.answer) {
                    setLocation(`/ask?q=${encodeURIComponent(item.questionText)}&visual=${item.includeVisual}&type=${item.visualType || ""}`);
                  }
                }}>
                  <CardHeader>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <CardTitle className="text-lg line-clamp-2">{item.questionText}</CardTitle>
                        <CardDescription className="flex items-center gap-4 mt-2">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatDistanceToNow(new Date(item.createdAt), { addSuffix: true })}
                          </span>
                          {item.includeVisual && (
                            <span className="flex items-center gap-1 text-primary">
                              <ImageIcon className="w-3 h-3" />
                              {item.visualType}
                            </span>
                          )}
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  {item.answer && (
                    <CardContent>
                      <p className="text-sm text-muted-foreground line-clamp-3">{item.answer.answerText.substring(0, 200)}...</p>
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>
          )}

          {/* Empty State */}
          {history && history.length === 0 && (
            <Card>
              <CardContent className="py-12 text-center">
                <Clock className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Questions Yet</h3>
                <p className="text-muted-foreground mb-4">Start asking questions to build your learning history</p>
                <Button onClick={() => setLocation("/")}>Ask Your First Question</Button>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
