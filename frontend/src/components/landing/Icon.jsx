import React from 'react';

const paths = {
  bolt: <path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z" />,
  shield: (
    <>
      <path d="M12 3 4 6v6c0 4.5 3.2 8 8 9 4.8-1 8-4.5 8-9V6l-8-3Z" />
      <path d="m8.5 12 2.5 2.5 4.5-5" />
    </>
  ),
  chart: (
    <>
      <path d="M5 21V12M12 21V4M19 21v-6" />
      <path d="M3 21h18" />
    </>
  ),
  leaf: (
    <>
      <path d="M20 4C10 4 5 9 5 15c0 2 1 4 3 4 6 0 12-5 12-15Z" />
      <path d="M4 21c3-6 7-9 12-11" />
    </>
  ),
  printer: (
    <>
      <path d="M7 9V3h10v6M7 17H4v-7h16v7h-3" />
      <path d="M7 14h10v7H7z" />
    </>
  ),
  file: (
    <>
      <path d="M6 3h8l5 5v13H6z" />
      <path d="M14 3v5h5M9 13h7M9 17h7" />
    </>
  ),
  cherry: (
    <>
      <circle cx="7" cy="17" r="4" />
      <circle cx="17" cy="17" r="4" />
      <path d="M7 13c1-5 4-8 8-9M17 13c-1-4-2-7-2-9M15 4c2 0 4 1 5 2" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="13" r="8" />
      <path d="M12 9v4l3 2M9 2h6" />
    </>
  ),
  target: (
    <>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1" />
    </>
  ),
  layers: <path d="m12 3 9 5-9 5-9-5 9-5ZM3 13l9 5 9-5M3 17.5l9 5 9-5" />,
  headset: (
    <>
      <path d="M4 14v-2a8 8 0 0 1 16 0v2" />
      <rect x="3" y="14" width="4" height="6" rx="1.5" />
      <rect x="17" y="14" width="4" height="6" rx="1.5" />
      <path d="M19 20c0 1.5-2 2-5 2" />
    </>
  ),
  calendar: (
    <>
      <rect x="4" y="5" width="16" height="16" rx="2" />
      <path d="M4 10h16M8 3v4M16 3v4M12 14v3M10.5 15.5h3" />
    </>
  )
};

export default function Icon({ name, size = 24 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}
