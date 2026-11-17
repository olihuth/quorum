import React, { useState } from 'react';
import { Lock, Mail } from 'lucide-react';

interface AuthPageProps {
  onLogin: (email: string, password: string) => string | null;
  onRegister: (email: string, password: string) => string | null;
  onContinueAsGuest: () => void;
}

type AuthMode = 'login' | 'register';

export const AuthPage: React.FC<AuthPageProps> = ({
  onLogin,
  onRegister,
  onContinueAsGuest,
}) => {
  const [mode, setMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleModeSwitch = (nextMode: AuthMode) => {
    setMode(nextMode);
    setErrorMessage(null);
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setErrorMessage(null);

    const normalizedEmail = email.trim().toLowerCase();
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailPattern.test(normalizedEmail)) {
      setErrorMessage('Informe um endereço de e-mail válido.');
      return;
    }

    if (password.length < 6) {
      setErrorMessage('A senha deve ter pelo menos 6 caracteres.');
      return;
    }

    if (mode === 'register') {
      if (password !== confirmPassword) {
        setErrorMessage('As senhas digitadas não coincidem.');
        return;
      }

      const registerError = onRegister(normalizedEmail, password);
      if (registerError) {
        setErrorMessage(registerError);
      }
      return;
    }

    const loginError = onLogin(normalizedEmail, password);
    if (loginError) {
      setErrorMessage(loginError);
    }
  };

  return (
    <div className="mx-auto max-w-md py-6 sm:py-10">
      <section className="rounded-lg border border-[#E2E8F0] bg-[#FFFFFF] p-6 sm:p-8">
        {/* Editorial Heading */}
        <div className="border-b border-[#E2E8F0] pb-5">
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-[#002776]">
            <span className="h-2 w-2 rounded-full bg-[#009C3B]" aria-hidden="true" />
            Quorum · Acesso Cidadão
          </div>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-[#0F172A]">
            {mode === 'login' ? 'Entrar na plataforma' : 'Criar conta cidadã'}
          </h1>
          <p className="mt-1 text-xs leading-relaxed text-slate-500">
            Acompanhe proposições legislativas, personalize suas Casas Seguidas e gerencie alertas em uma conta privada.
          </p>
        </div>

        {/* Mode Switch Tabs */}
        <div className="mt-5 grid grid-cols-2 rounded-lg border border-[#E2E8F0] bg-[#F8FAFC] p-1">
          <button
            type="button"
            onClick={() => handleModeSwitch('login')}
            className={`rounded-md py-1.5 text-xs font-semibold transition-colors ${
              mode === 'login'
                ? 'bg-white text-[#002776] ring-1 ring-[#E2E8F0]'
                : 'text-slate-500 hover:text-[#0F172A]'
            }`}
          >
            Entrar
          </button>
          <button
            type="button"
            onClick={() => handleModeSwitch('register')}
            className={`rounded-md py-1.5 text-xs font-semibold transition-colors ${
              mode === 'register'
                ? 'bg-white text-[#002776] ring-1 ring-[#E2E8F0]'
                : 'text-slate-500 hover:text-[#0F172A]'
            }`}
          >
            Criar Conta
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-5 space-y-4" noValidate>
          <div>
            <label
              htmlFor="auth-email"
              className="block text-xs font-semibold text-[#0F172A]"
            >
              E-mail
            </label>
            <div className="relative mt-1.5">
              <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                id="auth-email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="cidadao@exemplo.com.br"
                className="w-full rounded-md border border-[#E2E8F0] bg-white py-2 pl-9 pr-3 text-sm text-[#0F172A] placeholder:text-slate-400 focus:border-[#002776] focus:outline-none"
                required
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="auth-password"
              className="block text-xs font-semibold text-[#0F172A]"
            >
              Senha
            </label>
            <div className="relative mt-1.5">
              <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                id="auth-password"
                type="password"
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Mínimo de 6 caracteres"
                className="w-full rounded-md border border-[#E2E8F0] bg-white py-2 pl-9 pr-3 text-sm text-[#0F172A] placeholder:text-slate-400 focus:border-[#002776] focus:outline-none"
                required
              />
            </div>
          </div>

          {mode === 'register' && (
            <div>
              <label
                htmlFor="auth-confirm-password"
                className="block text-xs font-semibold text-[#0F172A]"
              >
                Confirmar senha
              </label>
              <div className="relative mt-1.5">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  id="auth-confirm-password"
                  type="password"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repita a senha"
                  className="w-full rounded-md border border-[#E2E8F0] bg-white py-2 pl-9 pr-3 text-sm text-[#0F172A] placeholder:text-slate-400 focus:border-[#002776] focus:outline-none"
                  required
                />
              </div>
            </div>
          )}

          {errorMessage && (
            <p
              role="alert"
              className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs font-medium text-red-700"
            >
              {errorMessage}
            </p>
          )}

          <button
            type="submit"
            className="w-full rounded-md bg-[#002776] px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#1D4ED8]"
          >
            {mode === 'login' ? 'Entrar' : 'Criar conta'}
          </button>
        </form>

        {/* Secondary Guest Preview */}
        <div className="mt-5 border-t border-[#E2E8F0] pt-4 text-center">
          <button
            type="button"
            onClick={onContinueAsGuest}
            className="text-xs font-semibold text-[#1D4ED8] hover:underline"
          >
            Explorar pautas como visitante →
          </button>
        </div>

        {/* Strict Privacy Notice */}
        <p className="mt-4 border-l-2 border-[#009C3B] pl-3 text-[11px] leading-relaxed text-slate-500">
          Sua conta no Quorum é estritamente privada: não exibimos perfil público, seguidores ou histórico pessoal para outros usuários.
        </p>
      </section>
    </div>
  );
};
