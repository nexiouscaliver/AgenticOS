FROM nginx:alpine

# curl is needed by entrypoint.sh to fetch and patch JS bundles at startup.
# wget (already in alpine) doesn't handle --compressed reliably.
RUN apk add --no-cache curl

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy configs
COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80

# entrypoint.sh fetches & patches JS bundles, then execs nginx
CMD ["/entrypoint.sh"]
