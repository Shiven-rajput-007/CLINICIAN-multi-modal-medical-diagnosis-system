import React from 'react';
import { User, Building, Mail, Shield, Calendar, LogOut } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { formatDate } from '../utils/formatters';

export const Profile: React.FC = () => {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-sky-700 text-white font-bold text-xl shadow-xs">
            {user.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900">
              {user.name}
            </h1>
            <p className="text-xs text-sky-700 font-semibold uppercase tracking-wider capitalize">
              {user.role.replace('_', ' ')} • {user.hospital_name}
            </p>
          </div>
        </div>

        <button
          onClick={logout}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 transition-colors self-start sm:self-auto"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-6">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700 pb-3 border-b border-slate-100">
          Institutional Clinician Profile
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-slate-500 font-medium flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-slate-400" />
              Full Name
            </span>
            <p className="text-sm font-semibold text-slate-900">{user.name}</p>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-slate-500 font-medium flex items-center gap-1.5">
              <Mail className="w-3.5 h-3.5 text-slate-400" />
              Institutional Email
            </span>
            <p className="text-sm font-semibold text-slate-900 font-mono">{user.email}</p>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-slate-500 font-medium flex items-center gap-1.5">
              <Building className="w-3.5 h-3.5 text-slate-400" />
              Hospital Affiliation
            </span>
            <p className="text-sm font-semibold text-slate-900">{user.hospital_name}</p>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-slate-500 font-medium flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-slate-400" />
              Access Role
            </span>
            <p className="text-sm font-semibold text-slate-900 capitalize">{user.role.replace('_', ' ')}</p>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1 sm:col-span-2">
            <span className="text-slate-500 font-medium flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              Account Created / Verified
            </span>
            <p className="text-sm font-semibold text-slate-900">{formatDate(user.created_at)}</p>
          </div>
        </div>

        <div className="p-4 rounded-lg bg-sky-50/70 border border-sky-200 text-xs text-sky-900 space-y-1">
          <p className="font-semibold">Security & Data Governance</p>
          <p className="text-sky-800">
            This account is cryptographically protected with bcrypt password hashing and RS256/HS256 JSON Web Tokens. Diagnosis records uploaded under this identity are strictly isolated and inaccessible to any other accounts on this server.
          </p>
        </div>
      </div>
    </div>
  );
};
