import sys

# prevents unnecassary pycache files from being created
sys.dont_write_bytecode = True

from flask import Flask
from flask_login import LoginManager
from flask_wtf import CSRFProtect

app = Flask(__name__)
app.config["SECRET_KEY"] = "a-very-secret-secret-key"
CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

sys.modules.setdefault("app", sys.modules[__name__])

# Import routes after the application is initialized.
import routes


if __name__ == "__main__":
    app.run(debug=True)
