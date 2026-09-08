const API_BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/batch-description`
  : (import.meta.env.DEV ? 'http://localhost:8000/api/batch-description' : '/api/batch-description');

export async function validateSdpExcel(file, includeBoxDate = false) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('incluir_caja_fecha', includeBoxDate ? 'true' : 'false');
  const token = localStorage.getItem('access_token');
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await fetch(`${API_BASE_URL}/validate-sdp-excel/`, {
    method: 'POST',
    headers,
    body: formData,
  });
  const data = await response.json();
  if (!response.ok || !data.success) {
    throw new Error(data.message || data.errors?.join(', ') || 'Error al validar el Excel');
  }
  return data;
}