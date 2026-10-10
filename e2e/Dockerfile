FROM mcr.microsoft.com/playwright:v1.50.0-noble

WORKDIR /e2e

COPY package*.json ./
RUN npm install

COPY . .

ENV CI=true

CMD ["npx", "playwright", "test"]
