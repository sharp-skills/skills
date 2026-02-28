---
name: prisma
description: >-
  Build type-safe database layers with Prisma ORM — schema modeling, migrations,
  queries, relations, transactions, and seeding. Use when tasks involve database
  schema design, type-safe data access in TypeScript/JavaScript, migrating
  between databases, or setting up a data layer for a new project.
license: Apache-2.0
compatibility: "Requires Node.js 16+"
metadata:
  author: terminal-skills
  version: "1.0.0"
  category: development
  tags: ["prisma", "orm", "database", "typescript", "migrations"]
---

# Prisma ORM

Type-safe database toolkit for TypeScript and JavaScript — schema-first, auto-generated client, zero-SQL queries with full type safety.

## Setup

```bash
npm install prisma --save-dev
npm install @prisma/client
npx prisma init  # Creates prisma/schema.prisma and .env
```

Set the database URL in `.env`:

```
DATABASE_URL="postgresql://user:password@localhost:5432/mydb?schema=public"
```

Supported databases: PostgreSQL, MySQL, SQLite, MongoDB, CockroachDB, SQL Server.

## Schema Design

The schema file (`prisma/schema.prisma`) defines your data model. Prisma generates TypeScript types and a query client from it.

```prisma
// prisma/schema.prisma — SaaS application data model

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  role      Role     @default(MEMBER)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  // Relations
  organizationId String
  organization   Organization @relation(fields: [organizationId], references: [id])

  @@index([organizationId])
  @@index([email])
}

model Organization {
  id        String   @id @default(cuid())
  name      String
  slug      String   @unique
  plan      Plan     @default(FREE)
  createdAt DateTime @default(now())

  users User[]

  @@index([slug])
}

enum Role {
  ADMIN
  MEMBER
  VIEWER
}

enum Plan {
  FREE
  PRO
  ENTERPRISE
}
```

## Migrations

```bash
# Create and apply a migration
npx prisma migrate dev --name init

# Apply in production (no interactive prompts)
npx prisma migrate deploy

# Reset database (drop + recreate + seed)
npx prisma migrate reset

# Generate client without migrating (schema-only change)
npx prisma generate
```

## Query Patterns

### CRUD Operations

```typescript
// db.ts — Prisma client singleton (prevents connection leaks in dev)
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };
export const prisma = globalForPrisma.prisma || new PrismaClient();
if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma;
```

```typescript
// user-service.ts — Type-safe user operations

import { prisma } from './db';
import type { User, Prisma } from '@prisma/client';

/** Create a user with organization membership. */
async function createUser(data: {
  email: string;
  name: string;
  organizationId: string;
}): Promise<User> {
  return prisma.user.create({
    data: {
      email: data.email,
      name: data.name,
      organization: { connect: { id: data.organizationId } },
    },
  });
}

/** Find users with filtering, sorting, and pagination. */
async function listUsers(params: {
  orgId: string;
  role?: 'ADMIN' | 'MEMBER' | 'VIEWER';
  search?: string;
  page?: number;
  pageSize?: number;
}) {
  const { orgId, role, search, page = 1, pageSize = 20 } = params;

  const where: Prisma.UserWhereInput = {
    organizationId: orgId,
    ...(role && { role }),
    ...(search && {
      OR: [
        { name: { contains: search, mode: 'insensitive' } },
        { email: { contains: search, mode: 'insensitive' } },
      ],
    }),
  };

  const [users, total] = await prisma.$transaction([
    prisma.user.findMany({
      where,
      orderBy: { createdAt: 'desc' },
      skip: (page - 1) * pageSize,
      take: pageSize,
      include: { organization: true },
    }),
    prisma.user.count({ where }),
  ]);

  return { users, total, pages: Math.ceil(total / pageSize) };
}
```

### Relations and Nested Queries

```typescript
// project-service.ts — Working with relations

/** Create a project with initial tasks in one query. */
async function createProjectWithTasks(orgId: string, data: {
  name: string;
  tasks: Array<{ title: string; priority: number }>;
}) {
  return prisma.project.create({
    data: {
      name: data.name,
      organization: { connect: { id: orgId } },
      tasks: {
        createMany: {
          data: data.tasks.map(t => ({
            title: t.title,
            priority: t.priority,
          })),
        },
      },
    },
    include: {
      tasks: true,           // Return created tasks in response
      organization: true,
    },
  });
}

/** Get project dashboard: task counts by status. */
async function getProjectStats(projectId: string) {
  const stats = await prisma.task.groupBy({
    by: ['status'],
    where: { projectId },
    _count: { status: true },
  });

  return Object.fromEntries(
    stats.map(s => [s.status, s._count.status])
  );
  // Returns: { TODO: 5, IN_PROGRESS: 3, DONE: 12 }
}
```

### Transactions

```typescript
// billing.ts — Atomic operations with transactions

/** Transfer credits between organizations atomically. */
async function transferCredits(fromOrgId: string, toOrgId: string, amount: number) {
  return prisma.$transaction(async (tx) => {
    // Deduct from sender
    const sender = await tx.organization.update({
      where: { id: fromOrgId },
      data: { credits: { decrement: amount } },
    });

    if (sender.credits < 0) {
      throw new Error('Insufficient credits');  // Rolls back entire transaction
    }

    // Add to receiver
    await tx.organization.update({
      where: { id: toOrgId },
      data: { credits: { increment: amount } },
    });

    // Log the transfer
    return tx.creditTransfer.create({
      data: { fromOrgId, toOrgId, amount },
    });
  });
}
```

### Raw SQL (escape hatch)

```typescript
// When Prisma's query builder isn't enough

/** Full-text search with PostgreSQL ts_rank. */
async function searchPosts(query: string) {
  return prisma.$queryRaw`
    SELECT id, title, ts_rank(to_tsvector('english', content), plainto_tsquery(${query})) as rank
    FROM "Post"
    WHERE to_tsvector('english', content) @@ plainto_tsquery(${query})
    ORDER BY rank DESC
    LIMIT 20
  `;
}
```

## Seeding

Run `npx prisma db seed` with a seed script configured in `package.json` (`"prisma": { "seed": "npx tsx prisma/seed.ts" }`). Use `prisma.model.create` with nested `create` to seed related data in one call.

## Guidelines

- Use a singleton pattern for `PrismaClient` in development to prevent connection pool exhaustion during hot reload
- Always add `@@index` for fields used in `where` clauses and foreign keys
- Use `include` and `select` deliberately -- include only the relations you need to avoid N+1-like over-fetching
- Prefer `createMany` over loops of `create` for bulk inserts (single SQL statement)
- Use `$transaction` for operations that must succeed or fail together
- Run `prisma migrate deploy` (not `migrate dev`) in CI/CD and production
- Schema changes that drop columns or tables require careful migration planning -- Prisma warns about destructive changes
- Use `prisma studio` (`npx prisma studio`) for a visual database browser during development
- Add `@updatedAt` to models you want automatic timestamp tracking on
