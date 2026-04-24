'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const HipsterShopServer = require('../server');

function getFutureExpiry() {
  const now = new Date();
  return {
    month: now.getMonth() + 1,
    year: now.getFullYear() + 1
  };
}

function buildRequest(cardNumber, expiry = getFutureExpiry()) {
  return {
    amount: {
      currency_code: 'USD',
      units: 20,
      nanos: 0
    },
    credit_card: {
      credit_card_number: cardNumber,
      credit_card_expiration_month: expiry.month,
      credit_card_expiration_year: expiry.year,
      credit_card_cvv: 123
    }
  };
}

test('ChargeServiceHandler passes a successful charge response to the callback', async () => {
  const result = await new Promise((resolve, reject) => {
    HipsterShopServer.ChargeServiceHandler(
      { request: buildRequest('4242424242424242') },
      (error, response) => {
        if (error) {
          reject(error);
          return;
        }

        resolve(response);
      }
    );
  });

  assert.match(
    result.transaction_id,
    /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
  );
});

test('ChargeServiceHandler passes charge validation errors to the callback', async () => {
  const originalWarn = console.warn;
  const warnings = [];
  console.warn = (message) => warnings.push(message);

  try {
    const error = await new Promise((resolve, reject) => {
      HipsterShopServer.ChargeServiceHandler(
        { request: buildRequest('1234567890123456') },
        (callbackError, response) => {
          try {
            assert.equal(response, undefined);
            resolve(callbackError);
          } catch (assertionError) {
            reject(assertionError);
          }
        }
      );
    });

    assert.equal(error.code, 400);
    assert.equal(error.message, 'Credit card info is invalid');
    assert.equal(warnings.length, 1);
  } finally {
    console.warn = originalWarn;
  }
});

test('CheckHandler reports the service as serving', async () => {
  const response = await new Promise((resolve, reject) => {
    HipsterShopServer.CheckHandler({}, (error, result) => {
      if (error) {
        reject(error);
        return;
      }

      resolve(result);
    });
  });

  assert.deepEqual(response, { status: 'SERVING' });
});
