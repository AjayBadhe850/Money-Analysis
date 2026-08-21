import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export interface ProgressProps {
  value: number; // 0 - 100
  className?: string;
  variant?: 'default' | 'emerald' | 'amber' | 'rose' | 'gradient';
  size?: 'sm' | 'md' | 'lg';
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  className,
  variant = 'default',
  size = 'md',
}) => {
  const clampedValue = Math.min(100, Math.max(0, value));

  const variants = {
    default: 'bg-indigo-500',
    emerald: 'bg-emerald-500',
    amber: 'bg-amber-500',
    rose: 'bg-rose-500',
    gradient: 'bg-gradient-to-r from-emerald-500 via-amber-500 to-rose-500',
  };

  const sizes = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  return (
    <div className={twMerge('w-full rounded-full bg-slate-800/80 overflow-hidden', sizes[size], className)}>
      <div
        className={twMerge('h-full transition-all duration-500 rounded-full', variants[variant])}
        style={{ width: `${clampedValue}%` }}
      />
    </div>
  );
};
