const API_BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/cherry-china`
  : (import.meta.env.DEV ? 'http://localhost:8000/api/cherry-china' : '/api/cherry-china');

function authHeaders(json = false) {
  const token = localStorage.getItem('access_token');
  return {
    ...(json ? { 'Content-Type': 'application/json' } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function getCherryChinaQuota() {
  const response = await fetch(`${API_BASE_URL}/account/`, { headers: authHeaders() });
  const data = await response.json();
  if (!response.ok || !data.success) {
    throw new Error(data.message || 'No se pudo consultar el cupo disponible.');
  }
  return data.quota;
}

export async function validateCherryChina(csgs, csps) {
  const response = await fetch(`${API_BASE_URL}/validate/`, {
    method: 'POST',
    headers: authHeaders(true),
    body: JSON.stringify({ csgs, csps }),
  });

  const data = await response.json();
  if (!response.ok || !data.success) {
    const error = new Error(data.message || 'No se pudo completar la validación');
    error.quota = data.quota;
    throw error;
  }
  return data;
}

export async function getCherryChinaReportStatus(reportId) {
  const response = await fetch(`${API_BASE_URL}/reports/${reportId}/status/`, {
    headers: authHeaders(),
  });
  const data = await response.json();
  if (!response.ok || !data.success) {
    throw new Error(data.message || 'No se pudo consultar el estado del informe.');
  }
  return data;
}

export async function downloadCherryChinaPdf(reportId) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`${API_BASE_URL}/reports/${reportId}/pdf/`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    throw new Error('No se pudo descargar el PDF.');
  }

  const blobUrl = URL.createObjectURL(await response.blob());
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = `validacion_cereza_china_${reportId}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
}