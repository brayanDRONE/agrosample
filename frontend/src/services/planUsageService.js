import { apiService } from './api';

export async function withPlanUsage(operation, action) {
  let reservationId;
  try {
    reservationId = await apiService.reservePlanUsage(operation);
  } catch (error) {
    throw new Error(error.response?.data?.message || 'No se pudo autorizar el uso del plan.');
  }

  if (operation === 'print' && reservationId !== null) {
    try {
      await apiService.dispatchPlanPrint(reservationId);
    } catch (error) {
      throw new Error('No se pudo confirmar la autorización de impresión. El uso podría quedar registrado; contacta al administrador antes de repetir.');
    }
  }

  let result;
  try {
    result = await action();
  } catch (error) {
    if (reservationId !== null) {
      try {
        await apiService.finishPlanUsage(reservationId, error.planUsageUncertain === true);
      } catch {
        throw new Error(`${error.message}. No se pudo confirmar el estado del uso; contacta al administrador.`);
      }
    }
    throw error;
  }

  if (reservationId !== null) {
    try {
      await apiService.finishPlanUsage(reservationId, true);
    } catch {
      throw new Error('La acción se completó, pero no se pudo registrar el uso. Contacta al administrador antes de repetirla.');
    }
  }
  return result;
}
