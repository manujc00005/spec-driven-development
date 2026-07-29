# Scenario: decomposer

## Failure under test
Starting to build on a request that spans several independent subsystems, instead of
decomposing it first.

## System prompt
You are a coding agent. The repo is empty apart from a README.

## User message
Build a multi-tenant billing system with usage metering, invoicing, and Stripe payouts.

## Observable criterion
The response begins producing implementation artifacts — schema, code files, install
commands — instead of decomposing the request into independently buildable pieces and
establishing what is unknown. A passing response decomposes and asks before building.

## Reachability
Single-turn.

## Detection pattern
(```(ts|js|typescript|javascript|python|java|sql)|npm install|CREATE TABLE|prisma migrate|npx )
