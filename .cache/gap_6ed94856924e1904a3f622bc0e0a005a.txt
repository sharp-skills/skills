---
name: zod
description: >-
  Assists with TypeScript-first schema validation using Zod. Use when defining data schemas,
  validating API inputs, parsing environment variables, integrating with form libraries or tRPC,
  or generating TypeScript types from runtime validators. Trigger words: zod, schema validation,
  type inference, z.object, z.infer, input validation.
license: Apache-2.0
compatibility: "Requires TypeScript 4.5+"
metadata:
  author: terminal-skills
  version: "1.0.0"
  category: development
  tags: ["zod", "validation", "typescript", "schema", "type-safety"]
---

# Zod

## Overview

Zod provides TypeScript-first schema validation that catches bad data at runtime while providing perfect TypeScript inference at compile time. It is widely used for API input validation, form handling, environment variable parsing, and integration with frameworks like tRPC and React Hook Form.

## Instructions

- When defining schemas, use primitive types (`z.string()`, `z.number()`), object schemas with `.shape`, `.partial()`, `.pick()`, `.omit()`, and compose complex types with `z.union()`, `z.discriminatedUnion()`, and `z.intersection()`.
- When adding refinements, apply built-in validators like `.email()`, `.url()`, `.min()`, `.max()` and use `.refine()` or `.superRefine()` for custom cross-field validation logic.
- When transforming data, chain `.transform()` for parsing and reshaping, use `z.coerce.number()` for type coercion, and `.default()` for optional fields with fallbacks.
- When extracting types, use `z.infer<typeof schema>` for output types and `z.input<typeof schema>` for pre-transform types, and export both the schema and its type together.
- When handling errors, use `ZodError` with `.flatten()` for field-level error maps in API responses and `.format()` for nested error structures.
- When integrating with forms, use `@hookform/resolvers/zod` for React Hook Form or equivalent adapters for other form libraries.
- When validating environment variables, create a schema for `process.env` and validate at app startup to fail fast on missing config.

## Examples

### Example 1: Validate API request bodies

**User request:** "Add Zod validation for my user creation endpoint"

**Actions:**
1. Define `CreateUserInput` schema with `z.object()` including email, name, and role fields
2. Add string refinements (`.email()`, `.min()`) and enum validation for role
3. Export inferred type: `type CreateUserInput = z.infer<typeof CreateUserInputSchema>`
4. Parse request body with `.safeParse()` and return flattened errors on failure

**Output:** A validated, type-safe user creation schema with descriptive error messages.

### Example 2: Parse environment variables at startup

**User request:** "Validate my app's environment variables with Zod"

**Actions:**
1. Define env schema with `z.object()` for all required variables
2. Use `z.coerce.number()` for PORT and `.url()` for API endpoints
3. Add `.default()` for optional variables with fallback values
4. Parse `process.env` at app startup and fail fast with clear error messages

**Output:** Type-safe environment config that crashes early with descriptive errors on missing variables.

## Guidelines

- Always export both the schema and its inferred type together.
- Use descriptive schema names: `CreateUserInput`, `UpdateOrderPayload`, `ApiResponse`.
- Prefer `z.discriminatedUnion()` over `z.union()` for tagged unions for better error messages and performance.
- Use `.describe()` on schemas for documentation generation.
- Place shared schemas in a `schemas/` directory; co-locate route-specific schemas with their handlers.
- Validate environment variables at app startup and fail fast on missing config.
- Use `.strip()` or `.passthrough()` explicitly on object schemas to control unknown key behavior.
