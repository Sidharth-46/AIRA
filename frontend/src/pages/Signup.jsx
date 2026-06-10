import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useThemeStore } from '../stores/themeStore'
import { HiOutlineArrowRight, HiOutlineEye, HiOutlineEyeOff } from 'react-icons/hi'

export default function Signup() {
  const navigate = useNavigate()
  const { signup, loading, error, clearError } = useAuthStore()
  const { theme } = useThemeStore()
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const success = await signup(form)
    if (success) navigate('/chat')
  }

  const passwordStrength = (pwd) => {
    let score = 0
    if (pwd.length >= 8) score++
    if (/[A-Z]/.test(pwd)) score++
    if (/[a-z]/.test(pwd)) score++
    if (/[0-9]/.test(pwd)) score++
    if (/[^A-Za-z0-9]/.test(pwd)) score++
    return score
  }

  const strength = passwordStrength(form.password)
  const strengthColors = ['#EF4444', '#F59E0B', '#F59E0B', '#22C55E', '#22C55E']
  const strengthLabels = ['', 'Weak', 'Fair', 'Good', 'Strong']

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center', 
      background: 'var(--color-aira-bg)',
      padding: '24px',
    }}>
      <div style={{ width: '100%', maxWidth: '400px' }} className="animate-fade-in">
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px', marginBottom: '48px' }}>
          <img src={theme === 'light' ? '/logo-dark.png' : '/logo.png'} alt="AIRA Logo" style={{ width: '56px', height: '56px' }} />
          <div style={{ textAlign: 'left' }}>
            <h1 style={{ fontSize: '32px', fontWeight: 700, color: 'var(--color-aira-text)', lineHeight: 1 }}>
              AIRA
            </h1>
            <p style={{ fontSize: '13px', color: 'var(--color-aira-text-dim)', marginTop: '4px' }}>
              Autonomous Intelligent Reasoning Agent
            </p>
          </div>
        </div>

        {/* Card */}
        <div style={{ 
          background: 'var(--color-aira-surface-3)', 
          border: '1px solid var(--color-aira-border)', 
          borderRadius: '16px', 
          padding: '32px',
        }}>
          {error && (
            <div className="animate-fade-in" style={{ 
              marginBottom: '16px', padding: '12px 16px', borderRadius: '10px', fontSize: '13px',
              background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', color: '#EF4444',
            }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--color-aira-text-muted)', marginBottom: '6px' }}>
                Username
              </label>
              <input 
                type="text" placeholder="johndoe" value={form.username}
                onChange={(e) => { setForm({ ...form, username: e.target.value }); clearError() }}
                minLength={3} required 
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--color-aira-text-muted)', marginBottom: '6px' }}>
                Email
              </label>
              <input 
                type="email" placeholder="you@example.com" value={form.email}
                onChange={(e) => { setForm({ ...form, email: e.target.value }); clearError() }}
                required 
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--color-aira-text-muted)', marginBottom: '6px' }}>
                Password
              </label>
              <div style={{ position: 'relative' }}>
                <input 
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Minimum 8 characters" value={form.password}
                  onChange={(e) => { setForm({ ...form, password: e.target.value }); clearError() }}
                  minLength={8} required 
                  style={{ paddingRight: '40px' }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: 'absolute',
                    right: '12px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    color: 'var(--color-aira-text-dim)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '4px'
                  }}
                  title={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <HiOutlineEyeOff size={18} /> : <HiOutlineEye size={18} />}
                </button>
              </div>
              {form.password && (
                <div style={{ display: 'flex', gap: '4px', alignItems: 'center', marginTop: '8px' }}>
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} style={{ 
                      height: '3px', flex: 1, borderRadius: '2px', transition: 'background 0.2s ease',
                      background: strength >= i ? strengthColors[strength - 1] : 'var(--color-aira-border)',
                    }} />
                  ))}
                  <span style={{ fontSize: '12px', marginLeft: '8px', color: strengthColors[strength - 1] || 'var(--color-aira-text-dim)' }}>
                    {strengthLabels[strength] || ''}
                  </span>
                </div>
              )}
            </div>

            <button 
              type="submit" disabled={loading}
              className="btn-primary"
              style={{ width: '100%', height: '44px', fontSize: '15px', marginTop: '8px' }}
            >
              {loading ? (
                <div style={{ width: '18px', height: '18px', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
              ) : (
                <>Create Account <HiOutlineArrowRight /></>
              )}
            </button>
          </form>

          <p style={{ textAlign: 'center', marginTop: '24px', fontSize: '14px', color: 'var(--color-aira-text-dim)' }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: 'var(--color-aira-primary)', fontWeight: 500, textDecoration: 'none' }}>
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
