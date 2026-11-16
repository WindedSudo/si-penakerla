import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Debug mode (Werkzeug debugger) hanya aktif saat APP_ENV=development.
    debug = os.environ.get('APP_ENV', 'development') == 'development'
    host = os.environ.get('APP_HOST', '127.0.0.1')
    app.run(debug=debug, host=host, port=int(os.environ.get('APP_PORT', 5000)))
