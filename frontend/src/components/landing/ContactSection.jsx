import React, { useEffect, useState } from 'react';
import './ContactSection.css';

const CONTACT_EMAIL = 'brayannunez8@gmail.com';
const PLAN_OPTIONS = ['Consulta general', 'Free', 'Starter', 'Pro', 'Servicios de implementación'];

export default function ContactSection() {
  const [form, setForm] = useState({ nombre: '', empresa: '', email: '', telefono: '', interes: PLAN_OPTIONS[0], mensaje: '' });
  const [sent, setSent] = useState(false);

  useEffect(() => {
    const onSelectPlan = (event) => setForm((prev) => ({ ...prev, interes: event.detail }));
    window.addEventListener('agrosample:select-plan', onSelectPlan);
    return () => window.removeEventListener('agrosample:select-plan', onSelectPlan);
  }, []);

  const update = (field) => (event) => setForm((prev) => ({ ...prev, [field]: event.target.value }));

  const handleSubmit = (event) => {
    event.preventDefault();
    const subject = `Contacto AgroSample.cl - ${form.interes}`;
    const body = [
      `Nombre: ${form.nombre}`,
      `Empresa: ${form.empresa}`,
      `Correo: ${form.email}`,
      `Teléfono: ${form.telefono}`,
      `Interés: ${form.interes}`,
      '',
      form.mensaje
    ].join('\n');
    window.location.href = `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    setSent(true);
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
          <button type="submit" className="lc-submit">Enviar consulta</button>
          {sent && (
            <p className="lc-hint">
              Se abrió tu aplicación de correo con el mensaje listo. Envíalo para completar tu consulta.
            </p>
          )}
        </form>
      </div>
    </section>
  );
}
