'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const charge = require('../charge');

const UUID_V4_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function getFutureExpiry() {
  const now = new Date();
  return {
    month: now.getMonth() + 1,
    year: now.getFullYear() + 1
  };
}

function getExpiredExpiry() {
  const now = new Date();
  const month = now.getMonth();

  if (month === 0) {
    return { month: 12, year: now.getFullYear() - 1 };
  }

  return { month, year: now.getFullYear() };
}

function buildRequest(cardNumber, expiry = getFutureExpiry()) {
  return {
    amount: {
      currency_code: 'USD',
      units: 12,
      nanos: 340000000
    },
    credit_card: {
      credit_card_number: cardNumber,
      credit_card_expiration_month: expiry.month,
      credit_card_expiration_year: expiry.year,
      credit_card_cvv: 123
    }
  };
}

test('charge returns a transaction id for accepted VISA cards', () => {
  const response = charge(buildRequest('4242424242424242'));

  assert.match(response.transaction_id, UUID_V4_PATTERN);
});

test('charge returns a transaction id for accepted MasterCard cards', () => {
  const response = charge(buildRequest('5555555555554444'));

  assert.match(response.transaction_id, UUID_V4_PATTERN);
});

test('charge rejects invalid card numbers', () => {
  assert.throws(
    () => charge(buildRequest('1234567890123456')),
    (error) => {
      assert.equal(error.code, 400);
      assert.equal(error.message, 'Credit card info is invalid');
      return true;
    }
  );
});

test('charge rejects unsupported card brands', () => {
  assert.throws(
    () => charge(buildRequest('378282246310005')),
    (error) => {
      assert.equal(error.code, 400);
      assert.equal(
        error.message,
        'Sorry, we cannot process amex credit cards. Only VISA or MasterCard is accepted.'
      );
      return true;
    }
  );
});

test('charge rejects expired cards with the card suffix in the message', () => {
  const expiry = getExpiredExpiry();

  assert.throws(
    () => charge(buildRequest('4242424242424242', expiry)),
    (error) => {
      assert.equal(error.code, 400);
      assert.equal(
        error.message,
        `Your credit card (ending 4242) expired on ${expiry.month}/${expiry.year}`
      );
      return true;
    }
  );
});
