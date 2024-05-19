
![Propolis Logo](https://images.hive.blog/p/3RTd4iuWD6NUeJEn5AVrJUoyatFqBqfcCJi1N7UixR4g2KPKN7w8NpZKoVmzrtkeTFLFfA7gA6f4H1tT3FaWF1a3As8SH1uEBm5Hov8ZqnjJ61ejqWxYexArdsAzpfzNsgeXcvLKiWchQBPSxVALG6bWto32AboiJte4LKEXb8BBD8?width=1600&height=1200&format=webp&mode=fit)


# Propolis Wiki

A web3 wiki using the hive blockchain for storing articles. 


## Setup

Clone the project

```bash
  git clone https://github.com/pharesim/propolis-wiki
```

Go to the project directory

```bash
  cd propolis-wiki
```

edit config file

```bash
  cp instance/config_default.py instance/config.py
  nano instance/config.py
```

### Database

Propolis requires a complementary PostgreSQL database to store some metadata. The structure can be derived from the updater.py script until there is a setup script/dump available.

### Run Locally

Start the local flask dev server

```bash
  ./wiki.sh
```

### Deployment

Install latest dist version including dependencies

```bash
  pip install dist/wiki*.whl
```

To deploy this project, you should use a webserver configured to your needs.

Example apache config:

```
DocumentRoot /var/www

WSGIDaemonProcess wiki user=wiki group=wiki threads=8
WSGIScriptAlias / /home/wiki/propolis-wiki/wsgi.py

<Directory /home/wiki/propolis-wiki>
    WSGIProcessGroup wiki
    WSGIApplicationGroup %{GLOBAL}
    Require all granted
</Directory>

```

### Build

Create a new dist file

```bash
  ./build.sh
```

Don't forget to bump version in pyproject.toml and wiki/static/js/main.js

## Contributing

Contributions are always welcome!

See `contributing.md` for ways to get started.

Please adhere to this project's `code of conduct`.


## License

[MIT](https://choosealicense.com/licenses/mit/)

