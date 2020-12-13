# Site availability checker

In general site availability checker service workflow can be described with next diagram:

    scheduler worker -> redis queue -> availability check worker -> kafka -> transfer worker -> postgres 

Sites for check stored in postgres db.
Checker super simple and provide only regexp pattern setting.
All code runs as jobs or cron jobs with [arq](https://arq-docs.helpmanual.io/).

## Start Service Locally

    docker-compose up -d
    
    # add new site
    docker-compose exec postgres psql -U test -d site_checker -c \
        "INSERT INTO sites (url, regexp) VALUES ('https://python.org', 'python')"
    
    # list check results in database (can be delayed to a few mins)
    docker-compose exec postgres psql -U test -d site_checker -c \
        "SELECT * FROM events"

## Run Tests

    pip install -r requirements.txt -r requirements-dev.txt  # install dependencies
    docker-compose up -d  # run all requred services
    black --check .  # run style check
    pytest tests  # run tests
    docker-compose down

## Code Style

There are used [black](https://black.readthedocs.io/en/stable/index.html) formatter for code:

    black .