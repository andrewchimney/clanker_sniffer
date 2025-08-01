FROM node:20

# Set working directory
WORKDIR /app

# Install OS dependencies (Docker socket mount already lets you call docker)


# Copy only package metadata and install deps (better cache layer)
COPY package*.json ./

# Install all dependencies at once — includes pg, swr, axios, form-data, etc.
RUN npm install


# Now copy your source code
COPY . .

# Expose frontend port
EXPOSE 3000

# Run dev server
CMD ["npm", "run", "dev"]
