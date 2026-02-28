---
name: drizzle-orm
description: "Drizzle ORM is a lightweight, type-safe TypeScript ORM for PostgreSQL, MySQL, and SQLite (including serverless databases like Neon, Turso, PlanetScale, Supabase, and Cloudflare D1). Use when asked to: set up a TypeScript ORM for a Node.js project, define database schemas with full type safety, write SQL-like queries in TypeScript, generate and run database migrations, connect to serverless or edge databases, replace Prisma or TypeORM with something lighter, use Drizzle with Next.js or Remix, query relational data with joins."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: database
  tags: [drizzle, orm, typescript, postgresql, mysql, sqlite, migrations, serverless]
---

# Drizzle ORM Skill

## Quick Start

```bash
npm install drizzle-orm
npm install -D drizzle-kit
# Pick your driver: pg | mysql2 | better-sqlite3 | @libsql/client etc.
npm install pg
npm install -D @types/pg
```

```typescript
// drizzle.config.ts
import { defineConfig } from "drizzle-kit";

export default defineConfig({
  schema: "./src/db/schema.ts",
  out: "./drizzle",
  dialect: "postgresql",
  dbCredentials: { url: process.env.DATABASE_URL! },
});
```

```typescript
// src/db/schema.ts
import { pgTable, serial, text, integer, timestamp } from "drizzle-orm/pg-core";
import { relations } from "drizzle-orm";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  email: text("email").notNull().unique(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const posts = pgTable("posts", {
  id: serial("id").primaryKey(),
  title: text("title").notNull(),
  body: text("body"),
  authorId: integer("author_id").references(() => users.id).notNull(),
});

export const usersRelations = relations(users, ({ many }) => ({
  posts: many(posts),
}));

export const postsRelations = relations(posts, ({ one }) => ({
  author: one(users, { fields: [posts.authorId], references: [users.id] }),
}));
```

```typescript
// src/db/client.ts
import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as schema from "./schema";

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
export const db = drizzle(pool, { schema });
```

```bash
# Generate + apply migrations
npx drizzle-kit generate
npx drizzle-kit migrate
# Or push schema directly (dev only)
npx drizzle-kit push
```

## When to Use

Use this skill when asked to:
- Set up or configure Drizzle ORM in a TypeScript/Node.js project
- Define database tables and schemas with type safety
- Write queries (select, insert, update, delete) using Drizzle's query builder
- Use relational queries (`db.query.users.findMany`) with nested relations
- Generate, apply, or manage database migrations with `drizzle-kit`
- Connect Drizzle to serverless databases (Neon, Turso, PlanetScale, Supabase, D1)
- Debug migration errors, snapshot corruption, or `drizzle-kit push` failures
- Infer TypeScript types from Drizzle schema definitions
- Replace Prisma or TypeORM with a lighter ORM
- Use Drizzle inside Next.js API routes, Remix loaders, or Cloudflare Workers

## Core Patterns

### Pattern 1: SQL-Like Query Builder (Source: official)

Full CRUD using the low-level SQL-like API — best when you need precise control.

```typescript
import { db } from "./db/client";
import { users, posts } from "./db/schema";
import { eq, and, like, desc, sql } from "drizzle-orm";

// SELECT with filter
const activeUsers = await db
  .select()
  .from(users)
  .where(like(users.email, "%@example.com"))
  .orderBy(desc(users.createdAt))
  .limit(10);

// INSERT returning the new row
const [newUser] = await db
  .insert(users)
  .values({ name: "Alice", email: "alice@example.com" })
  .returning();

// UPDATE
await db
  .update(users)
  .set({ name: "Alice Smith" })
  .where(eq(users.id, newUser.id));

// DELETE
await db.delete(users).where(eq(users.id, newUser.id));

// JOIN
const result = await db
  .select({ userName: users.name, postTitle: posts.title })
  .from(posts)
  .innerJoin(users, eq(posts.authorId, users.id))
  .where(eq(users.id, 1));
```

### Pattern 2: Relational Query Builder (Source: official)

Use `db.query.*` (RQB) for nested, relation-aware queries — requires `relations` defined in schema.

```typescript
import { db } from "./db/client";

// Find user with all their posts
const userWithPosts = await db.query.users.findFirst({
  where: (users, { eq }) => eq(users.id, 1),
  with: {
    posts: {
      orderBy: (posts, { desc }) => [desc(posts.id)],
      limit: 5,
    },
  },
});

// Find many users, include only specific post fields
const usersWithPostTitles = await db.query.users.findMany({
  columns: { id: true, name: true, email: true },
  with: {
    posts: {
      columns: { title: true },
    },
  },
});
```

### Pattern 3: Type Inference from Schema (Source: official)

Derive insert/select TypeScript types directly from table definitions.

```typescript
import { InferSelectModel, InferInsertModel } from "drizzle-orm";
import { users, posts } from "./db/schema";

// Full row type (from SELECT)
type User = InferSelectModel<typeof users>;
// Insert type (required vs optional columns respected)
type NewUser = InferInsertModel<typeof users>;

// Partial update helper
type UserUpdate = Partial<NewUser>;

// Runtime usage with full type safety
async function createUser(data: NewUser): Promise<User> {
  const [user] = await db.insert(users).values(data).returning();
  return user;
}
```

### Pattern 4: Drizzle with Serverless (Neon / Turso) (Source: official)

```typescript
// Neon (PostgreSQL serverless)
import { drizzle } from "drizzle-orm/neon-http";
import { neon } from "@neondatabase/serverless";

const sql = neon(process.env.DATABASE_URL!);
export const db = drizzle(sql);

// Turso (SQLite edge)
import { drizzle } from "drizzle-orm/libsql";
import { createClient } from "@libsql/client";

const client = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN,
});
export const db = drizzle(client);
```

### Pattern 5: Transactions (Source: official)

```typescript
import { db } from "./db/client";
import { users, posts } from "./db/schema";

const result = await db.transaction(async (tx) => {
  const [author] = await tx
    .insert(users)
    .values({ name: "Bob", email: "bob@example.com" })
    .returning();

  const [post] = await tx
    .insert(posts)
    .values({ title: "Hello", authorId: author.id })
    .returning();

  return { author, post };
});
```

### Pattern 6: Migrations in Production (Source: official)

```typescript
// src/db/migrate.ts — run once on deploy
import { drizzle } from "drizzle-orm/node-postgres";
import { migrate } from "drizzle-orm/node-postgres/migrator";
import { Pool } from "pg";

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
const db = drizzle(pool);

await migrate(db, { migrationsFolder: "./drizzle" });
await pool.end();
```

```bash
# package.json scripts
"db:generate": "drizzle-kit generate",
"db:migrate":  "tsx src/db/migrate.ts",
"db:push":     "drizzle-kit push",   # dev only — destructive!
"db:studio":   "drizzle-kit studio"
```

### Pattern 7: Error Handling for Unique Constraints (Source: community)

```typescript
import { db } from "./db/client";
import { users } from "./db/schema";

// Source: community
// Tested: SharpSkill
async function safeCreateUser(name: string, email: string) {
  try {
    const [user] = await db
      .insert(users)
      .values({ name, email })
      .returning();
    return { user, error: null };
  } catch (err: any) {
    // PostgreSQL unique violation code
    if (err?.code === "23505") {
      return { user: null, error: "Email already exists" };
    }
    throw err;
  }
}
```

### Pattern 8: Optional Fields on Update (Source: community)

Fix for TypeScript error on optional fields during `update().set()` — a known issue in drizzle-orm ≤ 0.32.

```typescript
// Source: community — workaround for TS error on optional column updates
// Tested: SharpSkill
import { db } from "./db/client";
import { posts } from "./db/schema";
import { eq, sql } from "drizzle-orm";

// Problem: TypeScript may reject `undefined` values in .set()
// Fix: use explicit cast or sql`` tag for nullable/optional fields
await db
  .update(posts)
  .set({
    body: sql`${body ?? null}`, // explicit null instead of undefined
  })
  .where(eq(posts.id, postId));
```

## Production Notes

**1. Never use `drizzle-kit push` in production**
`push` directly mutates the database schema without generating a migration file. This skips history tracking and can cause irreversible data loss. Use `drizzle-kit generate` + `migrate()` in production pipelines.
Source: GitHub Issues (community, multiple threads)

**2. Enum label conflicts on `push` with PostgreSQL**
When renaming or adding values to a PostgreSQL `pgEnum`, `drizzle-kit push` may throw `ERROR: enum label already exists`. This occurs because Drizzle does not detect existing enum values before attempting to add them. Workaround: add enum values manually via raw SQL (`ALTER TYPE ... ADD VALUE`), then re-run push.
Source: GitHub Issues #BUG (73 comments)

**3. `compositePrimaryKeys` undefined crash in `drizzle-kit push`**
Occurs when renaming columns or adding tables alongside schema changes when the schema has no composite primary keys defined. The introspection code dereferences an undefined object. Fix: ensure you're on drizzle-kit ≥ 0.21.3 and avoid mixing rename + add operations in one push. Use generate+migrate instead.
Source: GitHub Issues #BUG (70 comments)

**4. Table alias length limit with deeply nested relational queries**
Drizzle generates SQL aliases by concatenating relation names (`table1_table2_table3_...`). PostgreSQL identifier limit is 63 bytes — aliases beyond that are silently truncated, causing ambiguous column errors. Fix: keep relation chain depth ≤ 4, or use the SQL query builder with explicit aliases for deep joins.
Source: GitHub Issues #BUG (42 comments)

**5. Snapshot corruption after interrupted `generate`**
If `drizzle/meta/0000_snapshot.json` becomes malformed (e.g., interrupted write), all subsequent `generate` calls fail. Fix: delete the broken snapshot file, run `drizzle-kit generate` fresh. Back up the `drizzle/` folder in version control — treat it like source code.
Source: GitHub Issues #BUG (43 comments)

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `TypeError: Cannot read properties of undefined (reading 'compositePrimaryKeys')` | drizzle-kit introspection bug when schema has no composite PKs and columns are renamed | Upgrade drizzle-kit; use `generate` + `migrate` instead of `push` |
| `ERROR: enum label already exists` on `push` | Drizzle doesn't check existing PostgreSQL enum values before ALTER | Add new enum values manually via `ALTER TYPE ... ADD VALUE IF NOT EXISTS` |
| TypeScript error on `.set({ optionalField: value })` in `update()` | drizzle-orm ≤ 0.32 optional column type inference bug | Use `sql\`${value ?? null}\`` or upgrade to latest drizzle-orm |
| `snapshot.json data is malformed` | Corrupted migration snapshot from interrupted `generate` | Delete the bad snapshot, re-run `drizzle-kit generate` |
| Nested relational query returns wrong columns / ambiguous error | SQL alias exceeds 63-char PostgreSQL limit in deep relation chains | Limit nesting depth or use explicit SQL joins with short aliases |
| `react@18.2.0` peer dependency conflict on install | drizzle-orm pinned outdated React peer dep | Use `--legacy-peer-deps` flag or upgrade to latest drizzle-orm |
| `drizzle-kit generate:pg` command not found after upgrade | drizzle-kit ≥ 0.19 changed CLI syntax — old `generate:pg` is removed | Use `drizzle-kit generate` (dialect inferred from config) |

## Pre-Deploy Checklist

- [ ] `DATABASE_URL` (and any auth tokens for serverless DBs) set in environment secrets — never hardcoded
- [ ] Migration files in `./drizzle` committed to version control and reviewed before deploy
- [ ] `db:migrate` script runs `migrate()` programmatically on deploy — NOT `drizzle-kit push`
- [ ] All `pgEnum` additions tested against existing DB; use `ADD VALUE IF NOT EXISTS` for manual additions
- [ ] Relation depth audited — alias chains stay under ~50 chars to avoid PostgreSQL 63-byte limit
- [ ] `drizzle-orm` and `drizzle-kit` versions pinned to matching major versions (they must be in sync)
- [ ] Connection pool configured appropriately for serverless: use `neon-http` or `libsql` adapters, not `node-postgres` pool in edge environments

## Troubleshooting

**Error: `TypeError: Cannot read properties of undefined (reading 'compositePrimaryKeys')`**
Cause: drizzle-kit bug when introspecting schemas without composite primary keys during a push that includes column renames.
Fix: Upgrade `drizzle-kit` to latest. Separate schema changes into individual steps. Switch to `drizzle-kit generate` + `migrate()`.

**Error: `snapshot.json data is malformed`**
Cause: The migration snapshot was corrupted, usually by an interrupted write or manual edit.
Fix: Delete `drizzle/meta/0000_snapshot.json` (back it up first). Run `npx drizzle-kit generate` to recreate. Commit the `drizzle/` directory to git to prevent recurrence.

**Error: `There is not enough information to infer relation` (Drizzle Studio / RQB)**
Cause: `relations()` definitions in schema are not passed to the `drizzle()` client constructor.
Fix: Pass your schema to `drizzle(client, { schema })` — the second argument is required for RQB and Studio to resolve relations.

**Error: `Object literal may only specify known properties` on column definition**
Cause: Breaking change in drizzle-orm 0.32 / drizzle-kit 0.23 tightened column option types