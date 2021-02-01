# quick_and_dirty
This is a "quick_and_dirty" solution to produce prototype webapps, based on python's Starlette toolkit & 
focused as much as possible at the template & SQL Queries (I really don't like ORMs - no disrespect, It's just a matter of taste, with a salt of objective arguments).

By using internal API's, I try to leverage the capabilities of Jinja2 by providing Query, Forms & Path data, along with requested (predefined) DB Queries & optionally data straight from python functions (like flask.Blueprint/starlette.Route do with jinja2 & "**locals") to the template's disposal. 

A significant part of the business logic will take place at the template & the DB Queries, but hey, it's a solution for fast prototyping!
