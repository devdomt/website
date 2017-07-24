from flask import Flask, render_template

app = Flask("Personal_page")


@app.route("/")
def render_main_page():
    return render_template("main.html")


def main():
    app.run()


if __name__ == '__main__':
    main();
