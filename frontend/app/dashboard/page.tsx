"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { isAuthenticated, logout } from "@/lib/auth";

export default function DashboardPage() {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
    } else {
      setChecked(true);
    }
  }, [router]);

  function handleLogout() {
    logout();
    router.push("/login");
  }

  if (!checked) return null; // avoid flashing content before redirect check completes

  return (
    <div className="min-h-screen bg-black text-white p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <Button variant="outline" onClick={handleLogout}>
          Logout
        </Button>
      </div>
      <p className="text-gray-400 mt-2">You're logged in.</p>
    </div>
  );
}