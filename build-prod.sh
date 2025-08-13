set -e
set -o pipefail
rm -rf ./tmp && mkdir -m 777 ./tmp
TMPDIR=$(pwd)/tmp docker compose -f docker-compose.prod.yml build --no-cache