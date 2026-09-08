# Stage 1: Install dependencies
FROM node:20-slim AS deps

WORKDIR /app

RUN npm install -g pnpm

COPY package.json package-lock.json* ./
RUN npm install

# Stage 2: Build production bundle
FROM deps AS builder

COPY . .
RUN npm run build

# Stage 3: Production — serve with lightweight static server
FROM node:20-slim AS production

WORKDIR /app

RUN npm install -g serve

COPY --from=builder /app/dist ./dist

EXPOSE 5173

CMD ["serve", "-s", "dist", "-l", "5173"]

# Stage 4: Development — use for docker-compose dev mode
FROM deps AS development

WORKDIR /app

COPY . .

EXPOSE 5173

CMD ["npx", "vite", "--host"]
