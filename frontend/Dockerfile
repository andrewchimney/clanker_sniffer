# frontend/Dockerfile
FROM node:20

WORKDIR /app

COPY package*.json ./
RUN npm install pg
RUN npm install swr
RUN apt-get update && apt-get install -y ffmpeg

RUN npm install
#COPY .env .env

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
# For production, use: CMD ["npm", "run", "build"] then ["npm", "start"]
