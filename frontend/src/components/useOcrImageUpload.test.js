import { test } from 'node:test';
import assert from 'node:assert/strict';
import { compareOcrReadings, parseOcrNumbers } from './useOcrImageUpload.js';

test('identifica números distintos entre dos lecturas sin mezclarlos', () => {
  const primary = parseOcrNumbers('22 52 848');
  const alternative = parseOcrNumbers('22 92 8438');

  assert.deepEqual(compareOcrReadings(primary, alternative), {
    primaryOnly: [52, 848],
    alternativeOnly: [92, 8438],
  });
  assert.deepEqual(primary, [22, 52, 848]);
});

test('señala un número omitido y no marca lecturas iguales', () => {
  assert.deepEqual(compareOcrReadings([12, 44], [6, 12, 44]), {
    primaryOnly: [],
    alternativeOnly: [6],
  });
  assert.deepEqual(compareOcrReadings([6, 12], [6, 12]), {
    primaryOnly: [],
    alternativeOnly: [],
  });
});
