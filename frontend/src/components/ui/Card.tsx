import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div
    className={twMerge(
      'rounded-2xl border border-slate-200/90 bg-white/95 backdrop-blur-md text-slate-900 shadow-[0_10px_30px_-5px_rgba(0,50,150,0.04),0_4px_12px_-2px_rgba(0,0,0,0.02)] overflow-hidden transition-all',
      className
    )}
    {...props}
  />
);

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={twMerge('flex flex-col space-y-1.5 p-5 pb-4', className)} {...props} />
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ className, ...props }) => (
  <h3 className={twMerge('font-bold text-lg leading-tight tracking-tight text-slate-900 font-sans', className)} {...props} />
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({ className, ...props }) => (
  <p className={twMerge('text-xs text-slate-500 font-sans', className)} {...props} />
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={twMerge('p-5 pt-0', className)} {...props} />
);

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={twMerge('flex items-center p-5 pt-0 border-t border-slate-100 mt-4', className)} {...props} />
);

