# Multi-arch (arm64/amd64) base with Ruby 3.2
FROM fluent/fluentd:v1.16-debian

USER root
# build tools for native gems, then install the OCI Logging plugin
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends build-essential ruby-dev pkg-config ca-certificates; \
    gem install --no-document fluent-plugin-oci-logging; \
    apt-get purge -y --auto-remove build-essential ruby-dev pkg-config; \
    rm -rf /var/lib/apt/lists/*

# Ruby 3.2 removed File.exists?; add a compat shim for the plugin
COPY patch_exists.rb /fluentd/patch_exists.rb
ENV RUBYOPT="-r/fluentd/patch_exists.rb"

USER fluent
