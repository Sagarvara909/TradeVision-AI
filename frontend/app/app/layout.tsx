"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { isAuthenticated, logout } from "@/lib/auth";

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/upload", label: "Upload" },
  { href: "/history", label: "History" },
  { href: "/watchlist", label: "Watchlist" },
  { href: "/profile", label: "Profile" },
  { href: "/settings", label: "Settings" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
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

  if (!checked) return null;

  return (
    <div className="flex min-h-screen bg-black text-white">
      <aside className="w-56 border-r border-gray-800 p-4 flex flex-col">
        <h2 className="text-lg font-bold mb-6 px-2">TradeVision AI</h2>
        <nav className="flex flex-col gap-1 flex-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`px-3 py-2 rounded-md text-sm ${
                pathname === item.href
                  ? "bg-gray-800 text-white"
                  : "text-gray-400 hover:bg-gray-900 hover:text-white"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <Button variant="outline" onClick={handleLogout} className="mt-4">
          Logout
        </Button>
      </aside>
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}