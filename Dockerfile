# syntax=docker/dockerfile:1.4

FROM node:20-bullseye-slim AS base
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked --mount=type=cache,target=/var/lib/apt,sharing=locked \
   apt-get update && \
   apt-get dist-upgrade -y && \
   apt-get install -y --no-install-recommends python3

FROM base AS builder
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked --mount=type=cache,target=/var/lib/apt,sharing=locked \
   apt-get update && \
   apt-get install -y --no-install-recommends g++ make
WORKDIR /app
COPY --link app/package.json app/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
   npm ci
COPY --link app/src ./src
COPY --link app/lib ./lib
COPY --link app/builder.mjs ./
COPY --link app/util/tsconfig/tsconfig.bundle.json ./util/tsconfig/
RUN node builder.mjs bake && \
   npx tsc -p util/tsconfig/tsconfig.bundle.json && \
   node builder.mjs bundle && \
   mv ./dist/index.min.js ./dist/index.js && \
   mv ./dist/worker.min.js ./dist/worker.js

FROM base AS deps
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked --mount=type=cache,target=/var/lib/apt,sharing=locked \
   apt-get update && \
   apt-get install -y --no-install-recommends build-essential
WORKDIR /app
COPY --link app/package.json app/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
   npm ci --omit=dev

FROM base AS runner
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked --mount=type=cache,target=/var/lib/apt,sharing=locked \
   apt-get update && \
   apt-get install -y --no-install-recommends nscd ca-certificates && \
   ln -s /usr/bin/python3 /usr/bin/python
WORKDIR /app
RUN mkdir logs && \
   echo DOCKER_BUILD_IMAGE>DOCKER_BUILD_IMAGE

COPY --link app/lib ./lib
COPY --link app/locales ./locales
COPY --link app/config.json ./config.json
COPY --link app/package.json app/package-lock.json ./
COPY --link --from=deps /app/node_modules /app/node_modules
COPY --link --from=builder /app/dist /app/dist

CMD ["/bin/bash", "-c", "service nscd start; exec node --dns-result-order=ipv4first dist/index.js"]
