<!---
[![Tests](https://github.com/AustralianBioCommons/django_rems_gen3_mediator/actions/workflows/tests.yaml/badge.svg)](https://github.com/AustralianBioCommons/django_rems_gen3_mediator/actions/workflows/tests.yaml)
[![Coverage Status](https://coveralls.io/repos/github/AustralianBioCommons/django_rems_gen3_mediator/badge.svg?branch=main)](https://coveralls.io/github/AustralianBioCommons/django_rems_gen3_mediator?branch=main)
-->

## Django-Rems-Gen3-Mediator <img src="https://rems-demo.rahtiapp.fi/img/rems_logo_en.png" style="max-height=100">

This django app provides mediation between Gen3 and REMS. It has management commands to register Gen3 resources
with the REMS system. These management commands can be run through a cron job to periodically sync all Gen3 resources
with REMS. REMS can subsequently be used to manage entitlements to particular resources. The web component of this
django app listens for REMS entitlement requests, and makes corresponding changes to keep Gen3 permissions in sync. 

### Deployment

#### Ansible

```bash
cd deploy/ansible
ansible-playbook -i inventory.ini playbook.yml
```

#### Compose

```bash
cd deploy/compose
docker-compose up -d db
docker-compose --rm -e CMD="migrate" app
docker-compose up -d app mediator
docker-compose run --rm -e CMD="api-key add testapikey testkeydescription" app
docker-compose run --rm -e CMD="set-users admin" app
docker-compose run --rm -e CMD="grant-role owner admin" app
```

### Development

```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
cd rems_gen3_mediator
GEN3_AUTH_CONFIG=`cat ~/gen3-credentials-3.json` REMS_API_KEY=testapikey REMS_USER_ID=admin REMS_ORGANIZATION_ID=UniMelb python3 manage.py import_gen3_projects
GEN3_AUTH_CONFIG=`cat ~/gen3-credentials-3.json` REMS_API_KEY=testapikey REMS_USER_ID=admin REMS_ORGANIZATION_ID=UniMelb python3 manage.py runserver
```
