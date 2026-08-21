import { BudgetStatus, AlertSeverity } from '../types';

export function formatCurrency(amount: number | undefined | null, currency: string = 'USD'): string {
  if (amount === undefined || amount === null || isNaN(amount)) {
    return '$0.00';
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatCurrencyExact(amount: number | undefined | null, currency: string = 'USD'): string {
  if (amount === undefined || amount === null || isNaN(amount)) {
    return '$0.00';
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatPercent(value: number | undefined | null): string {
  if (value === undefined || value === null || isNaN(value)) {
    return '0.0%';
  }
  return `${value.toFixed(1)}%`;
}

export function formatDate(dateString: string | undefined | null): string {
  if (!dateString) return 'N/A';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateString;
  }
}

export function getBudgetStatusColor(status: BudgetStatus): { bg: string; text: string; border: string; bar: string } {
  switch (status) {
    case 'SAFE':
      return {
        bg: 'bg-emerald-500/10 dark:bg-emerald-500/15',
        text: 'text-emerald-600 dark:text-emerald-400',
        border: 'border-emerald-500/20',
        bar: 'bg-emerald-500',
      };
    case 'WARNING':
      return {
        bg: 'bg-amber-500/10 dark:bg-amber-500/15',
        text: 'text-amber-600 dark:text-amber-400',
        border: 'border-amber-500/20',
        bar: 'bg-amber-500',
      };
    case 'CRITICAL':
      return {
        bg: 'bg-orange-500/10 dark:bg-orange-500/15',
        text: 'text-orange-600 dark:text-orange-400',
        border: 'border-orange-500/20',
        bar: 'bg-orange-500',
      };
    case 'EXCEEDED':
      return {
        bg: 'bg-rose-500/10 dark:bg-rose-500/15',
        text: 'text-rose-600 dark:text-rose-400',
        border: 'border-rose-500/20',
        bar: 'bg-rose-500',
      };
    default:
      return {
        bg: 'bg-slate-500/10',
        text: 'text-slate-400',
        border: 'border-slate-500/20',
        bar: 'bg-slate-500',
      };
  }
}

export function getAlertSeverityColor(severity: AlertSeverity): { bg: string; text: string; border: string } {
  switch (severity) {
    case 'CRITICAL':
      return {
        bg: 'bg-rose-500/10 text-rose-500 border-rose-500/30',
        text: 'text-rose-400',
        border: 'border-rose-500/40',
      };
    case 'WARNING':
      return {
        bg: 'bg-amber-500/10 text-amber-500 border-amber-500/30',
        text: 'text-amber-400',
        border: 'border-amber-500/40',
      };
    case 'INFO':
    default:
      return {
        bg: 'bg-sky-500/10 text-sky-500 border-sky-500/30',
        text: 'text-sky-400',
        border: 'border-sky-500/40',
      };
  }
}
