from starlette.responses import HTMLResponse

from app.system.constants import WHERE_AM_I

async def http_exception(request, exc):
    try:
        if exc.status_code == 500:
            message = "Lovely Day!"
        elif exc.status_code == 403:
            message = str(exc.detail)
        else:
            message = "Lovely Day!"
        if WHERE_AM_I not in ("development", "docker_dev") and exc.status_code == 500:
            message = "Please Contact the Administrator!"
    except AttributeError:
        message = str(exc)
    # Using python's "format", causes conflict with the CSS syntax.
    return HTMLResponse(
        content="""<html> <head>
                <style>
                    * {
                        margin: 0;
                        padding: 0;
                    }
                    .imgbox {
                        display: grid;
                        height: 100%;
                    }
                    .center-fit {
                        max-width: 100%;
                        max-height: 100vh;
                        margin: auto;
                    }
                </style>
            </head>
            <body>
            <h1>This is what happened: {message} </h1>
            <h4>~ “All work and no play makes devs dull boys.”</h4>
            <div class="imgbox">
                <img class="center-fit" src='https://i.redd.it/s550dkwyk8621.jpg'>
            </div>
            </body>
            </html>""".replace(
            "message", message
        ),
        status_code=200,
        media_type="text/html",
    )


EXCEPTION_HANDLERS = {403: http_exception, 500: http_exception}
