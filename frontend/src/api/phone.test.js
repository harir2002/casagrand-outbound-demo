/**
 * Node tests for E.164 phone helpers used by the call form.
 * Run: npm test
 */

import assert from "node:assert/strict";
import { test } from "node:test";
import { isValidE164, normalizePhone, phoneValidationError } from "./phone.js";

test("normalizePhone strips separators", () => {
  assert.equal(normalizePhone(" +91 98765-43210 "), "+919876543210");
  assert.equal(normalizePhone("+1 (555) 123.4567"), "+15551234567");
  assert.equal(normalizePhone(""), "");
});

test("isValidE164 accepts valid numbers", () => {
  assert.equal(isValidE164("+919876543210"), true);
  assert.equal(isValidE164("+15551234567"), true);
  assert.equal(isValidE164("+44 20 7946 0958"), true);
});

test("isValidE164 rejects invalid numbers", () => {
  assert.equal(isValidE164(""), false);
  assert.equal(isValidE164("9876543210"), false); // missing +
  assert.equal(isValidE164("+0123456789"), false); // leading 0 after +
  assert.equal(isValidE164("+91"), false); // too short
  assert.equal(isValidE164("+9198765432101234567"), false); // too long
  assert.equal(isValidE164("+91abc9876"), false); // letters
});

test("phoneValidationError returns human messages", () => {
  assert.equal(phoneValidationError("+919876543210"), null);
  assert.match(phoneValidationError(""), /enter a phone number/i);
  assert.match(phoneValidationError("98765"), /must start with \+/i);
  assert.match(phoneValidationError("+12"), /invalid e\.164/i);
});
