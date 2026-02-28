# SharpSkills

An open-source library of AI agent skills following the [Agent Skills](https://agentskills.io) open standard. Every skill is automatically L1→L4 tested before publish. Works across Claude Code, OpenAI Codex, Gemini CLI, Cursor, and other AI-powered development tools.

**Philosophy:** Quality over quantity. Every skill passes L1→L4 testing before publish.

## Install a Skill

### Claude Code
```bash
curl -sL https://raw.githubusercontent.com/sharp-skills/skills/main/skills/{skill-name}/SKILL.md -o .claude/skills/{skill-name}.md
```

### Gemini CLI
```bash
curl -sL https://raw.githubusercontent.com/sharp-skills/skills/main/skills/{skill-name}/SKILL.md -o .gemini/skills/{skill-name}.md
```

### Cursor
```bash
curl -sL https://raw.githubusercontent.com/sharp-skills/skills/main/skills/{skill-name}/SKILL.md -o .cursor/skills/{skill-name}.md
```

## Skills Catalog (161 skills)

| Skill | Category | Description |
|---|---|---|
| [algolia](skills/algolia/SKILL.md) | 🛠 Dev | Work with algolia — integrate, configure, and automate |
| [ansible](skills/ansible/SKILL.md) | 🛠 Dev | Work with ansible — integrate, configure, and automate |
| [anthropic](skills/anthropic/SKILL.md) | 🤖 AI/ML | Integrates with the Anthropic Claude API to send messages, stream responses, handle mul... |
| [argocd](skills/argocd/SKILL.md) | 🛠 Dev | Work with argocd — integrate, configure, and automate |
| [auth0](skills/auth0/SKILL.md) | 🛠 Dev | Work with auth0 — integrate, configure, and automate |
| [aws-cloudwatch](skills/aws-cloudwatch/SKILL.md) | ⚙️ DevOps | Puts custom metrics into AWS CloudWatch using a simple wrapper around putMetricData |
| [aws-cognito](skills/aws-cognito/SKILL.md) | 🛠 Dev | Work with aws-cognito — integrate, configure, and automate |
| [aws-dynamodb](skills/aws-dynamodb/SKILL.md) | 🗄 Database | Production-grade AWS DynamoDB patterns with exponential backoff, VPC endpoints, IAM lea... |
| [aws-ec2](skills/aws-ec2/SKILL.md) | ⚙️ DevOps | Manages AWS EC2 instances with production-grade security and performance hardening |
| [aws-iam](skills/aws-iam/SKILL.md) | 🛠 Dev | Work with aws-iam — integrate, configure, and automate |
| [aws-lambda](skills/aws-lambda/SKILL.md) | 🛠 Dev | Work with aws-lambda — integrate, configure, and automate |
| [aws-s3](skills/aws-s3/SKILL.md) | ⚙️ DevOps | Production-depth AWS S3 skill covering request rate limits and prefix partitioning, mul... |
| [aws-sdk](skills/aws-sdk/SKILL.md) | 🛠 Dev | Work with aws-sdk — integrate, configure, and automate |
| [aws-sdk-rds](skills/aws-sdk-rds/SKILL.md) | 🛠 Dev | Work with aws-sdk-rds — integrate, configure, and automate |
| [aws-sns](skills/aws-sns/SKILL.md) | ⚙️ DevOps | Manages AWS Simple Notification Service for production-grade pub/sub messaging |
| [aws-sqs](skills/aws-sqs/SKILL.md) | 🛠 Dev | Work with aws-sqs — integrate, configure, and automate |
| [axios](skills/axios/SKILL.md) | 🛠 Dev | Work with axios — integrate, configure, and automate |
| [bcrypt](skills/bcrypt/SKILL.md) | 🛠 Dev | Work with bcrypt — integrate, configure, and automate |
| [bull](skills/bull/SKILL.md) | 🛠 Dev | Work with bull — integrate, configure, and automate |
| [celery](skills/celery/SKILL.md) | 🛠 Dev | Work with celery — integrate, configure, and automate |
| [cheerio](skills/cheerio/SKILL.md) | 🛠 Dev | Work with cheerio — integrate, configure, and automate |
| [chroma](skills/chroma/SKILL.md) | 🤖 AI/ML | Chroma is the open-source AI-native vector database for building LLM-powered search and... |
| [clerk](skills/clerk/SKILL.md) | 🛠 Dev | Work with clerk — integrate, configure, and automate |
| [cloudflare-workers](skills/cloudflare-workers/SKILL.md) | ⚙️ DevOps | Build, deploy, and harden Cloudflare Workers for production |
| [consul](skills/consul/SKILL.md) | 🛠 Dev | Work with consul — integrate, configure, and automate |
| [cors](skills/cors/SKILL.md) | 🛠 Dev | Work with cors — integrate, configure, and automate |
| [cron](skills/cron/SKILL.md) | 🛠 Dev | Work with cron — integrate, configure, and automate |
| [csv-parse](skills/csv-parse/SKILL.md) | 🛠 Dev | Work with csv-parse — integrate, configure, and automate |
| [cypress](skills/cypress/SKILL.md) | 🛠 Dev | Work with cypress — integrate, configure, and automate |
| [datadog](skills/datadog/SKILL.md) | 🛠 Dev | Work with datadog — integrate, configure, and automate |
| [date-fns](skills/date-fns/SKILL.md) | 🛠 Dev | Work with date-fns — integrate, configure, and automate |
| [dayjs](skills/dayjs/SKILL.md) | 🛠 Dev | Work with dayjs — integrate, configure, and automate |
| [discord-bot](skills/discord-bot/SKILL.md) | 🛠 Dev | Work with discord-bot — integrate, configure, and automate |
| [docker](skills/docker/SKILL.md) | ⚙️ DevOps | Manages Docker containers, images, networks, and volumes using the Docker Engine API an... |
| [docker-compose](skills/docker-compose/SKILL.md) | 🛠 Dev | Work with docker-compose — integrate, configure, and automate |
| [dotenv](skills/dotenv/SKILL.md) | 🛠 Dev | Work with dotenv — integrate, configure, and automate |
| [drizzle-orm](skills/drizzle/SKILL.md) | 🗄 Database | Drizzle ORM is a lightweight, type-safe TypeScript ORM for PostgreSQL, MySQL, and SQLit... |
| [elasticsearch](skills/elasticsearch/SKILL.md) | 🗄 Database | Connects to Elasticsearch clusters and performs full-text search, document indexing, qu... |
| [eslint](skills/eslint/SKILL.md) | 🛠 Dev | Work with eslint — integrate, configure, and automate |
| [etcd](skills/etcd/SKILL.md) | 🛠 Dev | Work with etcd — integrate, configure, and automate |
| [exceljs](skills/exceljs/SKILL.md) | 🛠 Dev | Work with exceljs — integrate, configure, and automate |
| [express](skills/express/SKILL.md) | 🛠 Dev | Work with express — integrate, configure, and automate |
| [fastapi-production](skills/fastapi/SKILL.md) | 🛠 Dev | Production-depth skill for building robust FastAPI services |
| [fetch-api](skills/fetch-api/SKILL.md) | 🛠 Dev | Work with fetch-api — integrate, configure, and automate |
| [ffmpeg](skills/ffmpeg/SKILL.md) | 🛠 Dev | Work with ffmpeg — integrate, configure, and automate |
| [firebase](skills/firebase/SKILL.md) | 🗄 Database | Integrates Firebase services (Authentication, Firestore, Realtime Database, Storage, Cl... |
| [github-actions](skills/github-actions/SKILL.md) | 🛠 Dev | Work with github-actions — integrate, configure, and automate |
| [github-cli](skills/github-cli/SKILL.md) | 🛠 Dev | Work with github-cli — integrate, configure, and automate |
| [gitlab-ci](skills/gitlab-ci/SKILL.md) | 🛠 Dev | Work with gitlab-ci — integrate, configure, and automate |
| [google-cloud-storage](skills/google-cloud-storage/SKILL.md) | 🛠 Dev | Work with google-cloud-storage — integrate, configure, and automate |
| [got](skills/got/SKILL.md) | 🛠 Dev | Work with got — integrate, configure, and automate |
| [grafana](skills/grafana/SKILL.md) | 🛠 Dev | Work with grafana — integrate, configure, and automate |
| [graphql](skills/graphql/SKILL.md) | 🛠 Dev | Work with graphql — integrate, configure, and automate |
| [grpc](skills/grpc/SKILL.md) | 🛠 Dev | Work with grpc — integrate, configure, and automate |
| [helm](skills/helm/SKILL.md) | 🛠 Dev | Work with helm — integrate, configure, and automate |
| [helmet](skills/helmet/SKILL.md) | 🛠 Dev | Work with helmet — integrate, configure, and automate |
| [hono](skills/hono/SKILL.md) | 🛠 Dev | Work with hono — integrate, configure, and automate |
| [husky](skills/husky/SKILL.md) | 🛠 Dev | Work with husky — integrate, configure, and automate |
| [ioredis](skills/ioredis/SKILL.md) | 🛠 Dev | Work with ioredis — integrate, configure, and automate |
| [jaeger](skills/jaeger/SKILL.md) | 🛠 Dev | Work with jaeger — integrate, configure, and automate |
| [jest](skills/jest/SKILL.md) | 🛠 Dev | Work with jest — integrate, configure, and automate |
| [jira](skills/jira/SKILL.md) | 🛠 Dev | Work with jira — integrate, configure, and automate |
| [jsonwebtoken](skills/jsonwebtoken/SKILL.md) | 🛠 Dev | Work with jsonwebtoken — integrate, configure, and automate |
| [jwt](skills/jwt/SKILL.md) | 🛠 Dev | Work with jwt — integrate, configure, and automate |
| [kafka](skills/kafka/SKILL.md) | 🛠 Dev | Work with kafka — integrate, configure, and automate |
| [keycloak](skills/keycloak/SKILL.md) | 🛠 Dev | Work with keycloak — integrate, configure, and automate |
| [knex](skills/knex/SKILL.md) | 🛠 Dev | Work with knex — integrate, configure, and automate |
| [kubernetes](skills/kubernetes/SKILL.md) | ⚙️ DevOps | Manages containerized application orchestration using Kubernetes (K8s) |
| [langchain](skills/langchain/SKILL.md) | 🛠 Dev | Work with langchain — integrate, configure, and automate |
| [linear](skills/linear/SKILL.md) | 🛠 Dev | Work with linear — integrate, configure, and automate |
| [llamaindex](skills/llamaindex/SKILL.md) | 🛠 Dev | Work with llamaindex — integrate, configure, and automate |
| [lodash](skills/lodash/SKILL.md) | 🛠 Dev | Work with lodash — integrate, configure, and automate |
| [loki](skills/loki/SKILL.md) | 🛠 Dev | Work with loki — integrate, configure, and automate |
| [lucia-auth](skills/lucia-auth/SKILL.md) | 🛠 Dev | Work with lucia-auth — integrate, configure, and automate |
| [mailgun](skills/mailgun/SKILL.md) | 🛠 Dev | Work with mailgun — integrate, configure, and automate |
| [meilisearch](skills/meilisearch/SKILL.md) | 🛠 Dev | Work with meilisearch — integrate, configure, and automate |
| [memcached](skills/memcached/SKILL.md) | 🛠 Dev | Work with memcached — integrate, configure, and automate |
| [minio](skills/minio/SKILL.md) | 🛠 Dev | Work with minio — integrate, configure, and automate |
| [mongodb](skills/mongodb/SKILL.md) | 🗄 Database | Provides production-grade MongoDB patterns for Node |
| [mongoose](skills/mongoose/SKILL.md) | 🛠 Dev | Work with mongoose — integrate, configure, and automate |
| [morgan](skills/morgan/SKILL.md) | 🛠 Dev | Work with morgan — integrate, configure, and automate |
| [multer](skills/multer/SKILL.md) | 🛠 Dev | Work with multer — integrate, configure, and automate |
| [mysql](skills/mysql/SKILL.md) | 🗄 Database | Production-grade MySQL integration for Node |
| [neon](skills/neon/SKILL.md) | 🛠 Dev | Work with neon — integrate, configure, and automate |
| [nestjs](skills/nestjs/SKILL.md) | 🛠 Dev | Work with nestjs — integrate, configure, and automate |
| [netlify](skills/netlify/SKILL.md) | 🛠 Dev | Work with netlify — integrate, configure, and automate |
| [nextauth](skills/nextauth/SKILL.md) | 🛠 Dev | Work with nextauth — integrate, configure, and automate |
| [nextjs](skills/nextjs/SKILL.md) | 🛠 Dev | Work with nextjs — integrate, configure, and automate |
| [nginx](skills/nginx/SKILL.md) | 🛠 Dev | Work with nginx — integrate, configure, and automate |
| [nginx-config](skills/nginx-config/SKILL.md) | 🛠 Dev | Work with nginx-config — integrate, configure, and automate |
| [nodemailer](skills/nodemailer/SKILL.md) | 🛠 Dev | Work with nodemailer — integrate, configure, and automate |
| [notion-api](skills/notion-api/SKILL.md) | 🛠 Dev | Work with notion-api — integrate, configure, and automate |
| [oauth2](skills/oauth2/SKILL.md) | 🛠 Dev | Work with oauth2 — integrate, configure, and automate |
| [okta](skills/okta/SKILL.md) | 🛠 Dev | Work with okta — integrate, configure, and automate |
| [openai](skills/openai/SKILL.md) | 🛠 Dev | Work with openai — integrate, configure, and automate |
| [opentelemetry](skills/opentelemetry/SKILL.md) | 🛠 Dev | Work with opentelemetry — integrate, configure, and automate |
| [passport](skills/passport/SKILL.md) | 🛠 Dev | Work with passport — integrate, configure, and automate |
| [paypal](skills/paypal/SKILL.md) | 🛠 Dev | Work with paypal — integrate, configure, and automate |
| [pdf-lib](skills/pdf-lib/SKILL.md) | 🛠 Dev | Work with pdf-lib — integrate, configure, and automate |
| [pg](skills/pg/SKILL.md) | 🛠 Dev | Work with pg — integrate, configure, and automate |
| [pinecone](skills/pinecone/SKILL.md) | 🗄 Database | Production-grade vector database skill for Pinecone |
| [pino](skills/pino/SKILL.md) | 🛠 Dev | Work with pino — integrate, configure, and automate |
| [plaid](skills/plaid/SKILL.md) | 🛠 Dev | Work with plaid — integrate, configure, and automate |
| [planetscale](skills/planetscale/SKILL.md) | 🛠 Dev | Work with planetscale — integrate, configure, and automate |
| [playwright](skills/playwright/SKILL.md) | 🛠 Dev | Work with playwright — integrate, configure, and automate |
| [pm2](skills/pm2/SKILL.md) | 🛠 Dev | Work with pm2 — integrate, configure, and automate |
| [postgresql](skills/postgresql/SKILL.md) | 🗄 Database | Production-depth PostgreSQL operations skill covering connection pooling with PgBouncer... |
| [prettier](skills/prettier/SKILL.md) | 🛠 Dev | Work with prettier — integrate, configure, and automate |
| [prisma-production-depth](skills/prisma/SKILL.md) | 🗄 Database | Production-depth Prisma ORM patterns for Node |
| [prometheus](skills/prometheus/SKILL.md) | 🛠 Dev | Work with prometheus — integrate, configure, and automate |
| [puppeteer](skills/puppeteer/SKILL.md) | 🛠 Dev | Work with puppeteer — integrate, configure, and automate |
| [pusher](skills/pusher/SKILL.md) | 🛠 Dev | Work with pusher — integrate, configure, and automate |
| [pydantic](skills/pydantic/SKILL.md) | 🛠 Dev | Work with pydantic — integrate, configure, and automate |
| [pytest](skills/pytest/SKILL.md) | 🛠 Dev | Work with pytest — integrate, configure, and automate |
| [rabbitmq](skills/rabbitmq/SKILL.md) | 🛠 Dev | Work with rabbitmq — integrate, configure, and automate |
| [rate-limiter-flexible](skills/rate-limiter-flexible/SKILL.md) | 🛠 Dev | Work with rate-limiter-flexible — integrate, configure, and automate |
| [react](skills/react/SKILL.md) | 🛠 Dev | Work with react — integrate, configure, and automate |
| [react-query](skills/react-query/SKILL.md) | 🛠 Dev | Work with react-query — integrate, configure, and automate |
| [redis](skills/redis/SKILL.md) | 🗄 Database | Production-grade Redis client patterns for Node |
| [redis-streams](skills/redis-streams/SKILL.md) | 🛠 Dev | Work with redis-streams — integrate, configure, and automate |
| [redux](skills/redux/SKILL.md) | 🛠 Dev | Work with redux — integrate, configure, and automate |
| [resend](skills/resend/SKILL.md) | 🛠 Dev | Work with resend — integrate, configure, and automate |
| [rest-api](skills/rest-api/SKILL.md) | 🛠 Dev | Work with rest-api — integrate, configure, and automate |
| [sendgrid](skills/sendgrid/SKILL.md) | 🛠 Dev | Sends transactional and bulk email via the Twilio SendGrid Web API v3 |
| [sentry](skills/sentry/SKILL.md) | 🛠 Dev | Work with sentry — integrate, configure, and automate |
| [sequelize](skills/sequelize/SKILL.md) | 🛠 Dev | Work with sequelize — integrate, configure, and automate |
| [sharp](skills/sharp/SKILL.md) | 🛠 Dev | Work with sharp — integrate, configure, and automate |
| [sharp-image](skills/sharp-image/SKILL.md) | 🛠 Dev | Work with sharp-image — integrate, configure, and automate |
| [shopify](skills/shopify/SKILL.md) | 🛠 Dev | Work with shopify — integrate, configure, and automate |
| [slack-api](skills/slack-api/SKILL.md) | 🛠 Dev | Work with slack-api — integrate, configure, and automate |
| [socket-io](skills/socket-io/SKILL.md) | 🛠 Dev | Work with socket-io — integrate, configure, and automate |
| [sqlalchemy](skills/sqlalchemy/SKILL.md) | 🛠 Dev | Work with sqlalchemy — integrate, configure, and automate |
| [sqlite](skills/sqlite/SKILL.md) | 🗄 Database | Production-depth SQLite operations for Node |
| [stripe](skills/stripe/SKILL.md) | 🛠 Dev | Integrates Stripe payment processing into applications using the official Stripe SDK (P... |
| [supabase-production](skills/supabase/SKILL.md) | 🗄 Database | Production-depth Supabase patterns covering connection pooling with PgBouncer, RLS poli... |
| [supertest](skills/supertest/SKILL.md) | 🛠 Dev | Work with supertest — integrate, configure, and automate |
| [telegram-bot](skills/telegram-bot/SKILL.md) | 🛠 Dev | Work with telegram-bot — integrate, configure, and automate |
| [terraform](skills/terraform/SKILL.md) | 🛠 Dev | Work with terraform — integrate, configure, and automate |
| [turso](skills/turso/SKILL.md) | 🛠 Dev | Work with turso — integrate, configure, and automate |
| [twilio-production](skills/twilio/SKILL.md) | 🛠 Dev | Production-grade Twilio integration covering webhook signature validation, retry logic ... |
| [twilio-sms](skills/twilio-sms/SKILL.md) | 🛠 Dev | Work with twilio-sms — integrate, configure, and automate |
| [twilio-voice](skills/twilio-voice/SKILL.md) | 🛠 Dev | Work with twilio-voice — integrate, configure, and automate |
| [typeorm](skills/typeorm/SKILL.md) | 🛠 Dev | Work with typeorm — integrate, configure, and automate |
| [typescript](skills/typescript/SKILL.md) | 🛠 Dev | Work with typescript — integrate, configure, and automate |
| [upstash](skills/upstash/SKILL.md) | 🛠 Dev | Work with upstash — integrate, configure, and automate |
| [uuid](skills/uuid/SKILL.md) | 🛠 Dev | Work with uuid — integrate, configure, and automate |
| [varnish](skills/varnish/SKILL.md) | 🛠 Dev | Work with varnish — integrate, configure, and automate |
| [vault](skills/vault/SKILL.md) | 🛠 Dev | Work with vault — integrate, configure, and automate |
| [vercel](skills/vercel/SKILL.md) | 🛠 Dev | Work with vercel — integrate, configure, and automate |
| [vite](skills/vite/SKILL.md) | 🛠 Dev | Work with vite — integrate, configure, and automate |
| [vitest](skills/vitest/SKILL.md) | 🛠 Dev | Work with vitest — integrate, configure, and automate |
| [vue](skills/vue/SKILL.md) | 🛠 Dev | Work with vue — integrate, configure, and automate |
| [weaviate](skills/weaviate/SKILL.md) | 🗄 Database | Production-grade vector database operations with Weaviate |
| [webpack](skills/webpack/SKILL.md) | 🛠 Dev | Work with webpack — integrate, configure, and automate |
| [websocket](skills/websocket/SKILL.md) | 🛠 Dev | Work with websocket — integrate, configure, and automate |
| [websockets](skills/websockets/SKILL.md) | 🛠 Dev | Work with websockets — integrate, configure, and automate |
| [winston](skills/winston/SKILL.md) | 🛠 Dev | Work with winston — integrate, configure, and automate |
| [woocommerce](skills/woocommerce/SKILL.md) | 🛠 Dev | Work with woocommerce — integrate, configure, and automate |
| [yup](skills/yup/SKILL.md) | 🛠 Dev | Work with yup — integrate, configure, and automate |
| [zod](skills/zod/SKILL.md) | 🛠 Dev | Work with zod — integrate, configure, and automate |
| [zustand](skills/zustand/SKILL.md) | 🛠 Dev | Work with zustand — integrate, configure, and automate |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

Apache-2.0. See [LICENSE](LICENSE).
