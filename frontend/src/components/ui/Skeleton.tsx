import React from 'react';
import { twMerge } from 'tailwind-merge';

export const Skeleton: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => {
  return (
    <div
      className={twMerge('animate-pulse rounded-xl bg-slate-200/80', className)}
      {...props}
    />
  );
};

