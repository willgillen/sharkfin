"use client";

import { ReactNode, useState, useRef, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";

interface DashboardLayoutProps {
  children: ReactNode;
}

// Main navigation items (always visible)
const mainNavigation = [
  { name: "Dashboard", href: "/dashboard" },
  { name: "Accounts", href: "/dashboard/accounts" },
  { name: "Transactions", href: "/dashboard/transactions" },
  { name: "Budgets", href: "/dashboard/budgets" },
  { name: "Reports", href: "/dashboard/reports" },
];

// Additional items in "More" dropdown
const moreNavigation = [
  { name: "Categories", href: "/dashboard/categories", group: "Settings" },
  { name: "Payees", href: "/dashboard/payees", group: "Settings" },
  { name: "Rules", href: "/dashboard/rules", group: "Settings" },
  { name: "Import Transactions", href: "/dashboard/import", group: "Tools" },
  { name: "Import History", href: "/dashboard/import/history", group: "Tools" },
];

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const moreMenuRef = useRef<HTMLDivElement>(null);

  // Close "More" dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (moreMenuRef.current && !moreMenuRef.current.contains(event.target as Node)) {
        setMoreMenuOpen(false);
      }
    }

    if (moreMenuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [moreMenuOpen]);

  // Check if any "More" menu item is active
  const isMoreMenuActive = moreNavigation.some((item) => pathname === item.href);

  return (
    <div className="min-h-screen bg-surface-secondary">
      {/* Top Navigation */}
      <nav className="bg-surface shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Left side: Logo and Navigation */}
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <Link href="/dashboard" className="text-2xl font-bold text-text-primary">
                  🦈 Shark Fin
                </Link>
              </div>

              {/* Desktop Navigation */}
              <div className="hidden md:ml-6 md:flex md:space-x-8">
                {/* Main navigation items */}
                {mainNavigation.map((item) => {
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={`${
                        isActive
                          ? "border-primary-500 text-text-primary"
                          : "border-transparent text-text-tertiary hover:border-border hover:text-text-secondary"
                      } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
                    >
                      {item.name}
                    </Link>
                  );
                })}

                {/* More dropdown */}
                <div className="relative" ref={moreMenuRef}>
                  <button
                    onClick={() => setMoreMenuOpen(!moreMenuOpen)}
                    className={`${
                      isMoreMenuActive
                        ? "border-primary-500 text-text-primary"
                        : "border-transparent text-text-tertiary hover:border-border hover:text-text-secondary"
                    } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
                  >
                    More
                    <svg
                      className={`ml-1 h-4 w-4 transition-transform ${moreMenuOpen ? "rotate-180" : ""}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {/* Dropdown Menu */}
                  {moreMenuOpen && (
                    <div className="absolute left-0 mt-2 w-56 rounded-md shadow-lg bg-surface ring-1 ring-border z-50">
                      <div className="py-1">
                        {/* Group items by category */}
                        {["Tools", "Settings"].map((group) => {
                          const groupItems = moreNavigation.filter((item) => item.group === group);
                          if (groupItems.length === 0) return null;

                          return (
                            <div key={group}>
                              <div className="px-4 py-2 text-xs font-semibold text-text-tertiary uppercase tracking-wider">
                                {group}
                              </div>
                              {groupItems.map((item) => {
                                const isActive = pathname === item.href;
                                return (
                                  <Link
                                    key={item.name}
                                    href={item.href}
                                    onClick={() => setMoreMenuOpen(false)}
                                    className={`${
                                      isActive
                                        ? "bg-primary-50 text-primary-600"
                                        : "text-text-primary hover:bg-surface-secondary"
                                    } block px-4 py-2 text-sm`}
                                  >
                                    {item.name}
                                  </Link>
                                );
                              })}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right side: User menu */}
            <div className="flex items-center">
              <div className="hidden md:flex md:items-center">
                <span className="text-sm text-text-secondary mr-4">{user?.full_name}</span>
                <button
                  onClick={logout}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  Logout
                </button>
              </div>

              {/* Mobile menu button */}
              <div className="md:hidden">
                <button
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className="inline-flex items-center justify-center p-2 rounded-md text-text-tertiary hover:text-text-primary hover:bg-surface-secondary focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500"
                >
                  <span className="sr-only">Open main menu</span>
                  {mobileMenuOpen ? (
                    <svg className="block h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  ) : (
                    <svg className="block h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-border">
            <div className="pt-2 pb-3 space-y-1">
              {/* Main navigation in mobile */}
              {mainNavigation.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`${
                      isActive
                        ? "bg-primary-50 border-primary-500 text-primary-600"
                        : "border-transparent text-text-primary hover:bg-surface-secondary hover:border-border"
                    } block pl-3 pr-4 py-2 border-l-4 text-base font-medium`}
                  >
                    {item.name}
                  </Link>
                );
              })}

              {/* More items in mobile */}
              <div className="border-t border-border mt-2 pt-2">
                {["Tools", "Settings"].map((group) => {
                  const groupItems = moreNavigation.filter((item) => item.group === group);
                  if (groupItems.length === 0) return null;

                  return (
                    <div key={group} className="mb-2">
                      <div className="px-4 py-2 text-xs font-semibold text-text-tertiary uppercase tracking-wider">
                        {group}
                      </div>
                      {groupItems.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                          <Link
                            key={item.name}
                            href={item.href}
                            onClick={() => setMobileMenuOpen(false)}
                            className={`${
                              isActive
                                ? "bg-primary-50 border-primary-500 text-primary-600"
                                : "border-transparent text-text-primary hover:bg-surface-secondary hover:border-border"
                            } block pl-3 pr-4 py-2 border-l-4 text-base font-medium`}
                          >
                            {item.name}
                          </Link>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* User section in mobile */}
            <div className="pt-4 pb-3 border-t border-border">
              <div className="flex items-center px-4">
                <div className="text-base font-medium text-text-primary">{user?.full_name}</div>
              </div>
              <div className="mt-3 px-4">
                <button
                  onClick={() => {
                    logout();
                    setMobileMenuOpen(false);
                  }}
                  className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
}
