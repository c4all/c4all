# C4all

Comments for all is an easy to use comment field. Read more about it on the [website](http://c4all.github.io).

### Development setup

    # prepare the virtual environment (requires virtualenvwrapper: http://virtualenvwrapper.readthedocs.org/en/latest/)
    mkvirtualenv --no-site-packages c4all

    # get c4all service
    git clone git@github.com:dobarkod/c4all.git c4all
    cd c4all

    # set up the development environment
    make dev-setup

    # run c4all service
    python manage.py runserver_plus


### The production setup

The production environment can't be set up automatically (at it may require
setting up databaes details and other per-server settings manually), but there
are some helper Makefile tasks to speed it up.

To set up the production environment for c4all service, loosely
follow this procedure:

    # prepare the virtual environment (requires virtualenvwrapper: http://virtualenvwrapper.readthedocs.org/en/latest/)
    mkvirtualenv --no-site-packages c4all

    # get c4all service
    git clone git@github.com:dobarkod/c4all.git c4all
    cd c4all

    # install the requirements
    make reqs/prod

    # create a project/settings/local.py settings file with per-server config
    # and import prod settings (write "from .prod import *" in local file
    # after you create it)
    vim c4all/settings/local.py

    # setup your own DB. to connect c4all service and your DB, refer to settings
    # part of this document and django docs (specifically https://docs.djangoproject.com/en/1.5/ref/databases/)

    # install Node.js and less compiler
    * OS-specific Node.js installation: https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager/)
    npm install -g less

    # for spell checking abilities, you will need to install enchart
    # (http://www.abisource.com/projects/enchant/) library. for specific
    # language, take a look at supported languages at aspell site
    # (http://aspell.net/man-html/Supported.html) and install it. language
    # set in base settings (LANGUAGE_CODE variable) is the same language spell
    # checker is using for its operation. after installing enchant, install
    # pyenchant by running:
    pip install pyenchant==1.6.5

    # and add change setting SPELLCHECK_ENABLED in base.py:
    SPELLCHECK_ENABLED = True

    # run automatic update (db sync/migrations, collectstatic)
    make prod-update

    # create superuser (provide credentials: email and password)
    python manage.py createsuperuser

    # your production environment is now ready
    python manage.py run_gunicorn

    # set the BASE_URL in base.py to "http://www.your-server-address.com".

    # default language is swedish, if you want to change it to english set
    # LANGUAGE_CODE variable in base.py to 'en_EN'.

    # head to the superadmin page at www.your-server-address.com/djadmin/,
    # login with your superuser credentials and add Site object in Sites by
    # providing URL of the site which will host c4all comments service.

    # include html snippets on your page:
    <script src="{{ BASE_URL }}/static/js/comments.js" type="text/javascript"></script>
    <div id="c4all-widget-container"></div>

    # article name handling is done via html tag reading. if admins add ID with
    # value "c4all-admin-page-title" to some html element, script will read its
    # text value. if ID not provided, script will first try to read page title,
    # followed by first h1 tag. if everything fails, url path/location will be
    # passed to server side.

    # start commenting!


Text-to-speech is possible via commercial Readspeaker service (http://www.readspeaker.com/).
After setting up Readspeaker account, enter your ReadSpeaker Customer ID into
rs_customer_id field of Site object in superadmin interface. Ensure that domain
where comments are displayed is the same as in ReadSpeaker admin interface.


The development environment by default includes:

* South for database migrations (both development and production use it)
* Django Debug Toolbar for displaying extra information about view execution
* SQLite database (dev.db in the project root directory)
* Integrated view debugger making it easy to debug crashes directly from the browser (Werkzeug and django-extension's runserver_plus)
* Full SQL statement logging
* Beefed-up Django shell with model auto-loading and IPython REPL
* Flake8 source code checker (style, passive code analysis)
* Console E-mail backend set by default in dev for simple E-mail send testing
* Automated testing all set-up with nose, optionally creating test coverage reports, and using the in-memory SQLite database (and disabled South) to speed up test execution
* Disabled cache for easier debugging


The production environment by default includes:

* [Gunicorn](http://gunicorn.org/) integration
* [Django Compressor](http://django_compressor.readthedocs.org/en/master/)
  for CSS/JS asset minification and compilation
* Database auto-discovery via environment settings, compatible with Heroku
* [Sentry](http://sentry.readthedocs.org/en/latest/) client (raven\_compat)
  for exception logging (used only if `SENTRY_DSN` variable is set in
  settings or environment)
* Local-memory cache (although memcached is strongly recommended if available)


### The settings files

The settings files `base` (base settings used in all environments),
`prod` (production settings), `dev` (local development settings) and
`test` (settings used when running automated tests) should contain only the
settings used by all developers/servers.

Per-server (or per-developer) settings should go into `local` module
(ie. `project/settings/local.py`). The usual pattern for this module is to
first import everything from the settings variant that best matches your
environment (`prod` for servers, `dev` for local development), and then
override/add settings as needed.

Example production settings just specifying the production database:

    # file: project/settings/local.py
    from .prod import *

    DATABASES = {
        'default': { ... }
    }

You shouldn't need to add `local.py` to the repository (in fact, git is
already set up to ignore it). If some setting needs to be shared by everyone,
it should probably be added to `base`, `dev` or `prod`.

The local settings file isn't required. If it doesn't exist, the production
setup will be used by default. This is useful if you don't have per-server
settings or they're deployed via Unix environment (as they are on eg. Heroku
and similar cloud hosting providers). There is a sample local.py located in
settings directory which hosts some of the commonly used variables.

### Environment settings

Settings can also be set via the environment variables. The following
variables are supported:

* `DATABASE_URL` - Heroku-compatible database URL
* `DEBUG` - String `true` enables DEBUG, any other disables
* `TEMPLATE_DEBUG` - String `true` enables TEMPLATE_DEBUG, any other disables
* `COMPRESS_ENABLED` - String `true` enables django-compressor, any other
  disables
* `SQL_DEBUG` - String `true` enables SQL statement logging, any other
   disables (disabled by default, available only if using `dev.py`)
* `CACHE_BACKEND` - String value to put into `CACHES['default']['BACKEND']`
* `EMAIL_BACKEND` - String value for EMAIL_BACKEND (only if using `dev.py`)

Note that values from `local.py` override environment settings! You probably
want to use either the local settings file or the environment settings, not
mix them.

### The extended tour

After setting up your new c4all project, try these:

    # make sure all tests pass (you'll need to write them first, though :)
    make test

    # get a test coverage report (outputs to stdout, saves HTML format in
    # cover/index.html and produces Cobertura report compatible with Jenkins)
    make coverage

    # clean up test artifacts, *.pyc files and cached compressed assets
    make clean

    # check if the code follows PEP8 and is free of obvious errors
    # this also includes cyclomatic complexity check and will complain if your
    # code is too complex (configurable by editing the Makefile)
    make lint

    # update the environment (eg. after pulling in new code)
    make dev-update

    # open up the new and improved Django shell
    python manage.py shell_plus


### Heroku support

To specify Python module dependencies on Heroku, add a pip requirements
file named requirements.txt to the root of your repository. Since c4all project
has python dependencies distributed in more files, you'll have to call
production requirements file from main requirements file you just created:

    git checkout -b heroku
    echo "-r requirements/prod.txt" > requirements.txt
    git add requirements.txt
    git commit -m 'requirements for heroku'


The production setup uses database autodiscovery so if you have a (promoted)
database in Heroku, it will automatically get picked up.

For Heroku, you'll probably want to add the `Procfile` file with contents
similar to this:

    web: python manage.py run_gunicorn --workers=4 --bind=0.0.0.0:$PORT

If your web app supports uploading of media (eg. images, videos or other
files) by users, you'll probably need the `django-storages` app to
automatically host them somewhere else (eg on Amazon S3). When
`django-storages` is set up, the collecstatic management command (run as
part of `make prod-update`) will copy the static assets to the specified
service as well.

After pushing the new code to Heroku for update, you should make sure to run
all the needed management commands to migrate the database, etc:

    heroku run make prod-update


### Sentry / Raven

To use the Sentry client, you'll need a server to point it to. Installing
Sentry server is easy as:

    # mkvirtualenv --no-site-packages sentry-env
    # pip install sentry
    # sentry init
    # sentry start

You'll want to install Sentry into its own environment as it requires
Django 1.2 or 1.3 at the moment.

If you don't want to install Sentry yourself, you can use a hosted
version at http://getsentry.com/.

When you connect to your (or hosted) Sentry server and create a new project
there, you'll be given Sentry DSN which you need to put into production
settings to activate Sentry exception logging.


#### Deployments via git

If deployments are done via git (and not fabric, see below), it's
recommended to create another Makefile target that will do the deploy, for
example:

    deploy:
      git pull
      $(MAKE) update
      # command to restart the service(s) as neccessary

### Fabric

A fabfile is provided with common tasks for rsyncing local directory to
the server for use while developing the project, and for deploying the
project using git clone/pull.

Useful commands:

  * server - host to connect to (same as -H, but accepts only one argument)
  * env - virtualenv name on the server, as used with virtualenvwrapper/workon
  * project_path - full path to the project directory on the server
  * rsync - use rsync to copy the local folder to the project directory on the server
  * setup - set up the project instance on the server (clones the origin
    repository, creates a virtual environment, initialises the database and
    runs the tests)
  * deploy - deploy a new version of project on the server using git pull
  * collecstatic, syncdb, migrate, runserver - run manage.py command
  * update - combines collecstatic, syncdb, migrate
  * test - run manage.py test with the test settings enabled

For all the commands, run 'fab -l' or look at the source.

#### Examples:

Copy local directory to the server, update database and static files, and
run tests (only files changed from last copy are going to be copied):

    fab server:my.server.com env:myenv project_path:/path/to/project rsync update test

Deploy a new instance of a project on a server ('myenv' will be newly created,
code will be cloned into /path/to/project):

    fab server:my.server.com env:myenv project_path:/path/to/project \
        setup:origin=http://github.com/senko/dj-skeletor

Deploy a new version of the project on the server (a new git tag will be
created for each deployment, so it's easy to roll-back if needed):

    fab server:my.server.com env:myenv project_path:/path/to/project deploy

##### Customization

Everyone has a slightly different workflow, so you'll probably want to
customize the default fabric tasks or combine them. You can either customize
fabfile.py and commit the changes to your repository, or you can create
local_fabfile.py, which will be loaded if it exists. The latter can be useful
if you have per-team-member fabric customizations you don't want to commit
to the repository.
