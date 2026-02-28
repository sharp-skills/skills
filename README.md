# SharpSkills

An open-source library of AI agent skills following the [Agent Skills](https://agentskills.io) open standard. Every skill is automatically L1→L4 tested before publish. Works across Claude Code, OpenAI Codex, Gemini CLI, Cursor, and other AI-powered development tools.

**Philosophy:** Quality over quantity. Every skill passes L1→L4 testing before publish.

## Install a Skill

### Claude Code

```bash
npx sharp-skills install stripe
```

Or using curl:

```bash
curl -sL https://raw.githubusercontent.com/sharp-skills/skills/main/skills/{skill-name}/SKILL.md -o .claude/skills/{skill-name}.md
```

### OpenAI Codex

```bash
curl -sL https://raw.githubusercontent.com/sharp-skills/skills/main/skills/{skill-name}/SKILL.md -o .codex/skills/{skill-name}.md
```

### Gemini CLI

```bash
curl -sL https://raw.githubusercontent.com/sharp-skills/skills/main/skills/{skill-name}/SKILL.md -o .gemini/skills/{skill-name}.md
```

### Cursor

```bash
curl -sL https://raw.githubusercontent.com/sharp-skills/skills/main/skills/{skill-name}/SKILL.md -o .cursor/skills/{skill-name}.md
```

Replace  with the skill you want to install.

## Skills Catalog (161 skills)

| Skill | Category | Description |
|-------|----------|-------------|
| [algolia](skills/algolia/) | Development | Work with algolia — integrate, configure, and automate |
| [ansible](skills/ansible/) | Development | Work with ansible — integrate, configure, and automate |
| [anthropic](skills/anthropic/) | AI/ML | Integrates with the Anthropic Claude API to send messages, stream responses, handle mul... |
| [argocd](skills/argocd/) | Development | Work with argocd — integrate, configure, and automate |
| [auth0](skills/auth0/) | Development | Work with auth0 — integrate, configure, and automate |
| [aws-cloudwatch](skills/aws-cloudwatch/) | DevOps | Puts custom metrics into AWS CloudWatch using a simple wrapper around putMetricData |
| [aws-cognito](skills/aws-cognito/) | Development | Work with aws-cognito — integrate, configure, and automate |
| [aws-dynamodb](skills/aws-dynamodb/) | Database | Production-grade AWS DynamoDB patterns with exponential backoff, VPC endpoints, IAM lea... |
| [aws-ec2](skills/aws-ec2/) | DevOps | Manages AWS EC2 instances with production-grade security and performance hardening |
| [aws-iam](skills/aws-iam/) | Development | Work with aws-iam — integrate, configure, and automate |
| [aws-lambda](skills/aws-lambda/) | Development | Work with aws-lambda — integrate, configure, and automate |
| [aws-s3](skills/aws-s3/) | DevOps | Production-depth AWS S3 skill covering request rate limits and prefix partitioning, mul... |
| [aws-sdk](skills/aws-sdk/) | Development | Work with aws-sdk — integrate, configure, and automate |
| [aws-sdk-rds](skills/aws-sdk-rds/) | Development | Work with aws-sdk-rds — integrate, configure, and automate |
| [aws-sns](skills/aws-sns/) | DevOps | Manages AWS Simple Notification Service for production-grade pub/sub messaging |
| [aws-sqs](skills/aws-sqs/) | Development | Work with aws-sqs — integrate, configure, and automate |
| [axios](skills/axios/) | Development | Work with axios — integrate, configure, and automate |
| [bcrypt](skills/bcrypt/) | Development | Work with bcrypt — integrate, configure, and automate |
| [bull](skills/bull/) | Development | Work with bull — integrate, configure, and automate |
| [celery](skills/celery/) | Development | Work with celery — integrate, configure, and automate |
| [cheerio](skills/cheerio/) | Development | Work with cheerio — integrate, configure, and automate |
| [chroma](skills/chroma/) | AI/ML | Chroma is the open-source AI-native vector database for building LLM-powered search and... |
| [clerk](skills/clerk/) | Development | Work with clerk — integrate, configure, and automate |
| [cloudflare-workers](skills/cloudflare-workers/) | DevOps | Build, deploy, and harden Cloudflare Workers for production |
| [consul](skills/consul/) | Development | Work with consul — integrate, configure, and automate |
| [cors](skills/cors/) | Development | Work with cors — integrate, configure, and automate |
| [cron](skills/cron/) | Development | Work with cron — integrate, configure, and automate |
| [csv-parse](skills/csv-parse/) | Development | Work with csv-parse — integrate, configure, and automate |
| [cypress](skills/cypress/) | Development | Work with cypress — integrate, configure, and automate |
| [datadog](skills/datadog/) | Development | Work with datadog — integrate, configure, and automate |
| [date-fns](skills/date-fns/) | Development | Work with date-fns — integrate, configure, and automate |
| [dayjs](skills/dayjs/) | Development | Work with dayjs — integrate, configure, and automate |
| [discord-bot](skills/discord-bot/) | Development | Work with discord-bot — integrate, configure, and automate |
| [docker](skills/docker/) | DevOps | Manages Docker containers, images, networks, and volumes using the Docker Engine API an... |
| [docker-compose](skills/docker-compose/) | Development | Work with docker-compose — integrate, configure, and automate |
| [dotenv](skills/dotenv/) | Development | Work with dotenv — integrate, configure, and automate |
| [drizzle-orm](skills/drizzle/) | Database | Drizzle ORM is a lightweight, type-safe TypeScript ORM for PostgreSQL, MySQL, and SQLit... |
| [elasticsearch](skills/elasticsearch/) | Database | Connects to Elasticsearch clusters and performs full-text search, document indexing, qu... |
| [eslint](skills/eslint/) | Development | Work with eslint — integrate, configure, and automate |
| [etcd](skills/etcd/) | Development | Work with etcd — integrate, configure, and automate |
| [exceljs](skills/exceljs/) | Development | Work with exceljs — integrate, configure, and automate |
| [express](skills/express/) | Development | Work with express — integrate, configure, and automate |
| [fastapi-production](skills/fastapi/) | Development | Production-depth skill for building robust FastAPI services |
| [fetch-api](skills/fetch-api/) | Development | Work with fetch-api — integrate, configure, and automate |
| [ffmpeg](skills/ffmpeg/) | Development | Work with ffmpeg — integrate, configure, and automate |
| [firebase](skills/firebase/) | Database | Integrates Firebase services (Authentication, Firestore, Realtime Database, Storage, Cl... |
| [github-actions](skills/github-actions/) | Development | Work with github-actions — integrate, configure, and automate |
| [github-cli](skills/github-cli/) | Development | Work with github-cli — integrate, configure, and automate |
| [gitlab-ci](skills/gitlab-ci/) | Development | Work with gitlab-ci — integrate, configure, and automate |
| [google-cloud-storage](skills/google-cloud-storage/) | Development | Work with google-cloud-storage — integrate, configure, and automate |
| [got](skills/got/) | Development | Work with got — integrate, configure, and automate |
| [grafana](skills/grafana/) | Development | Work with grafana — integrate, configure, and automate |
| [graphql](skills/graphql/) | Development | Work with graphql — integrate, configure, and automate |
| [grpc](skills/grpc/) | Development | Work with grpc — integrate, configure, and automate |
| [helm](skills/helm/) | Development | Work with helm — integrate, configure, and automate |
| [helmet](skills/helmet/) | Development | Work with helmet — integrate, configure, and automate |
| [hono](skills/hono/) | Development | Work with hono — integrate, configure, and automate |
| [husky](skills/husky/) | Development | Work with husky — integrate, configure, and automate |
| [ioredis](skills/ioredis/) | Development | Work with ioredis — integrate, configure, and automate |
| [jaeger](skills/jaeger/) | Development | Work with jaeger — integrate, configure, and automate |
| [jest](skills/jest/) | Development | Work with jest — integrate, configure, and automate |
| [jira](skills/jira/) | Development | Work with jira — integrate, configure, and automate |
| [jsonwebtoken](skills/jsonwebtoken/) | Development | Work with jsonwebtoken — integrate, configure, and automate |
| [jwt](skills/jwt/) | Development | Work with jwt — integrate, configure, and automate |
| [kafka](skills/kafka/) | Development | Work with kafka — integrate, configure, and automate |
| [keycloak](skills/keycloak/) | Development | Work with keycloak — integrate, configure, and automate |
| [knex](skills/knex/) | Development | Work with knex — integrate, configure, and automate |
| [kubernetes](skills/kubernetes/) | DevOps | Manages containerized application orchestration using Kubernetes (K8s) |
| [langchain](skills/langchain/) | Development | Work with langchain — integrate, configure, and automate |
| [linear](skills/linear/) | Development | Work with linear — integrate, configure, and automate |
| [llamaindex](skills/llamaindex/) | Development | Work with llamaindex — integrate, configure, and automate |
| [lodash](skills/lodash/) | Development | Work with lodash — integrate, configure, and automate |
| [loki](skills/loki/) | Development | Work with loki — integrate, configure, and automate |
| [lucia-auth](skills/lucia-auth/) | Development | Work with lucia-auth — integrate, configure, and automate |
| [mailgun](skills/mailgun/) | Development | Work with mailgun — integrate, configure, and automate |
| [meilisearch](skills/meilisearch/) | Development | Work with meilisearch — integrate, configure, and automate |
| [memcached](skills/memcached/) | Development | Work with memcached — integrate, configure, and automate |
| [minio](skills/minio/) | Development | Work with minio — integrate, configure, and automate |
| [mongodb](skills/mongodb/) | Database | Provides production-grade MongoDB patterns for Node |
| [mongoose](skills/mongoose/) | Development | Work with mongoose — integrate, configure, and automate |
| [morgan](skills/morgan/) | Development | Work with morgan — integrate, configure, and automate |
| [multer](skills/multer/) | Development | Work with multer — integrate, configure, and automate |
| [mysql](skills/mysql/) | Database | Production-grade MySQL integration for Node |
| [neon](skills/neon/) | Development | Work with neon — integrate, configure, and automate |
| [nestjs](skills/nestjs/) | Development | Work with nestjs — integrate, configure, and automate |
| [netlify](skills/netlify/) | Development | Work with netlify — integrate, configure, and automate |
| [nextauth](skills/nextauth/) | Development | Work with nextauth — integrate, configure, and automate |
| [nextjs](skills/nextjs/) | Development | Work with nextjs — integrate, configure, and automate |
| [nginx](skills/nginx/) | Development | Work with nginx — integrate, configure, and automate |
| [nginx-config](skills/nginx-config/) | Development | Work with nginx-config — integrate, configure, and automate |
| [nodemailer](skills/nodemailer/) | Development | Work with nodemailer — integrate, configure, and automate |
| [notion-api](skills/notion-api/) | Development | Work with notion-api — integrate, configure, and automate |
| [oauth2](skills/oauth2/) | Development | Work with oauth2 — integrate, configure, and automate |
| [okta](skills/okta/) | Development | Work with okta — integrate, configure, and automate |
| [openai](skills/openai/) | Development | Work with openai — integrate, configure, and automate |
| [opentelemetry](skills/opentelemetry/) | Development | Work with opentelemetry — integrate, configure, and automate |
| [passport](skills/passport/) | Development | Work with passport — integrate, configure, and automate |
| [paypal](skills/paypal/) | Development | Work with paypal — integrate, configure, and automate |
| [pdf-lib](skills/pdf-lib/) | Development | Work with pdf-lib — integrate, configure, and automate |
| [pg](skills/pg/) | Development | Work with pg — integrate, configure, and automate |
| [pinecone](skills/pinecone/) | Database | Production-grade vector database skill for Pinecone |
| [pino](skills/pino/) | Development | Work with pino — integrate, configure, and automate |
| [plaid](skills/plaid/) | Development | Work with plaid — integrate, configure, and automate |
| [planetscale](skills/planetscale/) | Development | Work with planetscale — integrate, configure, and automate |
| [playwright](skills/playwright/) | Development | Work with playwright — integrate, configure, and automate |
| [pm2](skills/pm2/) | Development | Work with pm2 — integrate, configure, and automate |
| [postgresql](skills/postgresql/) | Database | Production-depth PostgreSQL operations skill covering connection pooling with PgBouncer... |
| [prettier](skills/prettier/) | Development | Work with prettier — integrate, configure, and automate |
| [prisma-production-depth](skills/prisma/) | Database | Production-depth Prisma ORM patterns for Node |
| [prometheus](skills/prometheus/) | Development | Work with prometheus — integrate, configure, and automate |
| [puppeteer](skills/puppeteer/) | Development | Work with puppeteer — integrate, configure, and automate |
| [pusher](skills/pusher/) | Development | Work with pusher — integrate, configure, and automate |
| [pydantic](skills/pydantic/) | Development | Work with pydantic — integrate, configure, and automate |
| [pytest](skills/pytest/) | Development | Work with pytest — integrate, configure, and automate |
| [rabbitmq](skills/rabbitmq/) | Development | Work with rabbitmq — integrate, configure, and automate |
| [rate-limiter-flexible](skills/rate-limiter-flexible/) | Development | Work with rate-limiter-flexible — integrate, configure, and automate |
| [react](skills/react/) | Development | Work with react — integrate, configure, and automate |
| [react-query](skills/react-query/) | Development | Work with react-query — integrate, configure, and automate |
| [redis](skills/redis/) | Database | Production-grade Redis client patterns for Node |
| [redis-streams](skills/redis-streams/) | Development | Work with redis-streams — integrate, configure, and automate |
| [redux](skills/redux/) | Development | Work with redux — integrate, configure, and automate |
| [resend](skills/resend/) | Development | Work with resend — integrate, configure, and automate |
| [rest-api](skills/rest-api/) | Development | Work with rest-api — integrate, configure, and automate |
| [sendgrid](skills/sendgrid/) | Development | Sends transactional and bulk email via the Twilio SendGrid Web API v3 |
| [sentry](skills/sentry/) | Development | Work with sentry — integrate, configure, and automate |
| [sequelize](skills/sequelize/) | Development | Work with sequelize — integrate, configure, and automate |
| [sharp](skills/sharp/) | Development | Work with sharp — integrate, configure, and automate |
| [sharp-image](skills/sharp-image/) | Development | Work with sharp-image — integrate, configure, and automate |
| [shopify](skills/shopify/) | Development | Work with shopify — integrate, configure, and automate |
| [slack-api](skills/slack-api/) | Development | Work with slack-api — integrate, configure, and automate |
| [socket-io](skills/socket-io/) | Development | Work with socket-io — integrate, configure, and automate |
| [sqlalchemy](skills/sqlalchemy/) | Development | Work with sqlalchemy — integrate, configure, and automate |
| [sqlite](skills/sqlite/) | Database | Production-depth SQLite operations for Node |
| [stripe](skills/stripe/) | Development | Integrates Stripe payment processing into applications using the official Stripe SDK (P... |
| [supabase-production](skills/supabase/) | Database | Production-depth Supabase patterns covering connection pooling with PgBouncer, RLS poli... |
| [supertest](skills/supertest/) | Development | Work with supertest — integrate, configure, and automate |
| [telegram-bot](skills/telegram-bot/) | Development | Work with telegram-bot — integrate, configure, and automate |
| [terraform](skills/terraform/) | Development | Work with terraform — integrate, configure, and automate |
| [turso](skills/turso/) | Development | Work with turso — integrate, configure, and automate |
| [twilio-production](skills/twilio/) | Development | Production-grade Twilio integration covering webhook signature validation, retry logic ... |
| [twilio-sms](skills/twilio-sms/) | Development | Work with twilio-sms — integrate, configure, and automate |
| [twilio-voice](skills/twilio-voice/) | Development | Work with twilio-voice — integrate, configure, and automate |
| [typeorm](skills/typeorm/) | Development | Work with typeorm — integrate, configure, and automate |
| [typescript](skills/typescript/) | Development | Work with typescript — integrate, configure, and automate |
| [upstash](skills/upstash/) | Development | Work with upstash — integrate, configure, and automate |
| [uuid](skills/uuid/) | Development | Work with uuid — integrate, configure, and automate |
| [varnish](skills/varnish/) | Development | Work with varnish — integrate, configure, and automate |
| [vault](skills/vault/) | Development | Work with vault — integrate, configure, and automate |
| [vercel](skills/vercel/) | Development | Work with vercel — integrate, configure, and automate |
| [vite](skills/vite/) | Development | Work with vite — integrate, configure, and automate |
| [vitest](skills/vitest/) | Development | Work with vitest — integrate, configure, and automate |
| [vue](skills/vue/) | Development | Work with vue — integrate, configure, and automate |
| [weaviate](skills/weaviate/) | Database | Production-grade vector database operations with Weaviate |
| [webpack](skills/webpack/) | Development | Work with webpack — integrate, configure, and automate |
| [websocket](skills/websocket/) | Development | Work with websocket — integrate, configure, and automate |
| [websockets](skills/websockets/) | Development | Work with websockets — integrate, configure, and automate |
| [winston](skills/winston/) | Development | Work with winston — integrate, configure, and automate |
| [woocommerce](skills/woocommerce/) | Development | Work with woocommerce — integrate, configure, and automate |
| [yup](skills/yup/) | Development | Work with yup — integrate, configure, and automate |
| [zod](skills/zod/) | Development | Work with zod — integrate, configure, and automate |
| [zustand](skills/zustand/) | Development | Work with zustand — integrate, configure, and automate |

## Use Cases

Step-by-step guides: see [use-cases/](use-cases/)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

Apache-2.0. See [LICENSE](LICENSE).
