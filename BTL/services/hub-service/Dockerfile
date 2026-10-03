FROM composer:2 AS composer
FROM php:8.2-cli-alpine
RUN apk add --no-cache libxml2-dev oniguruma-dev $PHPIZE_DEPS && docker-php-ext-install pdo_mysql mbstring dom xml xmlwriter
COPY --from=composer /usr/bin/composer /usr/bin/composer
WORKDIR /var/www
COPY . .
RUN composer install --no-dev --no-interaction --prefer-dist --optimize-autoloader
EXPOSE 8004
CMD ["php", "artisan", "serve", "--host=0.0.0.0", "--port=8004"]
