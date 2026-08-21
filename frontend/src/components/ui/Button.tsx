import React from 'react';
import { Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'emerald';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  className,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled,
  leftIcon,
  rightIcon,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-background disabled:opacity-50 disabled:cursor-not-allowed select-none rounded-lg';

  const variants = {
    primary: 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20 focus:ring-indigo-500 active:scale-[0.98]',
    secondary: 'bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-700/60 focus:ring-slate-400 active:scale-[0.98]',
    outline: 'bg-transparent hover:bg-slate-800/60 text-slate-200 border border-slate-700 hover:border-slate-600 focus:ring-indigo-500',
    ghost: 'bg-transparent hover:bg-slate-800/50 text-slate-300 hover:text-slate-100 focus:ring-slate-500',
    destructive: 'bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/20 focus:ring-rose-500 active:scale-[0.98]',
    emerald: 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20 focus:ring-emerald-500 active:scale-[0.98]',
  };

  const sizes = {
    sm: 'text-xs px-3 py-1.5 gap-1.5',
    md: 'text-sm px-4 py-2 gap-2',
    lg: 'text-base px-5 py-2.5 gap-2.5',
    icon: 'p-2',
  };

  return (
    <button
      className={twMerge(clsx(baseStyles, variants[variant], sizes[size], className))}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Loader2 className="w-4 h-4 animate-spin shrink-0" />}
      {!isLoading && leftIcon && <span className="shrink-0">{leftIcon}</span>}
      {children}
      {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
    </button>
  );
};
