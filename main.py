from src.web.app import Application


if __name__ == '__main__':
    app = Application(port=80)
    app.run(debug=True)
