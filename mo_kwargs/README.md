
Mo' KWARGS!
---------------

###Decorator `override`###

`@override` will decorate a function to accept a `settings` parameter which is just like `**kwargs`, but the named parameters will override the properties in `settings`, rather than raise duplicate key name exceptions.

**Example**

We decorate the `login()` function with `@override`. In this case, `username` is a required parameter, and `password` will default to `None`. The settings parameter should always default to `None` so that it's not required.

```python
		@override
		def login(username, password=None, settings=None):
			pass
```

Define some `dicts` for use with our `settings` parameter:

		creds = {"userame": "ekyle", "password": "password123"}
		alt_creds = {"username": "klahnakoski"}


The simplest case is when we use settings with no overrides

		login(settings=creds)
		# SAME AS
		login(**creds)
		# SAME AS
		login(username="ekyle", password="password123")

You may override any property in settings, in this case it is `password`

		login(password="123", settings=creds)
		# SAME AS
		login(username="ekyle", password="123")

There is no problem with overriding everything in `settings`:

		login(username="klahnakoski", password="asd213", settings=creds)
		# SAME AS
		login(username="klahnakoski", password="asd213")

You may continue to use `**kwargs`; which provides a way to overlay one parameter template (`creds`) with another (`alt_creds`)

		login(settings=creds, **alt_creds)
		# SAME AS
		login(username="klahnakoski", password="password123")


**Motivation** - Extensive use of dependency injection, plus managing the configuration
for each of the components being injected, can result in some spectacularly
complex system configuration. One way to reduce the complexity is to use
configuration templates that contain useful defaults, and simply overwrite
the properties that need to be changed for the new configuration.
`@override` has been created to provide this templating system for Python
function calls (primarily class constructors).
