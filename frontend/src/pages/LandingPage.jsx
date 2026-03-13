import React from 'react';
import HeaderLanding from '../components/landing/HeaderLanding';
import HeroSection from '../components/landing/HeroSection';
import InfoSection from '../components/landing/InfoSection';
import Footer from '../components/landing/Footer';

export default function LandingPage() {
  return (
    <div className="landing-page">
      <HeaderLanding />
      <HeroSection />
      <InfoSection />
      <Footer />
    </div>
  );
}
