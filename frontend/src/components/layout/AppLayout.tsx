import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';
import { useAuth } from '../../context/AuthContext';
import { Skeleton } from '../ui/Skeleton';

export const AppLayout: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen w-screen bg-slate-950 items-center justify-center">
        <div className="space-y-4 text-center">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600 animate-pulse mx-auto" />
          <p className="text-sm font-medium text-slate-400">Loading Money Analysis Controller...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 selection:bg-indigo-500/20 selection:text-indigo-400">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar />
        <main className="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
