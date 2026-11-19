import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/api';
import './ContactSection.css';

const PLAN_OPTIONS = [
  'Consulta general',
  'Free',
  'Starter',
  'Pro',
  'Pro mensual',
  'Pro semestral',
  'Pro anual',
  'Servicios de implementación'
];

export default function ContactSection({ selectedInterest }) {
  const [form, setForm] = useState({ nombre: '', empresa: '', email: '', telefono: '', interes: PLAN_OPTIONS[0], mensaje: '' });
  const [sending, setSending] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);

  useEffect(() => {
    if (PLAN_OPTIONS.includes(selectedInterest)) {
      setForm((prev) => ({ ...prev, interes: selectedInterest }));
    }
  }, [selectedInterest]);

  const update = (field) => (event) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
    setStatusMessage(null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (sending) return;

    setSending(true);
    setStatusMessage(null);
    try {
      const payload = Object.fromEntries(
        Object.entries(form).map(([field, value]) => [field, value.trim()])
      );
      const result = await apiService.submitContactForm(payload);
      setStatusMessage({ type: 'success', text: result.message });
      setForm((prev) => ({
        ...prev,
        nombre: '',
        empresa: '',
        email: '',
        telefono: '',
        mensaje: ''
      }));
    } catch (error) {
      const responseStatus = error.response?.status;
      const text = responseStatus === 429
        ? 'Se alcanzó el límite de consultas. Inténtalo nuevamente más tarde.'
        : error.response?.data?.message || 'No pudimos enviar tu consulta. Inténtalo nuevamente más tarde.';
      setStatusMessage({ type: 'error', text });
    } finally {
      setSending(false);
    }
  };

  return (
    <section id="contacto" className="lc-section">
      <div className="lc-container">
        <div className="lc-info">
          <h2 className="lc-title">Hablemos de tu operación</h2>
          <p>
            Cuéntanos sobre tu packing o exportadora y te contactaremos con información de planes, una demostración o la implementación que necesitas.
          </p>
          <ul>
            <li>Solicitud de demostración</li>
            <li>Información comercial y de planes</li>
            <li>Servicios de implementación y personalizaciones</li>
          </ul>
        </div>

        <form className="lc-form" onSubmit={handleSubmit}>
          <div className="lc-row">
            <label>
              Nombre
              <input type="text" required value={form.nombre} onChange={update('nombre')} autoComplete="name" />
            </label>
            <label>
              Empresa
              <input type="text" required value={form.empresa} onChange={update('empresa')} autoComplete="organization" />
            </label>
          </div>
          <div className="lc-row">
            <label>
              Correo electrónico
              <input type="email" required value={form.email} onChange={update('email')} autoComplete="email" />
            </label>
            <label>
              Teléfono (opcional)
              <input type="tel" value={form.telefono} onChange={update('telefono')} autoComplete="tel" />
            </label>
          </div>
          <label>
            Me interesa
            <select value={form.interes} onChange={update('interes')}>
              {PLAN_OPTIONS.map((option) => <option key={option} value={option}>{option}</option>)}
            </select>
          </label>
          <label>
            Mensaje
            <textarea rows="4" required value={form.mensaje} onChange={update('mensaje')} />
          </label>
          <button type="submit" className="lc-submit" disabled={sending}>
            {sending ? 'Enviando…' : 'Enviar consulta'}
          </button>
          {statusMessage && (
            <p
              className={`lc-hint lc-hint--${statusMessage.type}`}
              role={statusMessage.type === 'error' ? 'alert' : 'status'}
              aria-live="polite"
            >
              {statusMessage.text}
            </p>
          )}
        </form>
      </div>
    </section>
  );
}
