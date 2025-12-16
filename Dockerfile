FROM python:3.13-slim

ENV VIRTUAL_ENV=/venv

RUN useradd heroku_restarter --create-home && mkdir /app $VIRTUAL_ENV && chown -R heroku_restarter /app $VIRTUAL_ENV

WORKDIR /app

# Install poetry at the system level
RUN pip install --no-cache poetry==2.1.1

USER heroku_restarter

RUN python -m venv $VIRTUAL_ENV

ENV PATH=$VIRTUAL_ENV/bin:$PATH

COPY --chown=heroku_restarter pyproject.toml poetry.lock ./

RUN pip install --no-cache --upgrade pip && poetry install --no-root --compile && rm -rf $HOME/.cache

COPY --chown=heroku_restarter . .

CMD ["/venv/bin/gunicorn"]
