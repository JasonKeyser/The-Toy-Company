#!/bin/sh
set -e
mkdir -p "$DJANGO_DATA_DIR/media/profile_pics"
[ -f "$DJANGO_DATA_DIR/media/default.jpg" ] || cp /app/deploy/default.jpg "$DJANGO_DATA_DIR/media/default.jpg"
python manage.py migrate --noinput
if [ -f game/fixtures/game_config.json ] && python manage.py shell -c "import sys; from game.models import Difficulty; sys.exit(1 if Difficulty.objects.exists() else 0)"; then
  echo "Empty database: loading game_config fixture"
  python manage.py loaddata game_config
fi
exec gunicorn myprojectname.wsgi:application --bind 0.0.0.0:8000 --workers 2 --access-logfile -