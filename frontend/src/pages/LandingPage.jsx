import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import HeaderLanding from '../components/landing/HeaderLanding';
import HeroSection from '../components/landing/HeroSection';
import InfoSection, { CtaSection } from '../components/landing/InfoSection';
import PlansSection from '../components/landing/PlansSection';
import ContactSection from '../components/landing/ContactSection';
import VideosSection from '../components/landing/VideosSection';
import Footer from '../components/landing/Footer';
import WhatsAppButton from '../components/landing/WhatsAppButton';

export default function LandingPage() {
  const { hash } = useLocation();
  const [selectedContactInterest, setSelectedContactInterest] = useState(null);
  const view = hash === '#videos'
    ? <VideosSection />
    : hash === '#planes'
      ? <PlansSection />
      : hash === '#contacto'
        ? <ContactSection selectedInterest={selectedContactInterest} />
        : null;

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [hash]);

  useEffect(() => {
    const onSelectPlan = (event) => setSelectedContactInterest(event.detail);
    window.addEventListener('agrosample:select-plan', onSelectPlan);
    return () => window.removeEventListener('agrosample:select-plan', onSelectPlan);
  }, []);

  return (
    <div className="landing-page" style={{ background: 'linear-gradient(180deg, #11242b 0%, #0e1f26 100%)', minHeight: '100vh' }}>
      <HeaderLanding />
      {view ? (
        <main className="landing-view">{view}</main>
      ) : (
        <>
          <HeroSection />
          <InfoSection />
          <CtaSection />
        </>
      )}
      <Footer />
      <WhatsAppButton />
    </div>
  );
}
