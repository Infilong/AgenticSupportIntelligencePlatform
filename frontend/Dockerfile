FROM node:22-slim
WORKDIR /app
RUN chown node:node /app
USER node
COPY --chown=node:node frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY --chown=node:node frontend/ ./
EXPOSE 5180
CMD ["npm", "run", "dev"]
