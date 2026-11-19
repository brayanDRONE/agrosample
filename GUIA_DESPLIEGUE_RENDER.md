# Despliegue en Render

Seguir primero [Preparación de despliegue](./DEPLOYMENT.md). No habilitar un
despliegue automático antes de verificar respaldos y migraciones.

El archivo `render.yaml` describe un servicio web y un worker independiente
para informes China. El worker necesita un plan compatible, Chromium y acceso a
la **misma** base PostgreSQL que el servicio web. `DATABASE_URL` se configura
manualmente en ambos servicios; el archivo no crea ni conecta la base por sí
solo. Las credenciales de las fuentes externas también se configuran mediante
variables privadas del proveedor.

Revisar los planes y las opciones de almacenamiento persistente del proveedor:
el sistema de archivos efímero no conserva medios históricos tras reinicios o
despliegues. El frontend requiere `VITE_API_URL` y debe compilarse de nuevo
cuando cambie esa variable.

El arranque del servicio no aplica migraciones. Tras restaurar y verificar el
respaldo en un entorno aislado, aplicar las migraciones de forma controlada y
verificar el backend y el worker antes de habilitar tráfico real.
