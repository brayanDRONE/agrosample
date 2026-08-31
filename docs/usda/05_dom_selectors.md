# DOM y selectores observados

- Login: `#uname`, `#login-submit`, `button.btn-toggle-password`.
- Menú: `#Agendamiento`, `#SolicitarServicio`.
- Lote: checkbox dinámico `input.loteSol`; en esta sesión `id/value=151318` y evento asociado a selección.
- Tipo despacho: `select.bootbox-input.bootbox-input-select`.
- Fecha: `#FechaInspeccion`.
- Sitio: enlaces de sitio; esta sesión seleccionó Teno.
- Hora: enlace padre con `onclick="AceptaAgendamiento(2,166974,'14:15')"`; el icono calendario es hijo, no selector único.
- Confirmación: `#idModalAcepta`, `#muestraHora`, `#btnAcepta`.

El outerHTML sanitizado de cada clic está en `network-trace.json`.
