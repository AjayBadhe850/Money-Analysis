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
    default: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
    secondary: 'bg-slate-800 text-slate-300 border-slate-700',
    success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    destructive: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    outline: 'bg-transparent text-slate-300 border-slate-700',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    cyan: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-[10px] font-medium',
    md: 'px-2.5 py-1 text-xs font-medium',
  };

  return (
    <div
      className={twMerge(
        clsx(
          'inline-flex items-center gap-1 rounded-full border transition-colors',
          variants[variant],
          sizes[size],
          className
        )
      )}
      {...props}
    />
  );
};
