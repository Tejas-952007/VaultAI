'use client';

import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { EmployeeIdentity, VaultAPI } from '@/lib/api';

interface AuthContextValue {
  employee: EmployeeIdentity | null;
  loading: boolean;
  login: (employeeId: string, password: string) => Promise<EmployeeIdentity>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const PUBLIC_PATHS = ['/login'];
const PROTECTED_PATHS = [
  '/workbench',
  '/documents',
  '/access-control',
  '/history',
  '/audit-history',
  '/security',
  '/air-gap',
  '/sandbox',
  '/telemetry',
];

function isProtectedPath(pathname: string) {
  return PROTECTED_PATHS.some((path) => pathname === path || pathname.startsWith(`${path}/`));
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return context;
}

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [employee, setEmployee] = useState<EmployeeIdentity | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    VaultAPI.getCurrentEmployee()
      .then((response) => {
        if (active) setEmployee(response.employee);
      })
      .catch(() => {
        if (active) setEmployee(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [pathname]);

  useEffect(() => {
    if (loading) return;
    if (pathname === '/') {
      router.replace(employee ? '/workbench' : '/login');
    } else if (employee && pathname === '/login') {
      router.replace('/workbench');
    } else if (!employee && isProtectedPath(pathname) && !PUBLIC_PATHS.includes(pathname)) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [employee, loading, pathname, router]);

  const value = useMemo<AuthContextValue>(() => ({
    employee,
    loading,
    async login(employeeId: string, password: string) {
      const response = await VaultAPI.login(employeeId, password);
      setEmployee(response.employee);
      return response.employee;
    },
    async logout() {
      await VaultAPI.logout();
      setEmployee(null);
      router.replace('/login');
    },
  }), [employee, loading, router]);

  const isLogin = pathname === '/login';
  const showApplication = !loading && Boolean(employee) && !isLogin && pathname !== '/';

  return (
    <AuthContext.Provider value={value}>
      {loading || pathname === '/' || (!employee && isProtectedPath(pathname)) || (employee && isLogin)
        ? <div className="min-h-screen bg-[#070B12]" />
        : isLogin
          ? children
          : showApplication
            ? children
            : <div className="min-h-screen bg-[#070B12]" />}
    </AuthContext.Provider>
  );
}
