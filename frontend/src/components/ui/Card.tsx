import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div
    className={twMerge(
      'rounded-xl border border-slate-800 bg-slate-900/70 backdrop-blur-md text-slate-100 shadow-xl overflow-hidden',
      className
    )}
    {...props}
  />
);

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={twMerge('flex flex-col space-y-1.5 p-5 pb-4', className)} {...props} />
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ className, ...props }) => (
  <h3 className={twMerge('font-semibold text-lg leading-none tracking-tight text-slate-100', className)} {...props} />
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({ className, ...props }) => (
  <p className={twMerge('text-xs text-slate-400', className)} {...props} />
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={twMerge('p-5 pt-0', className)} {...props} />
);

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={twMerge('flex items-center p-5 pt-0 border-t border-slate-800/60 mt-4', className)} {...props} />
);
