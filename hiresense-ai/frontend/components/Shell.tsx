"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearSession, getCurrentUser, isAuthenticated } from "@/lib/api";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard", roles: ["admin", "hr_staff", "recruiter", "hiring_manager"] },
  { href: "/jobs", label: "Jobs", roles: ["admin", "hr_staff", "recruiter", "hiring_manager"] },
  { href: "/admin", label: "Admin", roles: ["admin"] },
];

export default function Shell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<ReturnType<typeof getCurrentUser>>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    setUser(getCurrentUser());
    setReady(true);
  }, [router]);

  if (!ready) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface">
        <p className="font-body text-sm text-slate-500">Loading HireSense AI…</p>
      </div>
    );
  }

  const visibleLinks = NAV_LINKS.filter((l) => !user || l.roles.includes(user.role));

  return (
    <div className="min-h-screen bg-surface">
      <header className="border-b border-slate-200 bg-ink-950">
        <div className="mx-auto max-w-7xl px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/dashboard" className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-teal-accent" />
              <span className="font-display font-bold text-white tracking-tight">HireSense AI</span>
            </Link>
            <nav className="flex items-center gap-1">
              {visibleLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    pathname?.startsWith(link.href)
                      ? "bg-white/10 text-white"
                      : "text-slate-300 hover:text-white hover:bg-white/5"
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-4">
            {user && (
              <span className="text-sm text-slate-300">
                {user.full_name} <span className="text-slate-500">· {formatRole(user.role)}</span>
              </span>
            )}
            <button
              onClick={() => {
                clearSession();
                router.replace("/login");
              }}
              className="text-sm font-medium text-slate-300 hover:text-white px-3 py-1.5 rounded-md border border-slate-700 hover:border-slate-500 transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
    </div>
  );
}

function formatRole(role: string) {
  return role.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
