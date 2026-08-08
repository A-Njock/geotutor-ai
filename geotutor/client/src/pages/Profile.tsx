import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, User, LogOut } from "lucide-react";
import { useLocation } from "wouter";
import { trpc } from "@/lib/trpc";
import { toast } from "sonner";

export default function Profile() {
  const { user, logout } = useAuth();
  const [, setLocation] = useLocation();

  const logoutMutation = trpc.auth.logout.useMutation({
    onSuccess: () => {
      logout();
      toast.success("Logged out successfully");
      setLocation("/");
    },
  });

  if (!user) {
    setLocation("/");
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/30">
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container py-4">
          <Button variant="ghost" onClick={() => setLocation("/")}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
        </div>
      </header>
      <main className="container py-12">
        <div className="max-w-2xl mx-auto space-y-6">
          <div className="space-y-2">
            <h2 className="text-3xl font-bold text-foreground">Profile</h2>
            <p className="text-muted-foreground">Manage your account settings and preferences</p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="w-5 h-5" />
                Account Information
              </CardTitle>
              <CardDescription>Your GeoTutor account details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Name</p>
                  <p className="text-base">{user.name || "Not provided"}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Email</p>
                  <p className="text-base">{user.email || "Not provided"}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Role</p>
                  <p className="text-base capitalize">{user.role}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Login Method</p>
                  <p className="text-base capitalize">{user.loginMethod || "Not provided"}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Account Actions</CardTitle>
              <CardDescription>Manage your session and account</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="destructive" onClick={() => logoutMutation.mutate()} disabled={logoutMutation.isPending}>
                <LogOut className="w-4 h-4 mr-2" />
                {logoutMutation.isPending ? "Logging out..." : "Logout"}
              </Button>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
