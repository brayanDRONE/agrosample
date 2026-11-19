# Preparación de despliegue

Este procedimiento no despliega ni modifica producción por sí solo. Ensayarlo
primero en un entorno de prueba con una copia restaurada y anonimizada cuando
sea posible. El frontend es Vite y el backend es Django (`config.wsgi`).

## Antes de desplegar

1. Seleccionar los cambios y migraciones que se publicarán, sin incluir bases de
   datos locales, informes ni credenciales. Desactivar el despliegue automático
   mientras se realiza el respaldo y la migración.
2. Respaldar PostgreSQL y el almacenamiento de `MEDIA_ROOT` con las herramientas
   del proveedor. Verificar los respaldos mediante una restauración en una base y
   almacenamiento aislados; no restaurar sobre producción para probarlos.
3. La migración histórica 0011 ya no crea cuentas con contraseña fija en bases
   nuevas. Esto no cambia usuarios existentes: identificar los administradores
   antiguos y cambiar sus contraseñas de forma segura antes de habilitar acceso.
   No publicar ni transmitir contraseñas en archivos, comandos o registros.
   La protección de tokens por contraseña requiere volver a iniciar sesión
   después del despliegue; los tokens anteriores carecen del dato requerido.
4. Configurar en el backend `DEBUG=False`, `SECRET_KEY` aleatoria y privada,
   `DATABASE_URL` PostgreSQL, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` y
   `CORS_ALLOWED_ORIGINS` con los dominios reales. Configurar `VITE_API_URL` en
   el frontend con la URL HTTPS del backend terminada en `/api`. No incluir
   comodines ni orígenes innecesarios. Los orígenes locales solo se habilitan
   automáticamente con `DEBUG=True`; los dominios oficiales `agrosample.cl`
   y `www.agrosample.cl` se agregan siempre a CORS.
5. Configurar HTTPS en el proveedor y asegurarse de que el proxy confiable
   establezca `X-Forwarded-Proto`. Django exige cookies seguras y redirige HTTP
   cuando `DEBUG=False`. Activar `SECURE_HSTS_SECONDS` solo después de comprobar
   HTTPS y la política del dominio; su valor predeterminado es 0.
6. Configurar almacenamiento persistente para `MEDIA_ROOT`, incluyendo logos y
   archivos históricos. Los PDF nuevos de SDP, planillas y China se guardan en
   PostgreSQL. Revisar la capacidad de la base y respaldarla regularmente.
   Por decisión actual no hay borrado automático; definir y aplicar una política
   de retención antes de que el crecimiento sea un problema. En Render, el
   disco del backend está montado en `/opt/render/project/src/backend/media`
   y tiene 10 GB. Antes de sincronizar el Blueprint, revisar que conserve ese
   disco y sus datos. Los discos no se comparten con el worker, impiden escalar
   a varias instancias y causan una interrupción durante cada despliegue.
7. El acceso público a los archivos históricos de SDP, China y avatares se
   bloquea en Django; verificar también que ningún proxy, bucket o CDN los
   exponga directamente. Conservar los archivos históricos en el respaldo.
   Los informes China históricos que solo existan en disco necesitan que el
   servicio web pueda acceder a ese almacenamiento; los informes nuevos no.

## Migración controlada

Con los servicios apuntando al entorno correcto, respaldo y restauración
verificados, ejecutar desde `backend`:

```bash
python manage.py showmigrations
python manage.py check --deploy
python manage.py migrate --noinput
```

Revisar las advertencias de `check --deploy` y confirmar especialmente HTTPS,
HSTS, hosts y proxy. Los comandos de arranque de este repositorio **no ejecutan
migraciones automáticamente**: deben ejecutarse como paso controlado antes de
iniciar la nueva versión. El worker China debe usar la misma base y arrancar
después de las migraciones.

En Render, las migraciones nuevas deben ejecutarse con el código de la versión
que se publicará; el shell de la versión anterior todavía no las contiene. Para
coordinar el despliegue:

1. Desactivar temporalmente Auto Sync del Blueprint y Auto-Deploy del backend y
   del worker. Verificar los tres ajustes antes del push; uno no sustituye a los
   demás. En Vercel, controlar también las compilaciones: «Don't build
   anything» las omite sin retirar el sitio actual. Restablecer «Automatic» y
   desplegar el commit elegido solo después de comprobar el backend.
2. Con el backend en mantenimiento y el worker detenido tras terminar sus
   tareas, obtener respaldos actualizados de PostgreSQL y del disco de media.
   Comprobar que se pueden recuperar y conservarlos fuera de los servicios.
3. Antes de desplegar el backend, configurar en Render el comando de pre-deploy
   `python manage.py migrate --noinput` y verificar que se use para el commit
   elegido. Render lo ejecuta con el código recién compilado antes del arranque;
   no tiene acceso al disco persistente y debe fallar el despliegue si falla la
   migración. No ejecutar el comando simultáneamente en el worker.
4. Desplegar el backend y comprobar el resultado del pre-deploy y la respuesta
   del servicio. Después desplegar el worker y verificarlo; finalmente comprobar
   el frontend correspondiente antes de quitar el mantenimiento. Las
   migraciones no asignan planes automáticamente: los establecimientos
   existentes no podrán consumir operaciones sujetas a plan hasta que el
   administrador les asigne uno. Coordinar esas asignaciones antes de reabrir
   el acceso a los usuarios.
5. Revisar la sincronización propuesta del Blueprint, especialmente el disco,
   los comandos y los planes. Restablecer los ajustes automáticos solo cuando
   se haya decidido cómo se ejecutarán las migraciones de futuras versiones.

El comando de arranque que esté configurado actualmente en Render puede diferir
del repositorio. Comprobar ambos antes de desplegar: si el arranque existente
también ejecuta `migrate`, este se ejecutará de nuevo después del pre-deploy.
Si el despliegue falla, no restaurar ni revertir la base de producción sin
evaluar los cambios aplicados y el respaldo actualizado.

En una instalación nueva, crear un superusuario con contraseña robusta mediante
el comando interactivo `python manage.py createsuperuser`, y después asignarle
el perfil de AgroSample con `python manage.py create_admin <usuario>`. No se
crea una contraseña predeterminada. En una instalación existente, usar el
procedimiento seguro de cambio de contraseña y comprobar los permisos antes de
habilitar el acceso.

## Verificación posterior

- Confirmar aislamiento entre establecimientos, incluida la lectura y edición
  de inspecciones, resultados y documentos. Las inspecciones históricas sin
  establecimiento son visibles solo para el administrador general; no se
  reasignan automáticamente.
- Comprobar login, asignación manual de planes, consulta SDP, descarga privada,
  informes China y una impresión real con usuarios de prueba.
- Confirmar monitoreo y alertas, copias periódicas y una prueba de recuperación.
  No se han verificado los valores ni los servicios del entorno real.
