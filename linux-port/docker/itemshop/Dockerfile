# =============================================================================
#  ItemShop -- standalone PHP web shop, buys write into player.item_award so
#  the stock delivery pipeline (ItemAwardManager.cpp) hands items to the
#  player next login. Independent login form against account.account, not the
#  retail sas/pid auto-login scheme -- real game credentials work.
# =============================================================================
FROM php:8.2-apache

RUN docker-php-ext-install mysqli \
 && apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

COPY app/ /var/www/html/

# ACMD(do_in_game_mall) hardcodes "http://host/ishop?pid=...&sas=..." (no
# trailing slash). mod_dir's default DirectorySlash would 302 that to
# "/ishop/?pid=...&sas=..." before it ever reaches index.php - fine in a
# normal browser, but doubles the round trips through the old in-game
# embedded browser and made the shop intermittently fail to open
# ("Nie mozna odnalezc strony") instead of just being a bit slower. Serving
# /ishop directly avoids the extra hop entirely.
RUN a2enmod rewrite \
 && sed -i '/<VirtualHost \*:80>/a\    RewriteEngine On\n    RewriteRule ^/ishop$ /ishop/index.php [L]' \
    /etc/apache2/sites-enabled/000-default.conf

EXPOSE 80/tcp

HEALTHCHECK --interval=20s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS -o /dev/null "http://127.0.0.1/itemshop/" || exit 1
