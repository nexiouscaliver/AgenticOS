docker run -d \
  -e POSTGRES_DB=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  --restart unless-stopped \
  --name agentos-postgres \
  agnohq/pgvector:16