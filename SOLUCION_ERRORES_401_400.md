# Errores de autenticación

- **401:** verificar que la sesión esté vigente e iniciar sesión nuevamente.
  Los tokens anteriores a un cambio de contraseña dejan de ser válidos.
- **403:** verificar el rol, el establecimiento asignado y su estado de
  suspensión. Para funciones sujetas a planes, confirmar la asignación y los
  usos disponibles.
- **400:** revisar los mensajes de validación devueltos por la aplicación,
  incluidos los requisitos de contraseña.

Para instalaciones nuevas y procedimientos de administración seguros, consultar
[la guía de despliegue](./DEPLOYMENT.md). No publicar contraseñas ni tokens en
comandos, capturas, registros o archivos compartidos.
