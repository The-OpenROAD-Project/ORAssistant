# Install dependencies only when needed
FROM node:26-alpine AS deps
WORKDIR /app
COPY package.json yarn.lock .yarnrc.yml ./
# node:26 images ship neither yarn nor corepack. Corepack runs the Yarn
# release pinned in package.json "packageManager" and checks its hash.
ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0
RUN npm install -g corepack@0.36.0 && corepack enable && yarn install --immutable

# Rebuild the source code only when needed
FROM node:26-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Production image, copy all the files and run next
FROM node:26-alpine AS runner
WORKDIR /app

ENV NODE_ENV production

# Copy built assets from builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000

CMD ["npm", "start"]
