import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'success' | 'warning' | 'destructive' | 'outline' | 'purple' | 'cyan';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'default',
  size = 'md',
  ...props
}) => {
  const variants = {
    default: 'bg-blue-50 text-blue-700 border-blue-200/80 font-semibold',
    secondary: 'bg-slate-100 text-slate-700 border-slate-200 font-medium',
    success: 'bg-emerald-50 text-emerald-700 border-emerald-200/80 font-semibold',
    warning: 'bg-amber-50 text-amber-700 border-amber-200/80 font-semibold',
    destructive: 'bg-rose-50 text-rose-700 border-rose-200/80 font-semibold',
    outline: 'bg-white text-slate-700 border-slate-200 font-medium shadow-sm',
    purple: 'bg-purple-50 text-purple-700 border-purple-200/80 font-semibold',
    cyan: 'bg-cyan-50 text-cyan-700 border-cyan-200/80 font-semibold',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-[10px]',
    md: 'px-2.5 py-1 text-xs',
  };

  return (
    <div
      className={twMerge(
        clsx(
          'inline-flex items-center gap-1 rounded-full border transition-colors font-sans select-none',
          variants[variant],
          sizes[size],
          className
        )
      )}
      {...props}
    />
  );
};

