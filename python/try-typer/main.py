import typer

app = typer.Typer()

@app.command()
def welcome(name: str):
    print(f"Hello {name}")

@app.command()
def foo(what: str):
    print(f"foo{what}")

if __name__ == "__main__":
    app()
