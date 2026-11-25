import React, { useState } from 'react';
import './VideosSection.css';

const videos = [
  {
    id: 'SMPI2TLxtKE',
    title: 'Muestreo y Etiquetado',
    description: 'Conoce cómo generar muestras, imprimir adhesivos personalizados y crear diagramas de pallets en PDF.'
  },
  {
    id: 'm8pBcv5S9bQ',
    title: 'Descripción del Lote',
    description: 'Conoce cómo cargar tu archivo plano, registrar certificados y generar la planilla de descripción del lote para el SAG.'
  },
  {
    id: 'eE63m-HRRV4',
    title: 'Validación de SDP',
    description: 'Descubre cómo cargar tu packing list, validar los SDP del lote y obtener un resumen con reporte en PDF.'
  },
  {
    id: '8QZnDQFqEBU',
    title: 'Validación de Cerezas para China',
    description: 'Aprende a consultar códigos CSG y CSP y verificar el cumplimiento de productores y establecimientos.'
  }
];

export default function VideosSection() {
  const [playingVideo, setPlayingVideo] = useState(null);

  return (
    <section className="videos-section" aria-labelledby="videos-title">
      <div className="videos-container">
        <div className="videos-header">
          <h2 id="videos-title">Conoce AgroSample en acción</h2>
          <p>Descubre cómo funcionan nuestros módulos con estos videos explicativos.</p>
        </div>
        <div className="videos-grid">
          {videos.map((video) => (
            <article className="video-card" key={video.id}>
              <div className="video-player">
                {playingVideo === video.id ? (
                  <iframe
                    src={`https://www.youtube-nocookie.com/embed/${video.id}?autoplay=1`}
                    title={`Video: ${video.title}`}
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                    referrerPolicy="strict-origin-when-cross-origin"
                    allowFullScreen
                  />
                ) : (
                  <button
                    type="button"
                    className="video-play-button"
                    aria-label={`Reproducir video: ${video.title}`}
                    onClick={() => setPlayingVideo(video.id)}
                  >
                    <img src={`https://i.ytimg.com/vi/${video.id}/hqdefault.jpg`} alt="" loading="lazy" />
                    <span className="video-play-icon" aria-hidden="true">▶</span>
                  </button>
                )}
              </div>
              <div className="video-details">
                <h3>{video.title}</h3>
                <p>{video.description}</p>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
