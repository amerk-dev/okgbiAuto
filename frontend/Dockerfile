FROM node:16-alpine

WORKDIR /app
ENV REACT_APP_API_URL http://api:8000

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]