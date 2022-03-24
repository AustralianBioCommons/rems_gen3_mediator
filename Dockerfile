FROM python:3.7-slim

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED 1
ENV LC_ALL en_US.UTF-8
ENV LANG=en_US.UTF-8

# GEN3 CONFIG
ENV GEN3_SERVER_URL=""
ENV GEN3_AUTH_CONFIG=""
ENV GEN3_USER_CONFIG_FILE=""

# REMS CONFIG
ENV REMS_SERVER_URL=""
ENV REMS_USER_ID=""
ENV REMS_API_KEY=""
ENV REMS_ORGANIZATION_ID=""
ENV REMS_LICENSE_ID=""


RUN useradd -ms /bin/bash rems_mediator \
    && mkdir -p /app \
    && chown rems_mediator:rems_mediator /app -R \
    && echo "Acquire::http {No-Cache=True;};" > /etc/apt/apt.conf.d/no-cache \
    && apt-get -qq update && apt-get install -y --no-install-recommends \
        python3-pip \
        python3-setuptools \
        locales \
    && echo "$LANG UTF-8" > /etc/locale.gen \
    && locale-gen $LANG && update-locale LANG=$LANG \
    && apt-get autoremove -y && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/*

# Add the source files last to minimize layer cache invalidation
ADD --chown=rems_mediator:rems_mediator requirements.txt /app/
ADD --chown=rems_mediator:rems_mediator rems_gen3_mediator /app/rems_gen3_mediator

WORKDIR /app

RUN pip3 install --no-cache-dir -r requirements.txt

# Switch to new, lower-privilege user
USER rems_mediator

WORKDIR /app/rems_gen3_mediator

RUN python3 manage.py collectstatic --no-input

# gunicorn will listen on this port
EXPOSE 8000

CMD gunicorn -b :8000 --access-logfile - --error-logfile - --log-level info rems_gen3_mediator.wsgi
