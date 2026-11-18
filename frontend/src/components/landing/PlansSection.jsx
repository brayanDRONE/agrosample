import React, { useState } from 'react';
import Icon from './Icon';
import './PlansSection.css';

const plans = [
  {
    id: 'Free',
    name: 'Free',
    price: '$0',
    period: 'CLP',
    subtitle: 'Conoce AgroSample sin compromiso.',
    features: [
      '1 usuario por empresa',
      'Hasta 2 usos de módulo al día',
      'Acceso a los módulos habilitados',
      'Configuración remota de impresora',
      'Soporte básico'
    ],
    cta: 'Comenzar gratis'
  },
  {
    id: 'Starter',
    name: 'Starter',
    price: '$89.990',
    period: 'CLP/mes + IVA',
    subtitle: 'Digitaliza tus operaciones diarias.',
    popular: true,
    features: [
      'Acceso a los cuatro módulos',
      '1 usuario por empresa',
      'Hasta 150 operaciones mensuales',
      'Muestreo y etiquetado personalizado',
      'Planillas de Descripción del Lote',
      'Validación de SDP',
      'Validación de cerezas para China (CSG/CSP)',
      'Generación de documentos PDF',
      'Configuración remota de impresora',
      'Soporte remoto estándar'
    ],
    cta: 'Elegir Starter'
  },
  {
    id: 'Pro',
    name: 'Pro',
    price: '$149.990',
    period: 'CLP/mes + IVA',
    subtitle: 'Mayor capacidad para operaciones intensivas.',
    features: [
      'Acceso a los cuatro módulos',
      '1 usuario por empresa',
      'Alto volumen de operaciones, sujeto a política de uso razonable',
      'Impresión personalizada de adhesivos',
      'Diagramación de pallets',
      'Generación de reportes PDF',
      'Validaciones y documentación',
      'Configuración remota de impresora',
      'Soporte remoto prioritario',
      'Asistencia de puesta en marcha'
    ],
    cta: 'Elegir Pro'
  }
];

const comparison = [
  { label: 'Usuarios por empresa', values: ['1', '1', '1'] },
  { label: 'Operaciones permitidas', values: ['2 cada 24 horas', 'Hasta 150 al mes', 'Alto volumen*'] },
  { label: 'Módulo de muestreo', values: ['Limitado', true, true] },
  { label: 'Impresión de adhesivos', values: [false, true, true] },
  { label: 'Diagramas de pallets', values: [false, false, true] },
  { label: 'Generación de planillas', values: ['Limitado', true, true] },
  { label: 'Validación SDP', values: ['Limitado', true, true] },
  { label: 'Validación CSG/CSP China', values: ['Limitado', true, true] },
  { label: 'Exportación PDF', values: ['Limitado', true, true] },
  { label: 'Configuración de impresoras', values: [true, true, true] },
  { label: 'Nivel de soporte', values: ['Básico', 'Remoto estándar', 'Remoto prioritario'] }
];

const services = [
  { name: 'Activación y capacitación remota', price: '$49.990 + IVA' },
  { name: 'Configuración de impresora Zebra/Bixolon', price: '$79.990 + IVA' },
  { name: 'Implementación presencial', price: 'Desde $149.990 + IVA' },
  { name: 'Personalizaciones', price: 'A cotizar' }
];

const faqs = [
  {
    q: '¿Puedo cambiar de plan?',
    a: 'Sí, puedes solicitar un cambio de plan cuando lo necesites. Escríbenos desde el formulario de contacto y revisaremos las condiciones de tu caso.'
  },
  {
    q: '¿Los precios incluyen IVA?',
    a: 'No. Los valores publicados corresponden a precios netos y se les debe sumar IVA.'
  },
  {
    q: '¿Necesito instalar algún programa?',
    a: 'AgroSample funciona desde el navegador. Para la impresión de adhesivos se requiere una impresora compatible; consúltanos por la configuración en tu equipo.'
  },
  {
    q: '¿Qué impresoras son compatibles?',
    a: 'Ofrecemos configuración para impresoras Zebra y Bixolon. Si usas otro modelo, contáctanos y evaluamos su compatibilidad.'
  },
  {
    q: '¿Qué sucede cuando alcanzo el límite de operaciones?',
    a: 'Los límites aún no se aplican de forma automática. Para conocer cómo se gestionará esta situación, solicita información comercial y te responderemos.'
  },
  {
    q: '¿Puedo contratar la plataforma solo durante la temporada frutícola?',
    a: 'Es una consulta frecuente. Escríbenos con las fechas de tu temporada y te informaremos las alternativas disponibles.'
  }
];

function selectPlan(planId) {
  window.dispatchEvent(new CustomEvent('agrosample:select-plan', { detail: planId }));
}

function Cell({ value }) {
  if (value === true) return <span className="cmp-yes" aria-label="Incluido">✓</span>;
  if (value === false) return <span className="cmp-no" aria-label="No disponible">✕</span>;
  return <span>{value}</span>;
}

export default function PlansSection() {
  const [openFaq, setOpenFaq] = useState(0);

  return (
    <section id="planes" className="plans-section">
      <div className="plans-container">
        <div className="plans-header">
          <h2 className="plans-title">Planes diseñados para tu operación</h2>
          <p className="plans-subtitle">
            Desde pequeñas operaciones hasta empresas agroexportadoras de mayor volumen. Encuentra el plan que mejor se adapta a tus necesidades.
          </p>
        </div>

        <div className="plans-grid">
          {plans.map((plan) => (
            <article key={plan.id} className={`plan-card${plan.popular ? ' popular' : ''}`}>
              {plan.popular && <span className="plan-badge">Más popular</span>}
              <h3 className="plan-name">{plan.name}</h3>
              <p className="plan-subtitle">{plan.subtitle}</p>
              <p className="plan-price">
                <strong>{plan.price}</strong>
                <span>{plan.period}</span>
              </p>
              <ul className="plan-features">
                {plan.features.map((feature) => <li key={feature}>{feature}</li>)}
              </ul>
              <a href="#contacto" className="plan-button" onClick={() => selectPlan(plan.id)}>{plan.cta}</a>
            </article>
          ))}
        </div>

        <div className="compare-wrap">
          <h3 className="plans-block-title">Compara los planes</h3>
          <div className="compare-scroll">
            <table className="compare-table">
              <thead>
                <tr>
                  <th>Característica</th>
                  <th>Free</th>
                  <th className="highlight">Starter</th>
                  <th>Pro</th>
                </tr>
              </thead>
              <tbody>
                {comparison.map((row) => (
                  <tr key={row.label}>
                    <th scope="row">{row.label}</th>
                    {row.values.map((value, index) => (
                      <td key={index} className={index === 1 ? 'highlight' : ''}><Cell value={value} /></td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="plans-note">* Sujeto a política de uso razonable. Los límites comerciales son referenciales.</p>
        </div>

        <div className="services-wrap">
          <h3 className="plans-block-title">Servicios de implementación</h3>
          <div className="services-grid">
            {services.map((service) => (
              <div key={service.name} className="service-card">
                <span className="service-icon" aria-hidden="true"><Icon name="headset" size={22} /></span>
                <strong>{service.name}</strong>
                <span className="service-price">{service.price}</span>
              </div>
            ))}
          </div>
          <p className="plans-note">Valores referenciales. La configuración remota de impresora está incluida en todos los planes; la asistencia de puesta en marcha está incluida en el plan Pro.</p>
        </div>

        <div className="faq-wrap">
          <h3 className="plans-block-title">Preguntas frecuentes</h3>
          <div className="faq-list">
            {faqs.map((item, index) => {
              const open = openFaq === index;
              return (
                <div key={item.q} className={`faq-item${open ? ' open' : ''}`}>
                  <button
                    type="button"
                    className="faq-question"
                    aria-expanded={open}
                    onClick={() => setOpenFaq(open ? -1 : index)}
                  >
                    <span>{item.q}</span>
                    <span className="faq-caret" aria-hidden="true">{open ? '−' : '+'}</span>
                  </button>
                  {open && <p className="faq-answer">{item.a}</p>}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
