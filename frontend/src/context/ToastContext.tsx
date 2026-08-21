import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastContextType {
  toasts: Toast[];
  showToast: (type: ToastType, title: string, message?: string, duration?: number) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (type: ToastType, title: string, message?: string, duration: number = 4000) => {
      const id = Math.random().toString(36).substring(2, 9);
      const newToast: Toast = { id, type, title, message, duration };

      setToasts((prev) => [...prev, newToast]);

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  return (
    <ToastContext.Provider value={{ toasts, showToast, removeToast }}>
      {children}
      {/* Toast Render Container */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-md w-full pointer-events-none px-4">
        {toasts.map((toast) => {
          const getIcon = () => {
            switch (toast.type) {
              case 'success':
                return <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />;
              case 'error':
                return <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />;
              case 'warning':
                return <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />;
              case 'info':
              default:
                return <Info className="w-5 h-5 text-sky-400 shrink-0" />;
            }
          };

          const getBgColor = () => {
            switch (toast.type) {
              case 'success':
                return 'bg-slate-900/95 border-emerald-500/30 text-slate-100 shadow-emerald-500/10';
              case 'error':
                return 'bg-slate-900/95 border-rose-500/30 text-slate-100 shadow-rose-500/10';
              case 'warning':
                return 'bg-slate-900/95 border-amber-500/30 text-slate-100 shadow-amber-500/10';
              case 'info':
              default:
                return 'bg-slate-900/95 border-sky-500/30 text-slate-100 shadow-sky-500/10';
            }
          };

          return (
            <div
              key={toast.id}
              className={`pointer-events-auto flex items-start gap-3 p-4 rounded-xl border backdrop-blur-md shadow-xl transition-all duration-300 transform translate-y-0 ${getBgColor()}`}
            >
              {getIcon()}
              <div className="flex-1 text-sm">
                <div className="font-semibold text-slate-100">{toast.title}</div>
                {toast.message && <div className="text-xs text-slate-400 mt-0.5">{toast.message}</div>}
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                className="text-slate-400 hover:text-slate-200 transition-colors p-0.5"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};
