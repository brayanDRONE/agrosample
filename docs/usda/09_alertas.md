# Alertas y autenticación

Se observaron requests a `Notificacion/TotalNotificacion/` y `Home/ObtenerSancionAlerta` después del login. La sesión también pasó por SAG/ClaveÚnica.

Los clics incluyeron botones `Aceptar` de modales. El trace registra su orden y URL, pero no conserva contraseñas, cookies, tokens ni session IDs.
