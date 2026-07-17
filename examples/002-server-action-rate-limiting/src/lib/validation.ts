import { z } from "zod";

/**
 * Input contract for the subscribe action. Validation runs BEFORE any other
 * work (rate limiting excepted — see subscribe.ts for the ordering rationale):
 * nothing downstream ever sees an unvalidated value.
 */
export const subscribeSchema = z.object({
  email: z
    .string()
    .trim()
    .toLowerCase()
    .email("Enter a valid email address")
    // RFC 5321 limit; also caps the cost of any downstream processing.
    .max(254, "Email is too long"),
  // Honeypot: real users never fill this hidden field. Bots that do are
  // rejected with the SAME generic error as validation failures, so the
  // field's purpose is not observable from the response.
  website: z.literal("").optional(),
});

export type SubscribeInput = z.infer<typeof subscribeSchema>;

/**
 * All failures collapse to one generic message. Field-level errors would help
 * a legitimate UI, but this action is a spam target: distinguishing "invalid
 * email" from "honeypot tripped" teaches bots which check they failed.
 * Trade-off documented in DECISIONS.md D005.
 */
export const GENERIC_ERROR = "Could not process the subscription. Check the form and try again.";
