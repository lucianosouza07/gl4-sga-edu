import React from "react";
import { LoginForm } from "@/components/login-form";
import { Card, CardContent } from "@/components/ui/card";

export const LoginPage: React.FC = () => {
  return (
    <div className="flex min-h-screen w-full items-center justify-center p-6 md:p-10 bg-linear-to-b from-background via-background to-muted/30">
      <div className="w-full max-w-sm md:max-w-md">
        <Card className="border-border/60 shadow-xl shadow-primary/5 backdrop-blur-xs">
          <CardContent className="p-6 md:p-8">
            <LoginForm />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
