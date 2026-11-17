import React from 'react';
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react';
import { ToastNotification } from '../types/quorum';

interface ToastProps {
  toasts: ToastNotification[];
  onDismiss: (id: string) => void;
}

export const ToastContainer: React.FC<ToastProps> = ({ toasts, onDismiss }) => {
  if (toasts.length === 0) return null;

  return (
    <div
      aria-live="polite"
      className="fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2 px-4 sm:px-0"
    >
      {toasts.map((toast) => {
        const icon =
          toast.variant === 'success' ? (
            <CheckCircle2 className="h-5 w-5 shrink-0 text-[#009C3B]" />
          ) : toast.variant === 'warning' ? (
            <AlertCircle className="h-5 w-5 shrink-0 text-[#EAB308]" />
          ) : (
            <Info className="h-5 w-5 shrink-0 text-[#1D4ED8]" />
          );

        const borderClass =
          toast.variant === 'success'
            ? 'border-l-4 border-l-[#009C3B]'
            : toast.variant === 'warning'
              ? 'border-l-4 border-l-[#EAB308]'
              : 'border-l-4 border-l-[#1D4ED8]';

        return (
          <div
            key={toast.id}
            className={`animate-fade-in-up flex items-start gap-3 rounded-xl border border-[#E2E8F0] bg-[#FFFFFF] p-3.5 shadow-lg ${borderClass}`}
          >
            {icon}
            <p className="flex-1 text-sm font-medium text-[#0F172A]">{toast.message}</p>
            <button
              type="button"
              onClick={() => onDismiss(toast.id)}
              className="rounded p-0.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              aria-label="Fechar notificação"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
};
