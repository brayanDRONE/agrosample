# Área y horarios

Request observado:

`POST /SolicitudServicio/AreaInspeccionHorario`

Payload observado: `idSolicitudServicio=0`, `idSitio=156`, `fechaInspeccion=25-08-2026`, `loteSel[]=151318`, `esSinHora=False`.

Response: HTML con `Area B`, código de área `2`, y una hora disponible `14:15` con código `166974`. La acción visible fue `AceptaAgendamiento(2,166974,'14:15')`.
