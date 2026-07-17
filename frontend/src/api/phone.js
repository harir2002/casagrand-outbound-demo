/** E.164 phone helpers shared by the call form and tests. */

const E164_RE = /^\+[1-9]\d{7,14}$/;

/** Remove spaces, dashes, dots, parentheses. Keeps leading +. */
export function normalizePhone(raw) {
  return (raw || "").trim().replace(/[\s\-().]/g, "");
}

/** True when the (normalized) value is a valid E.164 number. */
export function isValidE164(raw) {
  return E164_RE.test(normalizePhone(raw));
}

/** Human message for invalid input; null when valid. */
export function phoneValidationError(raw) {
  const value = normalizePhone(raw);
  if (!value) return "Enter a phone number";
  if (!value.startsWith("+")) {
    return "Number must start with + and country code (e.g. +91…)";
  }
  if (!E164_RE.test(value)) {
    return "Invalid E.164 number — expected + followed by 8-15 digits";
  }
  return null;
}
