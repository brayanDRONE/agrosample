import React, { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import HeaderLanding from '../components/landing/HeaderLanding';
import HeroSection from '../components/landing/HeroSection';
import InfoSection, { CtaSection } from '../components/landing/InfoSection';
import PlansSection from '../components/landing/PlansSection';
import ContactSection from '../components/landing/ContactSection';
import Footer from '../components/landing/Footer';

const VIEWS = {
  '#planes': <PlansSection />,
  '#contacto': <ContactSection />
};

export default function LandingPage() {
  const { hash } = useLocation();
  const view = VIEWS[hash];

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [hash]);

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
    </div>
  );
}
